import os

from cryptography.fernet import Fernet

# must be same on both client and server
SECRET_KEY = ""
cipher = Fernet(SECRET_KEY)

def encrypt_data(data):
    encoded = data.encod()
    encrypted = cipher.encrypt(encoded)
    return encrypted.decode()

def decrypt_data(data):
    decrypted = cipher.decrypt(data.encode())
    return decrypted.decode()