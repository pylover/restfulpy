from ..utils import to_camel_case


class FieldInfo:
    def __init__(self, type_=str, max_length=None, min_length=None,
                  minimum=None, maximum=None, default=None, readonly=False,
                  pattern=None, pattern_description=None, protected=False,
                  not_none=None, required=None):
        self.type_ = type_
        self.pattern = pattern
        self.pattern_description = pattern_description
        self.max_length = max_length
        self.min_length = min_length
        self.minimum = minimum
        self.maximum = maximum
        self.readonly = readonly
        self.protected = protected
        self.not_none = not_none
        self.required = required
        self.default = default

    def to_json(self):
        type_ = self.type_[0] \
            if self.type_ and isinstance(self.type_, tuple) else self.type_

        return {
            'type': type_.__name__ if self.type_ else None,
            'not_none': self.not_none,
            'required': self.required,
            'pattern': self.pattern,
            'pattern_description': self.pattern_description,
            'maxLength': self.max_length,
            'minLength': self.min_length,
            'readonly': self.readonly,
            'protected': self.protected,
            'minimum': self.minimum,
            'maximum': self.maximum,
            'default': self.default,
        }

    def __copy__(self):
        new_one = type(self)()
        new_one.__dict__.update(self.__dict__)
        return new_one

    def to_dict(self):
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }


class MetadataField(FieldInfo):
    def __init__(self, name, key, primary_key=False, label=None,
                 watermark=None, message=None, example=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.key = key[1:] if key.startswith('_') else key
        self.primary_key = primary_key
        self.label = label
        self.watermark = watermark
        self.example = example
        self.message = message

    @classmethod
    def from_column(cls, c, info=None):
        if not info:
            info = c.info
        json_name = info.get('json') or to_camel_case(c.key)
        result = []

        key = c.key

        if hasattr(c, 'default') and c.default:
            default = c.default.arg if c.default.is_scalar else None
        else:
            default = None

        result.append(cls(
            json_name,
            key,
            default=default,
            type_=info.get('type'),
            not_none=info.get('not_none'),
            required=info.get('required'),
            pattern=info.get('pattern'),
            pattern_description=info.get('pattern_description'),
            max_length=info.get('max_length'),
            min_length=info.get('min_length'),
            minimum=info.get('minimum'),
            maximum=info.get('maximum'),
            watermark=info.get('watermark', None),
            label=info.get('label', None),
            example=info.get('example', None),
            primary_key=hasattr(c.expression, 'primary_key') \
                and c.expression.primary_key,
            readonly=info.get('readonly', False),
            protected=info.get('protected', False),
            message=info.get('message')
        ))

        return result

    def to_json(self):
        result = super().to_json()
        result.update(
            name=self.name,
            example=self.example,
            watermark=self.watermark,
            label=self.label,
            message=self.message,
            key=self.key,
            primaryKey=self.primary_key,
        )
        return result

