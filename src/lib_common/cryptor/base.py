import binascii

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util import Padding
from Crypto.Util.strxor import strxor

from lib_common.data.utils.generator import RandomBytesGenerator
from .schemas import CryptorRootConfigsM


class CryptoException(Exception):
    pass


class CryptoBase:
    CIPHER_IV_LENGTH = AES.block_size
    TAG_LENGTH = AES.block_size  # 16-byte tag for GCM
    MODE_MAP = {"gcm": AES.MODE_GCM}
    SUPPORTED_PADDINGS = ["pkcs7", "none"]  # GCM does not require padding

    def __init__(self, raw_key: bytes, xform: str):
        self.raw_key = raw_key
        self.alg_name, self.mode, self.padding = self._parse_xform(xform)

    def _parse_xform(self, xform: str):
        """解析xform并校验模式与填充的兼容性"""
        parts = xform.lower().split("/")
        if len(parts) != 3:
            raise CryptoException(f"Invalid xform format: {xform}")

        alg, mode_str, padding = parts
        if alg != "aes":
            raise CryptoException(f"Unsupported algorithm: {alg}")

        if mode_str not in self.MODE_MAP:
            raise CryptoException(f"Unsupported AES mode: {mode_str}")
        mode = self.MODE_MAP[mode_str]
        return alg, mode, padding

    def encrypt(self, plain_bytes: bytes) -> bytes:
        """加密（GCM模式无填充）
        :param plain_bytes: bytes 二进制
        :return: bytes 十六进展
        """
        if self.mode != AES.MODE_GCM:
            raise CryptoException(f"Unsupported mode: {self.mode}")

        iv = RandomBytesGenerator.sby_length(self.CIPHER_IV_LENGTH)
        cipher = AES.new(self.raw_key, self.mode, iv)
        padded_data = Padding.pad(plain_bytes, self.CIPHER_IV_LENGTH, self.padding)

        ciphertext, mac_tag = cipher.encrypt_and_digest(padded_data)
        cipher_bytes = iv + ciphertext + mac_tag
        cipher_hex = binascii.hexlify(cipher_bytes)
        return cipher_hex

    def decrypt(self, cipher_hex: bytes) -> bytes:
        """解密（GCM模式无填充）"""
        if self.mode != AES.MODE_GCM:
            raise CryptoException(f"Unsupported mode: {self.mode}")

        cipher_bytes = binascii.unhexlify(cipher_hex)
        if len(cipher_bytes) < self.CIPHER_IV_LENGTH + self.TAG_LENGTH:
            raise CryptoException("Invalid cipher text")

        iv = cipher_bytes[: self.CIPHER_IV_LENGTH]
        ciphertext = cipher_bytes[self.CIPHER_IV_LENGTH : -self.TAG_LENGTH]
        mac_tag = cipher_bytes[-self.TAG_LENGTH :]

        cipher = AES.new(self.raw_key, self.mode, iv)
        padded_data = cipher.decrypt_and_verify(ciphertext, mac_tag)
        plain_bytes = Padding.unpad(padded_data, self.CIPHER_IV_LENGTH, self.padding)
        return plain_bytes


class KeyManager:
    ROOT_KEY_LENGTH = 32  # AES-256
    WORK_KEY_LENGTH = 32
    PBKDF2_ITERATIONS = 600_000

    def __init__(self, configs: CryptorRootConfigsM):
        self._configs = configs
        if not self._configs:
            raise ValueError("Root configs is required")
        self.root_key = self.derive_root_key()
        self.crypto_base = CryptoBase(self.root_key, "aes/gcm/pkcs7")

    @property
    def root_secret(self) -> bytes:
        secret = binascii.unhexlify(self._configs.secret.get_secret_value())
        if len(secret) < self.ROOT_KEY_LENGTH:
            raise CryptoException("Root secret too short")
        return secret

    @property
    def root_material(self) -> bytes:
        material = binascii.a2b_base64(self._configs.material.get_secret_value())
        if len(material) < self.ROOT_KEY_LENGTH:
            raise CryptoException("Root material too short")
        return material

    @property
    def root_salt(self) -> bytes:
        # 盐值
        return binascii.a2b_base64(self._configs.salt)

    def derive_root_key(self) -> bytes:
        """使用PBKDF2派生根密钥"""
        try:
            material = self.root_material[: self.ROOT_KEY_LENGTH]
            secret = self.root_secret[: self.ROOT_KEY_LENGTH]
            mixed = strxor(material, secret)
            return PBKDF2(
                str(mixed),
                salt=self.root_salt,
                dkLen=self.ROOT_KEY_LENGTH,
                count=self.PBKDF2_ITERATIONS,
                hmac_hash_module=SHA256,
            )
        except Exception as e:
            raise CryptoException(f"Key derivation failed: {e}") from e

    def new_work_key(self) -> bytes:
        """生成随机工作密钥"""
        work_key_bytes = RandomBytesGenerator.sby_length(self.WORK_KEY_LENGTH)
        return self.encrypt_work_key(work_key_bytes)

    def encrypt_work_key(self, plain_work_key: bytes) -> bytes:
        """加密工作密钥
        :param plain_work_key: 明文
        :return: 密文work_key, bytes 16进制
        """
        return self.crypto_base.encrypt(plain_work_key)

    def decrypt_work_key(self, cipher_work_key: bytes) -> bytes:
        """解密工作密钥
        :param cipher_work_key: 密文work_key, bytes 16进制
        :return: 明文work_key, bytes 2进展
        """
        return self.crypto_base.decrypt(cipher_work_key)


class Cryptor:
    def __init__(self, config: CryptorRootConfigsM, work_key: bytes, xform: str = "aes/gcm/pkcs7"):
        self.work_key = work_key
        self.xform = xform
        self.key_manager = KeyManager(config)
        self.crypto_base = CryptoBase(self.key_manager.decrypt_work_key(self.work_key), self.xform)

    def encrypt(self, plain_text: str) -> str:
        """:param plain_text:
        :return:
        """
        try:
            plain_bytes = plain_text.encode("utf-8")
            cipher_bytes = self.crypto_base.encrypt(plain_bytes)
            cipher_text = cipher_bytes.decode("utf-8")
            return cipher_text
        except Exception as e:
            raise CryptoException(f"Encryption failed: {e}") from e

    def decrypt(self, cipher_text: str) -> str:
        try:
            cipher_bytes = cipher_text.encode("utf-8")
            plain_bytes = self.crypto_base.decrypt(cipher_bytes)
            plain_text = plain_bytes.decode("utf-8")
            return plain_text
        except Exception as e:
            raise CryptoException(f"Decryption failed: {e}") from e

    def verify(self, plain_text: str, cipher_text: str) -> bool:
        if plain_text == self.decrypt(cipher_text):
            return True
        else:
            return False
