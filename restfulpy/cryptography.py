import abc
import os

from Crypto.Cipher import AES


class Cipher(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def encrypt(self, raw):
        pass

    @abc.abstractmethod
    def decrypt(self, enc):
        pass


class AESCipher(Cipher):

    def __init__(self, key, random=os.urandom):
        self.bs = 16
        self.key = key
        self.random = random

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = self.random(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc):
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        result = self._unpad(cipher.decrypt(enc[AES.block_size:]))
        if not result.strip():
            raise ValueError()
        return result

    def _pad(self, s):
        remaining_bytes = len(s) % self.bs
        padding_bytes = self.bs - remaining_bytes
        return s + padding_bytes * bytes([padding_bytes])

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


