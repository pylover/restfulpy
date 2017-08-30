import unittest

from nanohttp import json, settings

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import prevent_form
from restfulpy.controllers import RestController, RootController


class ValidationPreventFormController(RestController):
    @json
    @prevent_form
    def post(self):
        return dict()


class Root(RootController):
    validation = ValidationPreventFormController()


class ValidationPreventFormTestCase(WebAppTestCase):
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

    def test_validation_prevent_form(self):
        # Good
        self.request('All', 'POST', '/validation', doc=False)

        # Bad
        self.request(
            'All', 'POST', '/validation', doc=False,
            params={'param': 'param'},
            expected_status=400
        )
        self.request(
            'All', 'POST', '/validation', doc=False,
            query_string={'param': 'param'},
            expected_status=400
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
