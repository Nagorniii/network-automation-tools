import os
import time
import socket
import paramiko
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dotenv import load_dotenv

load_dotenv()

logging.getLogger("paramiko").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("main.log", mode="w"),
        logging.StreamHandler()
    ]
)

username = os.getenv("user")
password = os.getenv("pass")
command_file = "commands.txt"
ip_addresses = "ip_address.txt"
backup_folder = "backup"

os.makedirs(backup_folder, exist_ok=True)


def read_until_prompt(shell, prompt="#", pause=0.2, max_wait=300):
    output = ""
    start_time = time.time()

    while True:
        if shell.recv_ready():
            data = shell.recv(65535).decode("utf-8", errors="ignore")
            output += data
            if prompt in output.splitlines()[-1]:
                break
        else:
            time.sleep(pause)
        if time.time() - start_time > max_wait:
            break

    return output

def read_commands():
    try:
        with open(command_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Файл команд '{command_file}' не знайдено.")
        return []


def execute_command_ssh(ip, commands, port=22, timeout=10):
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
        time.sleep(0.5)

        output = ""
        shell.send("terminal length 0\n")
        time.sleep(0.5)
        shell.recv(65535)

        for cmd in commands:
            shell.send(cmd + "\n")
            time.sleep(0.5)
            output += read_until_prompt(shell, prompt="#")


        shell.close()
        ssh.close()

        if output.strip():
            timestamp = datetime.now().strftime("%Y_%m_%d")
            backup_file = os.path.join(backup_folder, f"{ip}_{timestamp}.txt")
            with open(backup_file, "w") as backf:
                backf.write(output)
            logging.info(f"[OK] Конфігурація {ip} збережена у {backup_file}")
        else:
            logging.warning(f"[WARN] Від {ip} не отримано жодного виводу")


    except paramiko.AuthenticationException:
        logging.error(f"[AUTH FAIL] {ip} — неправильний логін або пароль")
    except (paramiko.SSHException, socket.timeout, paramiko.ssh_exception.NoValidConnectionsError) as e:
        logging.error(f"[SSH ERROR] {ip} — {e}")
    except Exception as e:
        logging.exception(f"[UNEXPECTED] {ip} — {e}")


def main():
    commands = read_commands()
    if not commands:
        logging.error("Не знайдено команд для виконання.")
        return
    try:
        with open(ip_addresses, "r") as f1:
            ips = [line.strip() for line in f1 if line.strip()]
    except FileNotFoundError:
        logging.error(f"Файл із IP '{ip_addresses}' не знайдено.")
        return

    with ThreadPoolExecutor(max_workers = min(32, os.cpu_count()+4)) as executor:
        futures = {executor.submit(execute_command_ssh, ip, commands):ip for ip in ips}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"[FATAL] {ip} crashed: {e}")

    logging.info("Роботу завершено.")

if __name__ == "__main__":
    main()