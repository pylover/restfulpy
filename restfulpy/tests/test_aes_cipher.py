from restfulpy.cryptography import AESCipher


def mockup_random(size):
    return b'#' * size


def test_encrypt():
    key = b'1234567890123456'
    message = b'test-message'
    encrypted = b'################>T2\tyZ\\\x0f20[\x97e\x97\xbb5'
    cipher = AESCipher(key, random=mockup_random)
    assert encrypted == cipher.encrypt(message)
    assert message == cipher.decrypt(encrypted)

