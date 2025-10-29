# NetBox Automation Script

A lightweight Python utility for automating IP and prefix management in **NetBox**. The script allows you to view, create, and manage prefixes and IP addresses directly through the NetBox API, with interactive prompts for fast network provisioning.

## Features

- View existing prefixes in NetBox
- Create new prefixes automatically
- Allocate available IP addresses within a prefix
- Auto-generate related subnets and switch/router IPs
- Supports tag creation and assignment on the fly
- Interactive CLI menu for quick operations

## Requirements

- Python 3.8+
- Dependencies:


```
  pip install -r requirements.txt
```
- A valid NetBox API token

## Configuration

Create a `.env` file in the same directory as the script:

```
NETBOX_URL=https://your-netbox-instance/api
NETBOX_TOKEN=your_api_token
```


## Usage

Run the script from the terminal:

```
python main.py
```

Then select from the interactive menu:

```
=== Main Menu ===
1. View all prefixes
2. Create a new prefix
3. Add network and related IPs
4. Add IP manually
0. Exit
```

Example output:
```
✅ Created prefix 10.10.1.0/27
✅ Created IP 10.10.1.1/27
```


