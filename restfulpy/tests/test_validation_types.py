import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationTypesController(RestController):

    @json
    @validate_form(
        types={
            'typedParam1': float,
            'typedParam2': float,
            'typedParam3': float,
        },
        client={
           'types': {
               'typedParam1': int,
               'typedParam2': int
           }
        },
        admin={
           'types': {
               'typedParam1': complex,
               'typedParam4': complex
           }
        }
    )
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationTypesController()


class ValidationTypesTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())

    @classmethod
    def configure_app(cls):
        super().configure_app()
        settings.merge("""
            logging:
              loggers:
                default:
                  level: info
            """)

    def test_validation_types(self):
        # Test `type`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request(
            'All', 'POST', '/validation',
            doc=False,
            params={
                'typedParam1': '1',
                'typedParam2': '2',
                'typedParam3': '3',
                'typedParam4': '4'
            }
        )
        self.assertEqual(type(result['typedParam1']), float)
        self.assertEqual(type(result['typedParam2']), float)
        self.assertEqual(type(result['typedParam3']), float)
        self.assertEqual(type(result['typedParam4']), str)

        self.request(
            'All', 'POST', '/validation',
            doc=False,
            params={'typedParam1': 'not_convertible'},
            expected_status=400
        )

        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request(
            'Client', 'POST', '/validation',
            doc=False,
            params={
                'typedParam1': '1',
                'typedParam2': '2',
                'typedParam3': '3',
                'typedParam4': '4'
            }
        )
        self.assertEqual(type(result['typedParam1']), int)
        self.assertEqual(type(result['typedParam2']), int)
        self.assertEqual(type(result['typedParam3']), float)
        self.assertEqual(type(result['typedParam4']), str)

        self.request(
            'Client', 'POST', '/validation',
            doc=False,
            params={'typedParam1': 'not_convertible'},
            expected_status=400
        )

        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request(
            'Admin', 'POST', '/validation',
            doc=False,
            params={
                'typedParam1': '1',
                'typedParam2': '2',
                'typedParam3': '3',
                'typedParam4': '4'
            }
        )
        # type complex is dict
        self.assertEqual(type(result['typedParam1']), dict)
        self.assertEqual(type(result['typedParam2']), float)
        self.assertEqual(type(result['typedParam3']), float)
        self.assertEqual(type(result['typedParam4']), dict)

        self.request(
            'Admin', 'POST', '/validation',
            doc=False,
            params={'typedParam1': 'not_convertible'},
            expected_status=400
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
