import sqlite3
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def decrypt_pgadmin():
    db_path = r'C:\Users\ankur\AppData\Roaming\pgAdmin\pgadmin4.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM keys WHERE name='SECURITY_PASSWORD_SALT';")
    salt = cursor.fetchone()[0].encode('utf-8')
    
    master_pw = b'epgFwjYb2oYQ_R0l'
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=25000,
    )
    key = kdf.derive(master_pw)
    
    cursor.execute("SELECT id, name, username, password FROM server;")
    servers = cursor.fetchall()
    print("Servers:", servers)
    
    for s in servers:
        s_id, name, username, enc_pw = s
        if enc_pw:
            print(f"Encrypted password for {name} ({username}): {enc_pw}")
            try:
                raw = base64.b64decode(enc_pw)
                nonce = raw[:12]
                ciphertext = raw[12:]
                aesgcm = AESGCM(key)
                decrypted = aesgcm.decrypt(nonce, ciphertext, None)
                print(f"DECRYPTED PASSWORD: {decrypted.decode('utf-8')}")
            except Exception as e:
                print(f"Decryption error: {e}")
        else:
            print(f"Server {name} has no saved password stored.")
            
    conn.close()

if __name__ == "__main__":
    decrypt_pgadmin()
