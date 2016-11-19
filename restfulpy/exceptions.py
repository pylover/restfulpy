

class RestfulException(Exception):
    def to_json(self):
        return {
            'type': str(type(self)),
            'content': str(self),
        }


class FileNotFoundException(RestfulException):
    pass


class OrmException(RestfulException):
    pass


class KeyDecodeError(OrmException):
    pass


class FormParserError(RestfulException):
    def __init__(self):
        super(FormParserError, self).__init__('Cannot parse the form.')


class ValidationError(RestfulException):
    field = None

    def __init__(self, field_name, *args, **kw):
        self.field = field_name
        super(ValidationError, self).__init__(*args, **kw)

    def to_json(self):
        d = super(ValidationError, self).to_json()
        d['field'] = self.field
        return d
