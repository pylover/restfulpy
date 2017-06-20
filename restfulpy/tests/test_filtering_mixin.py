import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import settings, HttpBadRequest
from nanohttp.contexts import Context

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, FilteringMixin


class FilteringObject(FilteringMixin, DeclarativeBase):
    __tablename__ = 'filtering_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class FilteringMixinTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', None)
    __configuration__ = '''
    db:
      uri: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)

    def test_filtering_mixin(self):
        for i in range(1, 6):
            # noinspection PyArgumentList
            obj = FilteringObject(
                title='object %s' % i,
            )
            DBSession.add(obj)
        DBSession.commit()

        # Bad Value
        with Context({'QUERY_STRING': 'id=1'}, self.application) as context:
            context.query_string['id'] = 1
            self.assertRaises(HttpBadRequest, FilteringObject.filter_by_request)

        # IN
        with Context({'QUERY_STRING': 'id=^1,2,3'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 3)

        # NOT IN
        with Context({'QUERY_STRING': 'id=!^1,2,3'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 2)

        # IN (error)
        with Context({'QUERY_STRING': 'id=^'}, self.application):
            self.assertRaises(HttpBadRequest, FilteringObject.filter_by_request)

        # Between
        with Context({'QUERY_STRING': 'id=~1,3'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 3)

        # IS NULL
        with Context({'QUERY_STRING': 'title=null'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 0)

        # IS NOT NULL
        with Context({'QUERY_STRING': 'title=!null'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 5)

        # LIKE
        with Context({'QUERY_STRING': 'title=%obj'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 5)

        with Context({'QUERY_STRING': 'title=%OBJ'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 0)

        # ILIKE
        with Context({'QUERY_STRING': 'title=%~obj'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 5)

        with Context({'QUERY_STRING': 'title=%~OBJ'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 5)

        # ==
        with Context({'QUERY_STRING': 'id=1'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 1)

        # !=
        with Context({'QUERY_STRING': 'id=!1'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 4)

        # >=
        with Context({'QUERY_STRING': 'id=>=2'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 4)

        # >
        with Context({'QUERY_STRING': 'id=>2'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 3)

        # <=
        with Context({'QUERY_STRING': 'id=<=3'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 3)

        # <
        with Context({'QUERY_STRING': 'id=<3'}, self.application):
            self.assertEqual(FilteringObject.filter_by_request().count(), 2)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
