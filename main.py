import os
import time
import socket
import paramiko
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("user")
password = os.getenv("pass")
command_file = "commands.txt"
ip_addresses = "ip_addres.txt"

def execute_command_ssh(ip, commands, port=22, timeout=10):
    try:
        print(f"\n=== CONNECTING TO {ip} ===")
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

        full_output = ""
        for cmd in commands:
            shell.send(cmd + "\n")
            time.sleep(0.3)
            while shell.recv_ready():
                full_output += shell.recv(65535).decode("utf-8")

        shell.close()
        ssh.close()

        #clean_output = "\n".join(line.strip() for line in full_output.splitlines() if line.strip())
        print(full_output)

    except paramiko.ssh_exception.IncompatiblePeer as e:
        print(f"[ERROR] {ip} - Incompatible SSH peer: {e}")
    except paramiko.ssh_exception.AuthenticationException:
        print(f"[ERROR] {ip} - Authentication failed")
    except paramiko.ssh_exception.NoValidConnectionsError:
        print(f"[ERROR] {ip} - Cannot connect (No valid connections)")
    except socket.timeout:
        print(f"[ERROR] {ip} - Connection timed out")
    except Exception as e:
        print(f"[ERROR] {ip} - Unexpected error: {e}")



def configure_device ():
    try:
        with open(command_file, "r") as f:
            commands = [line.strip() for line in f if line.strip()]
        with open(ip_addresses, "r") as f1:
            ips = [line.strip() for line in f1 if line.strip()]
        for ip in ips:
            execute_command_ssh(ip, commands)
    except FileNotFoundError:
        print("Файл не знайдено")
    except Exception as e:
        print(f"Несподівана помилка: {e}")

def main():
    configure_device()

if __name__ == "__main__":
    main()