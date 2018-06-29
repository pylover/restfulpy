

import re

from sqlalchemy import Column, Unicode, String
from sqlalchemy.orm import relationship as sa_relationship, \
    composite as sa_composite, synonym as sa_synonym
from nanohttp import HttpBadRequest

from ..utils import to_camel_case
from ..fieldinfo import FieldInfo


# noinspection PyAbstractClass
class Field(Column):

    @property
    def can_validate(self):
        return 'pattern' in self.info or \
            'min_length' in self.info or \
            'max_length' in self.info or \
            'max' in self.info or \
            'min' in self.info

    def __init__(self,
                 *args,
                 json=None,
                 readonly=None,
                 max_length=None,
                 min_length=None,
                 max_=None,
                 min_=None,
                 pattern=None,
                 protected=None,
                 watermark=None,
                 nullable=False,
                 label=None,
                 icon=None,
                 example=None,
                 message=None,
                 info=None,
                 **kwargs):
        info = info or dict()

        if json is not None:
            info['json'] = json

        if readonly is not None:
            info['readonly'] = readonly

        if protected is not None:
            info['protected'] = protected

        if watermark is not None:
            info['watermark'] = watermark

        if max_length is not None:
            info['max_length'] = max_length
        elif args and isinstance(args[0], (Unicode, String)):
            info['max_length'] = args[0].length

        if min_length is not None:
            info['min_length'] = min_length

        if max_ is not None:
            info['max'] = max_

        if min_ is not None:
            info['min'] = min_

        if pattern is not None:
            info['pattern'] = pattern

        if label is not None:
            info['label'] = label

        if icon is not None:
            info['icon'] = icon

        if example is not None:
            info['example'] = example

        if message is not None:
            info['message'] = message

        super(Field, self).__init__(*args, info=info, nullable=nullable, **kwargs)

    def _validate_pattern(self, value):
        if not re.match(self.info['pattern'], value):
            raise HttpBadRequest('Cannot match field: %s with value "%s" by acceptable pattern' % (self.name, value))
        return value

    def _validate_length(self, value, min_length, max_length):
        if not isinstance(value, str):
            raise HttpBadRequest(status_text='Invalid type: %s for field: %s' % (type(value), self.name))

        value_length = len(value)
        if min_length is not None and value_length < min_length:
            raise HttpBadRequest(
                status_text=f'Please enter at least {min_length} characters for field: {self.name}.'
            )

        if max_length is not None and value_length > max_length:
            raise HttpBadRequest(
                status_text=f'Cannot enter more than: {max_length} in field: {self.name}.'
            )

    def _validate_min_max(self, value, min_, max_):
        if not isinstance(value, (int, float)):
            raise HttpBadRequest(status_text='Invalid type: %s for field: %s' % (type(value), self.name))

        if min_ is not None and value < min_:
            import pudb; pudb.set_trace()  # XXX BREAKPOINT
            raise HttpBadRequest(
                status_text=f'Minimum allowed value is {min_} for field: {self.name}.'
            )

        if max_ is not None and value > max_:
            import pudb; pudb.set_trace()  # XXX BREAKPOINT
            raise HttpBadRequest(
                status_text=f'Maximum allowed value is {max_} for field: {self.name}.'
            )


    def validate(self, value):
        if value is None:
            return value

        if 'pattern' in self.info:
            self._validate_pattern(value)

        if 'min_length' in self.info or 'max_length' in self.info:
            self._validate_length(value, self.info.get('min_length'), self.info.get('max_length'))

        if 'min' in self.info or 'max' in self.info:
            self._validate_min_max(self, self.info.get('min'), self.info.get('max'))
        return value


def relationship(*args, json=None, protected=None, **kwargs):
    info = dict()

    if json:
        info['json'] = json

    if protected:
        info['protected'] = protected

    return sa_relationship(*args, info=info, **kwargs)


def composite(*args, json=None, protected=None, readonly=None, **kwargs):
    info = dict()

    if json is not None:
        info['json'] = json

    if protected is not None:
        info['protected'] = protected

    if readonly is not None:
        info['readonly'] = readonly

    return sa_composite(*args, info=info, **kwargs)


def synonym(*args, json=None, protected=None, readonly=None, **kwargs):
    info = dict()

    if json is not None:
        info['json'] = json

    if protected is not None:
        info['protected'] = protected

    if readonly is not None:
        info['readonly'] = readonly

    return sa_synonym(*args, info=info, **kwargs)


class ModelFieldInfo(FieldInfo):
    def __init__(self, name, key, primary_key=False, label=None, watermark=None, icon=None,
                 message='Invalid value', example=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.key = key[1:] if key.startswith('_') else key
        self.primary_key = primary_key
        self.label = label or watermark
        self.watermark = watermark
        self.icon = icon
        self.message = message
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
            optional=c.nullable if hasattr(c, 'nullable') else None,
            pattern=info.get('pattern'),
            max_length=info.get('max_length') if 'max_length' in info else
                (c.type.length if hasattr(c, 'type') and hasattr(c.type, 'length') else None),
            min_length=info.get('min_length'),
            min_=info.get('min'),
            max_=info.get('max'),
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
            name=self.name,
            example=self.example,
            message=self.message,
            watermark=self.watermark,
            label=self.label,
            icon=self.icon,
            key=self.key,
            primaryKey=self.primary_key,
        )
        return result

