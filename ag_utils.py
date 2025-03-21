from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import os


config_path = os.environ.get("AG_CONFIG_PATH")


def read_from_file(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return f.read()


def write_to_file(file_path: str, content: bytes):
    with open(file_path, "wb") as f:
        f.write(content)


def generate_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def encrypt_data(data: str, key: bytes) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data.encode()) + encryptor.finalize()
    return iv + encrypted_data


def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_data.decode()


def get_siliconflow_api_key():
    path = config_path + "/siliconflow.txt"
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    return content.strip()


def get_deepseek_api_key():
    password = "asoulbella"
    key_file_path = config_path + "/encryption_key.txt"
    key_content = read_from_file(key_file_path)
    salt = key_content[:16]
    key = generate_key(password, salt)

    encrypted_file_path = config_path + "/deepseek.txt"
    encrypted_data = read_from_file(encrypted_file_path)

    decrypted_data = decrypt_data(encrypted_data, key)
    return decrypted_data


def get_api_key(vendor):
    if vendor == "siliconflow":
        return get_siliconflow_api_key()
    elif vendor == "deepseek":
        return get_deepseek_api_key()
    else:
        return None


def multi_line_input():
    lines = []
    while True:
        line = input()
        if line.strip() == "" or line.strip() == "EOF":
            break
        if line.strip() == "exit" or line.strip() == "quit" or line.strip() == "q":
            return "exit"
        lines.append(line)
    return "\n".join(lines)
