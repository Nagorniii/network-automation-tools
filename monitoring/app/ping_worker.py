import subprocess
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logging.getLogger("subprocess").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("main.log", mode="w"),
        logging.StreamHandler()
    ]
)

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


def main():
    """with open("../ip_addresses.txt", "r") as f:
        ips = [line.strip() for line in f if line.strip()]
    with ThreadPoolExecutor(max_workers = min(32, os.cpu_count()+4)) as executor:
        futures = {executor.submit(ping_ip, ip):ip for ip in ips}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                is_alive, ip, timestamp = future.result()
                if is_alive:
                    logging.info(f"{timestamp} {ip} - Online")
                else:
                    logging.info(f"{timestamp} {ip} - Offline")

            except Exception as e:
                logging.error (f"[FATAL] {ip} crashed: {e}")"""

if __name__ == "__main__":
    main()
