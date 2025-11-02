# 🖥️ Network Monitoring Tool

A lightweight network monitoring system that periodically checks the availability of devices and retrieves interface information over SSH.  
The project combines Python + Flask for backend processing and a simple web interface for visualization.

---

## 🚀 Features

- ICMP (ping) availability checks  
- SSH connection to network devices (Cisco-like syntax supported)  
- Parsing of:
  - Hostname  
  - Interface status (`show ip interface brief`)
- Results saved to `results.json`
- Web dashboard for quick visibility of device status and interfaces
- Automatic periodic scanning in background

---

## 🧱 Project Structure

```
monitoring/
│
├── app/
│   ├── main.py              # Flask web server
│   ├── ssh_worker.py        # Core logic: ping + SSH execution + parsing
│   ├── templates/
│   │   └── index.html       # Web UI page
│   ├── static/
│   │   └── styles.css       # Styling for dashboard
│   │   └── script.js  
│   └── ip_addresses.txt     # List of devices to monitor
│
├── Dockerfile               # Container build definition
├── docker-compose.yml       # Service configuration
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

---

## ⚙️ Configuration

Create a `.env` file in `app/` directory:

```bash
user=your_ssh_username
pass=your_ssh_password
```

List all target devices in `ip_addresses.txt`:

```
10.10.10.1
10.10.10.2
10.10.10.3
```

---

## 🐳 Docker Setup

### Build and start the container

```
cd monitoring
docker compose up --build -d
```

The Flask web interface will be available at:

👉 http://localhost:5000

---

## 🖼️ Web Interface

The main dashboard displays:
- **IP** — Device address  
- **Status** — Online/offline  
- **Hostname** — Parsed from device config  
- **Interfaces** — Interface state (e.g. `GI0/0/0 (up)`)  
- **Timestamp** — Last scan time  

The table updates automatically every 10 seconds.

---

## 🔁 Manual scan

You can trigger an immediate scan manually via:

```
http://localhost:5000/api/scan
```

Or by pressing refresh in the browser — background scanning runs automatically every few minutes.

---

## 🧰 Development

Install dependencies locally (optional, if not using Docker):

```
pip install -r requirements.txt
python app/main.py
```

---

## 📄 License

This project is released under the MIT License.
You are free to use and modify it for both personal and commercial projects.

---

## 👤 Author

Developed by **Євгеній Нагорний**  
📧 _for internal network automation and monitoring usage_
