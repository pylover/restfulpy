import unittest
from datetime import datetime
from nanohttp import json, settings
from sqlalchemy import Unicode, Integer, DateTime

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class ModelValidationCheckingModel(DeclarativeBase):
    __tablename__ = 'model_validation_checking_model'

    id = Field(Integer, primary_key=True, readonly=True)
    title = Field(Unicode(50), unique=True, nullable=False, pattern='[A-Z][a-zA-Z]*')
    modified = Field(DateTime, default=datetime.now, readonly=True)


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = ModelValidationCheckingModel

    @ModelValidationCheckingModel.validate
    @json
    @commit
    def post(self):
        m = ModelValidationCheckingModel()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @ModelValidationCheckingModel.expose
    def get(self, title: str=None):
        query = ModelValidationCheckingModel.query
        if title:
            return query.filter(ModelValidationCheckingModel.title == title).one_or_none()
        return query


class ModelValidationDecoratorTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())
    __configuration__ = '''
    db:
      url: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)

    def test_model_validate_decorator(self):
        # Required
        self.request('ALL', 'POST', '/', params={}, expected_status=400)

        # Correct pattern
        resp, ___ = self.request('ALL', 'POST', '/', params=dict(title='Test'), doc=False)
        self.assertEqual(resp['title'], 'Test')

        # Invalid pattern
        self.request(
            'ALL', 'POST', '/',
            params=dict(title='startWithSmallCase'),
            expected_status=400,
            doc=False
        )

        # Readonly
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='Test',
                modified=datetime.now().isoformat()
            ),
            expected_status=400,
            doc=False
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
