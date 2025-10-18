# SSH Backup Tool

A lightweight Python tool for **automated network device configuration backup** over SSH.  
It connects to each IP address from a list, runs a set of commands, and saves the output to timestamped text files.

---

## 🔧 Features

- Parallel SSH connections using `ThreadPoolExecutor`
- Handles authentication and connection errors gracefully
- Logs all activity to `main.log`
- Automatically creates a backup directory
- Environment-based credential management (`.env` file)

---

## 📂 Project Structure

```
project/
│
├── main.py                # Main script
├── commands.txt           # List of commands to execute
├── ip_address.txt         # Target IP addresses
├── .env                   # Environment variables (login/password)
├── backup/                # Backup results
├── main.log               # Execution log
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Requirements

Python 3.8+  

All dependencies are listed in `requirements.txt`.  
To install them, run:

```bash
pip install -r requirements.txt
```

---

## 🧩 Setup

1. Create a `.env` file in the project root:
   ```
   user=admin
   pass=your_password
   ```

2. Create `commands.txt` with the list of commands to execute:
   ```
   show version
   show running-config
   ```

3. Create `ip_address.txt` with the list of target IPs:
   ```
   10.0.0.1
   10.0.0.2
   ```

---

## 🚀 Run

```
python3 main.py
```

The output for each device will be saved in the `backup/` folder as:
```
backup/10.0.0.1_2025_10_18.txt
```

---

## 🧠 How It Works

1. Loads SSH credentials from `.env`
2. Reads IP addresses and command list
3. Launches a thread for each IP:
   - Establishes SSH connection  
   - Executes commands  
   - Saves output to a timestamped file  
4. Logs all events and errors to `main.log`

---

## ⚠️ Error Handling

Type | Message | Cause  
---- | -------- | ------
`[AUTH FAIL]` | Invalid username or password | Authentication failed  
`[SSH ERROR]` | Unable to connect | Host unreachable or SSH port closed  
`[WARN]` | Empty output | Command returned no data  
`[UNEXPECTED]` | Unexpected error | Other exceptions  

---

## 🧰 Example Log Output

```
2025-10-18 12:30:01 [INFO] Connecting to 10.0.0.1...
2025-10-18 12:30:03 [OK] Configuration from 10.0.0.1 saved to backup/10.0.0.1_2025_10_18.txt
2025-10-18 12:30:03 [INFO] Task completed.
```

---

## 🪪 Author

**Yevhenii**  
Purpose: Simplify automated SSH configuration backups for network devices.

---

## 🚧 Future Improvements

- Support for Telnet and SFTP  
- Save output in JSON or structured format  
- Command execution timeout per device  
- Automatic diff detection between backups  
- Integration with NetBox or other CMDBs
