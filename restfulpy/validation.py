import functools

from nanohttp import context
from nanohttp.exceptions import HttpBadRequest


def validate_form(deny=None, exclude=None, filter=None, only=None, **rules_per_role):
    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            def _deny(_fields):
                """
                Raise HttpBadRequest if _fields has overlap with inputs.
                :param _fields:
                :return:
                """
                for field in _fields:
                    for env in [context.form, context.query_string]:
                        if env.get(field, None):
                            raise HttpBadRequest('%s-denied' % field)

            def _exclude(_fields):
                """
                Exclude which parameter not in _fields.
                :param _fields:
                :return:
                """
                for field in _fields:
                    for env in [context.form, context.query_string]:
                        if env.get(field, None):
                            del env[field]

            def _filter(_fields):
                """
                Exclude all parameters unless which are in _fields.
                :param _fields:
                :return:
                """
                for env in [context.form, context.query_string]:
                    for _key in list(env):
                        if _key not in _fields:
                            del env[_key]

            def _only(_fields):
                """
                Raise HttpBadRequest if any parameter is in input and not in _fields.
                :param _fields:
                :return:
                """
                for field in _fields:
                    if not any(env.get(field, None) for env in [context.form, context.query_string]):
                        raise HttpBadRequest('%s-denied' % field)
                for env in [context.form, context.query_string]:
                    for _input in list(env):
                        if _input not in _fields:
                            raise HttpBadRequest('bad-%s' % _input)

            effective_rules = dict(role=[])
            for action, _fields in [('deny', deny), ('exclude', exclude), ('filter', filter),
                                    ('only', only)]:
                if _fields:
                    effective_rules[action] = _fields[:]

            for role, rule in rules_per_role.items():
                if context.identity.is_in_roles(role):
                    for key, parameters in rule.items():
                        if not effective_rules[key]:
                            effective_rules[key] = []
                        effective_rules[key].extend(
                            [param for param in parameters if param not in effective_rules[key]])
            effective_rules.pop('role')

            for action, fields in effective_rules.items():
                if fields:
                    locals()[''.join(['_', action])](fields)

            return func(*args, **kwargs)

        return wrapper

    return decorator
