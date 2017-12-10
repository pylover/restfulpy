import functools
import re
from itertools import chain

from nanohttp import context
from nanohttp.exceptions import HttpBadRequest


class FormValidator:
    def __init__(
            self,
            blacklist=None,
            exclude=None,
            filter_=None,
            whitelist=None,
            requires=None,
            exact=None,
            types=None,
            pattern=None,
            **rules_per_role
    ):
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

        if types:
            self.default_rules['types'] = types

        if pattern:
            self.default_rules['pattern'] = pattern

        self._rules_per_role = rules_per_role

    def extract_rulesets(self, rule_name, user_rules):
        return [ruleset[rule_name] for ruleset in ([self.default_rules] + user_rules) if rule_name in ruleset]

    def extract_rules_odd(self, rule_name, user_rules) -> set:
        return set(chain(
            *self.extract_rulesets(rule_name, user_rules)
        ))

    def extract_rules_pair(self, rule_name, user_rules) -> dict:
        rulesets = self.extract_rulesets(rule_name, user_rules)
        result = {}
        for r in rulesets:
            result.update(r)
        return result

    def __call__(self, *args, **kwargs):
        input_collections = [context.form, context.query_string]
        all_input_fields = set(chain(*input_collections))
        user_rules = [v for k, v in self._rules_per_role.items() if k in context.identity.roles] \
            if context.identity else []

        denied_fields = self.extract_rules_odd('blacklist', user_rules)
        if denied_fields:
            if all_input_fields & denied_fields:
                raise HttpBadRequest('These fields are denied: [%s]' % ', '.join(denied_fields))

        excluded_fields = self.extract_rules_odd('exclude', user_rules)
        if excluded_fields:
            for collection in input_collections:
                for field in set(collection) & excluded_fields:
                    del collection[field]

        filtered_fields = self.extract_rules_odd('filter_', user_rules)
        if filtered_fields:
            for collection in input_collections:
                for field in set(collection) - filtered_fields:
                    del collection[field]

        whitelist_fields = self.extract_rules_odd('whitelist', user_rules)
        if whitelist_fields:
            if all_input_fields - whitelist_fields:
                raise HttpBadRequest(
                    'These fields are not allowed: [%s]' % ', '.join(all_input_fields - whitelist_fields)
                )

        required_fields = self.extract_rules_odd('requires', user_rules)
        if required_fields:
            if required_fields - all_input_fields:
                raise HttpBadRequest('These fields are required: [%s]' % ', '.join(required_fields - all_input_fields))

        exact_fields = self.extract_rules_odd('exact', user_rules)
        if exact_fields:
            bad_fields = all_input_fields.symmetric_difference(exact_fields)
            if bad_fields:
                raise HttpBadRequest(
                    reason=';'.join([f'invalid-{f}' for f in bad_fields]),
                    info='Exactly these fields are allowed: [%s]' % ', '.join(exact_fields)
                )

        type_pairs = self.extract_rules_pair('types', user_rules)
        if type_pairs:
            type_keys = set(type_pairs.keys())
            for collection in input_collections:
                for field in set(collection) & type_keys:
                    desired_type = type_pairs[field]
                    try:
                        collection[field] = desired_type(collection[field])
                    except ValueError:
                        raise HttpBadRequest(
                            reason=f'invalid-{field}-type',
                            info='The field: %s must be %s' % (field, desired_type.__name__)
                        )

        pattern_pairs = self.extract_rules_pair('pattern', user_rules)
        if pattern_pairs:
            pattern_keys = set(pattern_pairs.keys())
            for collection in input_collections:
                for field in set(collection) & pattern_keys:
                    desired_pattern = pattern_pairs[field]
                    pattern = re.compile(desired_pattern) if isinstance(desired_pattern, str) else desired_pattern
                    if pattern.match(collection[field]) is None:
                        raise HttpBadRequest(
                            reason=f'invalid-{field}-format',
                            info='The field %s: %s must be matched with %s pattern' %
                            (field, collection[field], pattern.pattern)
                        )
        return args, kwargs


def validate_form(blacklist=None, exclude=None, filter_=None, whitelist=None, requires=None, exact=None, types=None,
                  pattern=None, **rules_per_role):
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
    :param types: A dictionary of fields and their expected types. Fields will be casted to expected types if possible.
                  Otherwise :class:`nanohttp.exceptions.HttpBadRequest` will be raised.
    :param pattern: A dictionary of fields and their expected regex patterns. Fields will be matched by expected pattern
                    if possible. Otherwise :class:`nanohttp.exceptions.HttpBadRequest` will be raised.

    :param rules_per_role: A dictionary ``{ role: { ... } }``, which you can apply above rules to single role.

    :return: A validation decorator.
    """

    def decorator(func):
        validator = FormValidator(blacklist=blacklist, exclude=exclude, filter_=filter_, whitelist=whitelist,
                                  requires=requires, exact=exact, types=types, pattern=pattern, **rules_per_role)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            args, kwargs = validator(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def prevent_form(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if context.form or context.query_string:
            raise HttpBadRequest('No input allowed.')
        return func(*args, **kwargs)

    return wrapper
