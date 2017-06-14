

class RestfulException(Exception):
    def to_json(self):
        return {
            'type': str(type(self)),
            'content': str(self),
        }


class UnsupportedError(Exception):
    """Used to indicate we're not supporting a feature and or method.

    .. versionadded:: 0.11.0

    """
    pass
