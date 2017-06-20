import functools
from itertools import chain

from nanohttp import context
from nanohttp.exceptions import HttpBadRequest


class FormValidator:
    def __init__(self, blacklist=None, exclude=None, filter_=None, whitelist=None, requires=None, exact=None,
                 **rules_per_role):
        self.default_rules = {}
        if blacklist:
            self.default_rules['blacklist'] = set(blacklist)

        if exclude:
            self.default_rules['exclude'] = set(exclude)

        if filter_:
            self.default_rules['filter_'] = set(filter_)

        if whitelist:
            self.default_rules['whitelist'] = set(whitelist)

        if requires:
            self.default_rules['requires'] = set(requires)

        if exact:
            self.default_rules['exact'] = set(exact)

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

        denied_fields = self.extract_rule_fields('blacklist', user_rules)
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

        whitelist_fields = self.extract_rule_fields('whitelist', user_rules)
        if whitelist_fields:
            if all_input_fields - whitelist_fields:
                raise HttpBadRequest(
                    'These fields are not allowed: [%s]' % ', '.join(all_input_fields - whitelist_fields)
                )

        required_fields = self.extract_rule_fields('requires', user_rules)
        if required_fields:
            if required_fields - all_input_fields:
                raise HttpBadRequest('These fields are required: [%s]' % ', '.join(required_fields - all_input_fields))

        exact_fields = self.extract_rule_fields('exact', user_rules)
        if exact_fields:
            if exact_fields != all_input_fields:
                raise HttpBadRequest('Exactly these fields are allowed: [%s]' % ', '.join(whitelist_fields))

        return args, kwargs


def validate_form(blacklist=None, exclude=None, filter_=None, whitelist=None, requires=None, exact=None,
                  **rules_per_role):
    """Creates a validation decorator based on given rules:

    :param blacklist: A list fields to raise :class:`nanohttp.exceptions.HttpBadRequest` if exists in request.
    :param exclude: A list of fields to remove from the request payload if exists.
    :param filter_: A list of fields to filter the request payload.
    :param whitelist: A list of fields to raise :class:`nanohttp.exceptions.HttpBadRequest` if anythings else found in
                the request payload.
    :param requires: A list of fields to raise :class:`nanohttp.exceptions.HttpBadRequest` if the given fields are not
                 in the request payload.
    :param exact: A list of fields to raise :class:`nanohttp.exceptions.HttpBadRequest` if the given fields are not
                 exact match.
    :param rules_per_role: A dictionary ``{ role: { ... } }``, which you can apply above rules to single role.

    :return: A validation decorator.
    """

    def decorator(func):
        validator = FormValidator(blacklist=blacklist, exclude=exclude, filter_=filter_, whitelist=whitelist,
                                  requires=requires, exact=exact, **rules_per_role)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args, kwargs = validator(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator
