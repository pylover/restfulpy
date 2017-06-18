import functools
from itertools import chain

from nanohttp import context
from nanohttp.exceptions import HttpBadRequest


class FormValidator:

    def __init__(self, deny=None, exclude=None, filter_=None, only=None, **rules_per_role):
        self.default_rules = {}
        if deny:
            self.default_rules['deny'] = set(deny)

        if exclude:
            self.default_rules['exclude'] = set(exclude)

        if filter_:
            self.default_rules['filter_'] = set(filter_)

        if only:
            self.default_rules['only'] = set(only)

        self._rules_per_role = rules_per_role

    def extract_rule_fields(self, rule_name, user_rules):
        return set(chain(
            *[ruleset[rule_name] for ruleset in ([self.default_rules] + user_rules) if rule_name in ruleset]
        ))

    def __call__(self, *args, **kwargs):
        input_collections = [context.form, context.query_string]
        all_input_fields = set(chain(*input_collections))
        user_rules = [v for k, v in self._rules_per_role.items() if k in context.identity.roles] \
            if context.identity else []

        denied_fields = self.extract_rule_fields('deny', user_rules)
        if denied_fields:
            if all_input_fields & denied_fields:
                raise HttpBadRequest('These fields are denied: [%s]' % ', '.join(denied_fields))

        excluded_fields = self.extract_rule_fields('exclude', user_rules)
        if excluded_fields:
            for collection in input_collections:
                for field in set(collection) & excluded_fields:
                    del collection[field]

        filtered_fields = self.extract_rule_fields('filter_', user_rules)
        if filtered_fields:
            for collection in input_collections:
                for field in set(collection) - filtered_fields:
                    del collection[field]

        only_fields = self.extract_rule_fields('only', user_rules)
        if only_fields:
            if only_fields != all_input_fields:
                raise HttpBadRequest('Only these fields are allowed: [%s]' % ', '.join(only_fields))

        return args, kwargs


def validate_form(deny=None, exclude=None, filter_=None, only=None, **rules_per_role):
    """Creates a validation decorator based on given rules:

    :param deny: A list fields to raise :class:`nanohttp.exceptions.HttpBadRequest` if exists in request.
    :param exclude: A list of fields to remove from the request payload if exists.
    :param filter_: A list of fields to filter the request payload.
    :param only: A list of fields to raise :class:`nanohttp.exceptions.HttpBadRequest` if the given fields are not
                 exact match.
    :param rules_per_role: A dictionary ``{ role: { ... } }``, which you can apply above rules to single role.

    :return: A validation decorator.
    """
    def decorator(func):
        validator = FormValidator(deny=deny, exclude=exclude, filter_=filter_, only=only, **rules_per_role)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args, kwargs = validator(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator
