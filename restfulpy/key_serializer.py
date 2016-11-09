from hashids import Hashids


class BaseKeySerializer(object):

    def dumps(self, v):
        raise NotImplementedError()

    def loads(self, v):
        raise NotImplementedError()


class XorKeySerializer(BaseKeySerializer):

    def __init__(self, secret):
        self.secret = int(secret)

    def dumps(self, v):
        assert isinstance(v, int)
        return hex(v ^ self.secret)[2:]

    def loads(self, v):
        return int(v, 16) ^ self.secret


class HashIdSerializer(BaseKeySerializer):
    def __init__(self, salt):
        self.hash_maker = Hashids(salt=salt)

    def dumps(self, v):
        assert isinstance(v, int)
        return self.hash_maker.encode(v)

    def loads(self, v):
        assert isinstance(v, str)
        result = self.hash_maker.decode(v)

        if not result:
            raise ValueError('invalid id')

        return result[0]


if __name__ == '__main__':
    s = XorKeySerializer(34523534)

    for i in range(2 ** 16):
        d = s.dumps(i)

        if i % 1000000:
            print(i, d)
        assert i == s.loads(d)
