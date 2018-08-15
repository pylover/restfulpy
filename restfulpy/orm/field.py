import re

from nanohttp import HTTPBadRequest
from sqlalchemy import Column, Unicode, String
from sqlalchemy.orm import relationship as sa_relationship, \
    composite as sa_composite, synonym as sa_synonym


class Field(Column):

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
        example=None,
        **kwargs
    ):

        info = {}

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

        if example is not None:
            info['example'] = example

        if not_none is not None:
            nullable = False if isinstance(not_none
        if not nullable:
            info['not_none'] = True

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



