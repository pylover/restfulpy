

class LemurException(Exception):
    def to_json(self):
        return {
            'type': str(type(self)),
            'content': str(self),
        }


class FileNotFoundException(LemurException):
    pass


class OrmException(LemurException):
    pass


class KeyDecodeError(OrmException):
    pass


class FormParserError(LemurException):
    def __init__(self):
        super(FormParserError, self).__init__('Cannot parse the form.')


class ValidationError(LemurException):
    field = None

    def __init__(self, field_name, *args, **kw):
        self.field = field_name
        super(ValidationError, self).__init__(*args, **kw)

    def to_json(self):
        d = super(ValidationError, self).to_json()
        d['field'] = self.field
        return d
