import re

from nanohttp import HTTPBadRequest
from sqlalchemy import Column, Unicode, String
from sqlalchemy.orm import relationship as sa_relationship, \
    composite as sa_composite, synonym as sa_synonym


class Field(Column):

    def __init__(self, *args, json=None, readonly=None, max_length=None,
                 min_length=None, maximum=None, minimum=None, protected=None,
                 pattern=None, pattern_description=None, watermark=None,
                 not_none=None, nullable=False, required=None, label=None,
                 example=None, default=None, python_type=None, message=None,
                 **kwargs):

        info = {
            'json': json,
            'readonly': readonly,
            'protected': protected,
            'watermark': watermark,
            'message': message,
            'label': label,
            'min_length': min_length,
            'maximum': maximum,
            'minimum': minimum,
            'pattern': pattern,
            'pattern_description': pattern_description,
            'example': example,
            'not_none': not_none,
            'default': default,
            'type': python_type,
        }

        if max_length is None and args \
                and isinstance(args[0], (Unicode, String)):
            info['max_length'] = args[0].length
        else:
            info['max_length'] = max_length

        if required is not None:
            info['required'] = required

        if not_none:
            nullable = False

        super(Field, self).__init__(
            *args,
            info=info,
            nullable=nullable,
            default=default,
            **kwargs
        )


def relationship(*args, json=None, protected=True, readonly=True, **kwargs):
    info = {
        'json': json,
        'protected': protected,
        'readonly': readonly,
    }

    return sa_relationship(*args, info=info, **kwargs)


def composite(*args, json=None, protected=None, readonly=None, **kwargs):
    info = {
        'json': json,
        'protected': protected,
        'readonly': readonly,
    }

    return sa_composite(*args, info=info, **kwargs)


def synonym(*args, json=None, protected=None, readonly=None, **kwargs):
    info = {
        'json': json,
        'protected': protected,
        'readonly': readonly,
    }

    return sa_synonym(*args, info=info, **kwargs)

