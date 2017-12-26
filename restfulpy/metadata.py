from restfulpy.utils import to_camel_case


class Field:
    def __init__(self, name, type_=str, default_=None, optional=None,
                 pattern=None, max_length=None, min_length=None,
                 example=None, readonly=False,
                 protected=False):
        self.name = name
        self.type_ = type_
        self.default_ = default_
        self.optional = optional
        self.pattern = pattern
        self.max_length = max_length
        self.min_length = min_length
        self.example = example
        self.readonly = readonly
        self.protected = protected

    @property
    def type_name(self):
        return self.type_ if isinstance(self.type_, str) else self.type_.__name__

    def to_json(self):
        return dict(
            name=self.name,
            type_=self.type_name,
            default=self.default_,
            optional=self.optional,
            pattern=self.pattern,
            maxLength=self.max_length,
            minLength=self.min_length,
            example=self.example,
            readonly=self.readonly,
            protected=self.protected
        )


class MetadataField(Field):
    def __init__(self, name, key, primary_key=False, label=None, watermark=None, icon=None,
                 message='Invalid value', **kwargs):
        super().__init__(name, **kwargs)
        self.key = key[1:] if key.startswith('_') else key
        self.primary_key = primary_key
        self.label = label or watermark
        self.watermark = watermark
        self.icon = icon
        self.message = message

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
            default_=default_,
            optional=c.nullable if hasattr(c, 'nullable') else None,
            pattern=info.get('pattern'),
            max_length=info.get('max_length') if 'max_length' in info else
                (c.type.length if hasattr(c, 'type') and hasattr(c.type, 'length') else None),
            min_length=info.get('min_length'),
            message=info.get('message', 'Invalid Value'),
            watermark=info.get('watermark', None),
            label=info.get('label', None),
            icon=info.get('icon', None),
            example=info.get('example', None),
            primary_key=hasattr(c.expression, 'primary_key') and c.expression.primary_key,
            readonly=info.get('readonly', False),
            protected=info.get('protected', False)
        ))

        return result

    def to_json(self):
        result = super().to_json()
        result.update(
            message=self.message,
            watermark=self.watermark,
            label=self.label,
            icon=self.icon,
            key=self.key,
            primaryKey=self.primary_key,
        )
        return result
