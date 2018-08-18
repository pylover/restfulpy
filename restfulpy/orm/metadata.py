from ..utils import to_camel_case


class FieldInfo:
    def __init__(self, type_=str, default=None, pattern=None, max_length=None,
                 min_length=None, readonly=False, protected=False, min_=None,
                 max_=None, not_none=None, required=None):
        self.type_ = type_ if isinstance(type_, str) else type_.__name__
        self.default = default
        self.pattern = pattern
        self.max_length = max_length
        self.min_length = min_length
        self.min_ = min_
        self.max_ = max_
        self.readonly = readonly
        self.protected = protected
        self.not_none = not_none
        self.required = required

    def to_json(self):
        return {
            'type': self.type_,
            'default_': self.default,
            'not_none': self.not_none,
            'required': self.required,
            'pattern': self.pattern,
            'maxLength': self.max_length,
            'minLength': self.min_length,
            'readonly': self.readonly,
            'protected': self.protected,
            'min': self.min_,
            'max': self.max_
        }

    def __copy__(self):
        new_one = type(self)()
        new_one.__dict__.update(self.__dict__)
        return new_one

    def to_dict(self):
        return self.__dict__


class MetadataField(FieldInfo):
    def __init__(self, name, key, primary_key=False, label=None,
                 watermark=None, icon=None, message='Invalid value',
                 example=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.key = key[1:] if key.startswith('_') else key
        self.primary_key = primary_key
        self.label = label or watermark
        self.watermark = watermark
        self.example = example

    @classmethod
    def from_column(cls, c, info=None):
        if not info:
            info = c.info
        json_name = info.get('json', to_camel_case(c.key))
        result = []

        key = c.key

        if hasattr(c, 'default') and c.default:
            default_ = c.default.arg if c.default.is_scalar else None
        else:
            default_ = None

        if hasattr(c, 'type'):
            try:
                type_ = c.type.python_type
            except NotImplementedError:
                # As we spoke, hybrid properties have no type
                type_ = ''
        else:  # pragma: no cover
            type_ = 'str'

        result.append(cls(
            json_name,
            key,
            type_=type_,
            default=default_,
            not_none=info.get('not_none'),
            required=info.get('required'),
            pattern=info.get('pattern'),
            max_length=info.get('max_length') if 'max_length' in info else (
                c.type.length if hasattr(c, 'type') \
                and hasattr(c.type, 'length') else None
            ),
            min_length=info.get('min_length'),
            min_=info.get('min'),
            max_=info.get('max'),
            watermark=info.get('watermark', None),
            label=info.get('label', None),
            example=info.get('example', None),
            primary_key=hasattr(c.expression, 'primary_key') \
                and c.expression.primary_key,
            readonly=info.get('readonly', False),
            protected=info.get('protected', False)
        ))

        return result

    def to_json(self):
        result = super().to_json()
        result.update(
            name=self.name,
            example=self.example,
            watermark=self.watermark,
            label=self.label,
            key=self.key,
            primaryKey=self.primary_key,
        )
        return result

