from cryptography.fernet import Fernet
key = Fernet.generate_key()
print("Kopyala bunu .env dosyasına FERNET_KEY= olarak yapıştır:")
print(key.decode())