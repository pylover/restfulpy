import re

from nanohttp import HTTPBadRequest
from sqlalchemy import Column, Unicode, String
from sqlalchemy.orm import relationship as sa_relationship, \
    composite as sa_composite, synonym as sa_synonym


class Field(Column):

    @property
    def can_validate(self):
        return 'pattern' in self.info or \
            'min_length' in self.info or \
            'max_length' in self.info or \
            'max' in self.info or \
            'min' in self.info

    def __init__(
        self,
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
        **kwargs
    ):

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

        super(Field, self).__init__(
            *args,
            info=info,
            nullable=nullable,
            **kwargs
        )


def relationship(*args, json=None, protected=True, readonly=True, **kwargs):
    info = dict()

    if json is not None:
        info['json'] = json

    if protected is not None:
        info['protected'] = protected

    if readonly is not None:
        info['readonly'] = readonly

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



