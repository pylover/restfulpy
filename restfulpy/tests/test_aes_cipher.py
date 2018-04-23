import unittest

from restfulpy.cryptography import AESCipher


def mockup_random(size):
    return b'#' * size


class AESCipherTestCase(unittest.TestCase):
    def test_encrypt(self):
        key = b'1234567890123456'
        message = b'test-message'
        encrypted = b'################>T2\tyZ\\\x0f20[\x97e\x97\xbb5'
        cipher = AESCipher(key, random=mockup_random)
        self.assertEqual(encrypted, cipher.encrypt(message))
        self.assertEqual(message, cipher.decrypt(encrypted))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

