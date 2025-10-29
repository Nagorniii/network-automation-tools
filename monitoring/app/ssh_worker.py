import paramiko, socket
import os, json, re
import time
import subprocess
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


logging.getLogger("paramiko").setLevel(logging.WARNING)
load_dotenv()

username = os.getenv("user")
password = os.getenv("pass")
commands = ["sh ip int b", "sh run | i hostname"]

def ping_ip(ip):
    timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    reply = subprocess.run(['ping', '-c', '2', '-W', '2', ip],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           encoding='utf-8')
    if reply.returncode == 0:
        return True, ip, timestamp
    else:
        return False, ip, timestamp

def execute_command_ssh(ip,commands, port=22, timeout=10):
    try:
        logging.info(f"Підключення до {ip}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=ip,
            port=port,
            timeout=timeout,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False
        )

        shell = ssh.invoke_shell()
        shell.settimeout(2)
        time.sleep(0.5)

        output = ""
        shell.send("terminal length 0\n")
        time.sleep(0.2)
        shell.recv(65535)

        for idx, cmd in enumerate(commands):
            start = f"!CMD_START_{idx}!"
            end = f"!CMD_END_{idx}!"
            shell.send(f"{start}\n")
            time.sleep(0.1)
            shell.send(cmd + "\n")
            time.sleep(0.2)
            shell.send(f"{end}\n")
            time.sleep(0.1)

        while True:
            try:
                part = shell.recv(60000).decode("utf-8")
                output += part
            except socket.timeout:
                break
        shell.close()
        return output

    except paramiko.AuthenticationException:
        logging.error(f"[AUTH FAIL] {ip} — неправильний логін або пароль")
    except (paramiko.SSHException, socket.timeout, paramiko.ssh_exception.NoValidConnectionsError) as e:
        logging.error(f"[SSH ERROR] {ip} — {e}")
    except Exception as e:
        logging.exception(f"[UNEXPECTED] {ip} — {e}")

def parse_interfaces(results):

    for ip in  results:
        output = results[ip]["commands"]["sh ip int b"]
        results[ip]["interfaces"] = []
        lines = output.strip().splitlines()[2:]

        for line in lines:
            parts = re.split(r"\s+", line.strip())
            if len(parts) >= 6:
                iface = {
                    "interface": parts[0],
                    "ip_address": parts[1],
                    "protocol": parts[5]
                }
                results[ip]["interfaces"].append(iface)

def parse_hostname(results):

    for ip in  results:
        output = results[ip]["commands"]["sh run | i hostname"]
        results[ip]["hostname"] = []
        lines = output.strip().splitlines()[1:2]

        for line in lines:
            parts = re.split(r"\s+", line.strip())
            results[ip]["hostname"]=parts[1]



def main():
    results = {}

    with open("../ip_addresses.txt", "r") as f:
        ips = [line.strip() for line in f if line.strip()]

    logging.info("Починаю перевірку доступності хостів...")
    with ThreadPoolExecutor(max_workers=min(32, os.cpu_count()+4)) as executor:
        futures = {executor.submit(ping_ip, ip): ip for ip in ips}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                is_alive, ip, timestamp = future.result()
                results[ip] = {
                    "status": "online" if is_alive else "offline",
                    "timestamp": timestamp,
                }
            except Exception as e:
                logging.error(f"[FATAL] {ip} crashed: {e}")
                results[ip] = {"status": "error", "error": str(e)}

        online_hosts = [ip for ip, data in results.items() if data["status"] == "online"]
    if online_hosts:
        logging.info(f"Підключаюсь по SSH до {len(online_hosts)} хостів...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(execute_command_ssh, ip, commands): ip for ip in online_hosts}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    output = future.result()
                    if output:
                        results[ip]["commands"] = {}
                        for idx, cmd in enumerate(commands):
                            start_marker = f"!CMD_START_{idx}!"
                            end_marker = f"!CMD_END_{idx}!"
                            match = re.search(rf"\s*{re.escape(start_marker)}\s*(.*?)\s*{re.escape(end_marker)}\s*", output, re.S)

                            if match:
                                cmd_output = match.group(1).strip()
                                results[ip]["commands"][cmd] = cmd_output
                            else:
                                results[ip]["commands"][cmd] = ""
                        logging.info(f"[{ip}] Команди виконані")
                    else:
                        logging.warning(f"[{ip}] Порожній результат")
                except Exception as e:
                    logging.error(f"[SSH FAIL] {ip}: {e}")
                    results[ip]["status"] = "ssh_error"
                    results[ip]["error"] = str(e)
    else:
        logging.warning("Немає доступних хостів для SSH-з'єднання.")



    parse_interfaces(results)
    parse_hostname(results)


    filename = "results.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    logging.info(f"Результати збережено у {filename}")

if __name__ == "__main__":
    main()
