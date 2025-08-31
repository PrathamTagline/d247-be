import json
import hashlib
from base64 import b64decode
from Crypto.Cipher import AES
import os
from base64 import b64encode

def openssl_bytes_to_key(password: bytes, salt: bytes, key_len: int, iv_len: int):
    """
    Replicates OpenSSL's EVP_BytesToKey (MD5 based).
    Derives a key and IV from the given password and salt.
    """
    dtot = b''
    d = b''
    while len(dtot) < (key_len + iv_len):
        d = hashlib.md5(d + password + salt).digest()
        dtot += d
    return dtot[:key_len], dtot[key_len:key_len + iv_len]


def decrypt_data(ciphertext: str, password: str):
    raw = b64decode(ciphertext)

    if not raw.startswith(b"Salted__"):
        raise ValueError("Invalid ciphertext format")

    salt = raw[8:16]
    encrypted = raw[16:]

    key, iv = openssl_bytes_to_key(password.encode(), salt, 32, 16)
    cipher = AES.new(key, AES.MODE_CBC, iv)

    decrypted = cipher.decrypt(encrypted)

    # Remove PKCS7 padding
    pad_len = decrypted[-1]
    if pad_len < 1 or pad_len > AES.block_size:
        raise ValueError("Invalid padding")
    decrypted = decrypted[:-pad_len]

    text = decrypted.decode("utf-8")
    try:
        return json.loads(text)
    except Exception:
        return text



def encrypt_data(data, password: str) -> str:
    """
    Encrypts data using AES-256-CBC (OpenSSL compatible with Salted__ header).
    Returns Base64 encoded string.
    """
    # Convert to JSON string if dict/object
    if not isinstance(data, str):
        data = json.dumps(data)

    data_bytes = data.encode("utf-8")

    # PKCS7 padding
    pad_len = AES.block_size - (len(data_bytes) % AES.block_size)
    data_bytes += bytes([pad_len]) * pad_len

    # Generate salt
    salt = os.urandom(8)

    # Derive key and IV
    key, iv = openssl_bytes_to_key(password.encode(), salt, 32, 16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(data_bytes)

    # Prepend Salted__ + salt (OpenSSL format)
    openssl_blob = b"Salted__" + salt + encrypted
    return b64encode(openssl_blob).decode("utf-8")
