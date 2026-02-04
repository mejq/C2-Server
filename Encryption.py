import os
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()

raw_key = os.getenv("FERNET_KEY")
if not raw_key:
    raise ValueError("Fernet key is missing")

try:
    FERNET_KEY = raw_key.encode('utf-8') # string -> bytes
    fernet_instance = Fernet(FERNET_KEY)
except Exception as e:
    raise ValueError(f"Fernet key is invalid Error: {e}")



#Takes plain text and encrypts it.
def encrypt_data(plain_text: str) -> str:
    try:
        data_bytes = plain_text.encode('utf-8')
        token = fernet_instance.encrypt(data_bytes)
        return token.decode('ascii')
    except Exception as e:
        raise RuntimeError(f"Encryption Error: {e}")


#Takes encrypted message and decrypts it.
def decrypt_data(token_str: str) -> str:
    try:
        token_bytes = token_str.encode('ascii')
        plain_text = fernet_instance.decrypt(token_bytes)
        return plain_text.decode('utf-8')
    except InvalidToken as e:
        raise ValueError(f"Invalid or Corrupted Token Error: {e}")
    except Exception as e:
        raise RuntimeError(f"Encryption Error: {e}")