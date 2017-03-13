

import re

from sqlalchemy import Column, Unicode, String
from sqlalchemy.orm import relationship as sa_relationship, composite as sa_composite
from nanohttp import HttpBadRequest


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
                 nullable=False,
                 label=None,
                 icon=None,
                 example=None,
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
        elif args and isinstance(args[0], (Unicode, String)):
            info['max_length'] = args[0].length

        if min_length is not None:
            info['min_length'] = min_length

        if pattern is not None:
            info['pattern'] = pattern

        if label is not None:
            info['label'] = label

        if icon is not None:
            info['icon'] = icon

        if example is not None:
            info['example'] = example

        super(Field, self).__init__(*args, info=info, nullable=nullable, **kwargs)

    def _validate_pattern(self, value):
        if value is None:
            return
        if not re.match(self.info['pattern'], value):
            raise HttpBadRequest('Cannot match field: %s with value "%s" by acceptable pattern' % (self.name, value))
        return value

    def _validate_length(self, value, min_length, max_length):
        if value is None:
            return

        if not isinstance(value, str):
            raise HttpBadRequest('Invalid type: %s for field: %s' % (type(value), self.name))

        value_length = len(value)
        if min_length is not None:
            if value_length < min_length:
                raise HttpBadRequest('Please enter at least %d characters for field: %s.' % (min_length, self.name))

        if max_length is not None:
            if value_length > max_length:
                raise HttpBadRequest('Cannot enter more that : %d in field: %s.' % (max_length, self.name))

    def validate(self, value):
        if 'pattern' in self.info:
            self._validate_pattern(value)

        if 'min_length' in self.info or 'max_length' in self.info:
            self._validate_length(value, self.info.get('min_length'), self.info.get('max_length'))
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

    if json:
        info['json'] = json

    if protected:
        info['protected'] = protected

    if readonly is not None:
        info['readonly'] = readonly

    return sa_composite(*args, info=info, **kwargs)
