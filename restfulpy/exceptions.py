

class RestfulException(Exception):
    def to_json(self):
        return {
            'type': str(type(self)),
            'content': str(self),
        }
