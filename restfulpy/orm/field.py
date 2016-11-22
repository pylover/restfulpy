

import re

from sqlalchemy import Column, Unicode, String
from sqlalchemy.orm import relationship as sa_relationship

from restfulpy.exceptions import ValidationError


# noinspection PyAbstractClass
class Field(Column):

    @property
    def can_validate(self):
        return 'pattern' in self.info or \
            'min_length' in self.info or \
            'max_length' in self.info

    def __init__(self,
                 *args,
                 json=None,
                 readonly=None,
                 max_length=None,
                 min_length=None,
                 pattern=None,
                 protected=None,
                 watermark=None,
                 **kwargs):
        info = dict()

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

        if min_length is not None:
            info['min_length'] = min_length

        if pattern is not None:
            info['pattern'] = pattern

        if args and isinstance(args[0], (Unicode, String)):
            info['max_length'] = args[0].length

        super(Field, self).__init__(*args, info=info, **kwargs)

    def _validate_pattern(self, value):
        if value is None:
            return
        if not re.match(self.info['pattern'], value):
            raise ValidationError(self.name, 'Cannot match "%s" with field acceptable pattern' % value)
        return value

    def _validate_length(self, value, min_length, max_length):
        if value is None:
            return

        if not isinstance(value, str):
            raise ValidationError(self.name, 'Invalid type: %s' % type(value))
        value_length = len(value)
        if min_length is not None:
            if value_length < min_length:
                raise ValidationError(self.name, 'Please enter at least %d characters.' % min_length)

        if max_length is not None:
            if value_length > max_length:
                raise ValidationError(self.name, 'Cannot enter more that : %d in this field.' % max_length)

    def validate(self, value):
        if 'pattern' in self.info:
            self._validate_pattern(value)

        if 'min_length' in self.info or 'max_length' in self.info:
            self._validate_length(value, self.info.get('min_length'), self.info.get('max_length'))
        return value

    @property
    def is_attachment(self):
        return 'attachment' in self.info


def relationship(*args, json=None, **kwargs):
    info = dict()
    if json is not None:
        info['json'] = json
    return sa_relationship(*args, info=info, **kwargs)
