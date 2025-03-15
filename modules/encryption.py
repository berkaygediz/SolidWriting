import base64
import hashlib


class EncryptionEngine:
    def __init__(self, key: str):
        self.key = hashlib.md5(key.encode()).digest()

    def encrypt(self, content: str) -> str:
        encrypted_content = bytearray(content, "utf-8")

        for i in range(len(encrypted_content)):
            encrypted_content[i] ^= self.key[i % len(self.key)]

        return base64.b64encode(encrypted_content).decode("utf-8")

    def decrypt(self, encrypted_content: str) -> str:
        encrypted_content = base64.b64decode(encrypted_content)
        decrypted_content = bytearray(encrypted_content)

        for i in range(len(decrypted_content)):
            decrypted_content[i] ^= self.key[i % len(self.key)]

        return decrypted_content.decode("utf-8")
