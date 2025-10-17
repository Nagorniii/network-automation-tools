import os
import time

import paramiko
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("user")
password = os.getenv("pass")
ip1 = "10.153.0.252"

def execute_command_ssh(ip, port=22,timeout=10):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)

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

    shell.send("sh int desc\n")
    time.sleep(0.2)
    output = shell.recv(60000).decode("utf-8")

    shell.close()
    print(output)

def main():
    print("Hello")
    execute_command_ssh(ip1)
    print("goodbye")


if __name__ == "__main__":
    main()