import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import settings

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, FullTextSearchMixin, fts_escape, to_tsvector


class FullTextSearchObject(FullTextSearchMixin, DeclarativeBase):
    __tablename__ = 'fulltext_search_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))

    __ts_vector__ = to_tsvector(
        title
    )


class FullTextSearchMixinTestCase(WebAppTestCase):
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

    def test_fts_escape(self):
        result = fts_escape('&%!^$*[](){}\\')
        self.assertEqual(result, '\&\%\!\^\$\*\[\]\(\)\{\}\\\\')

    def test_to_tsvector(self):
        result = to_tsvector('a', 'b', 'c')
        self.assertEqual(str(result), 'to_tsvector(:to_tsvector_1, :to_tsvector_2)')

    def test_activation_mixin(self):
        # noinspection PyArgumentList
        query = FullTextSearchObject.search('a')
        self.assertEqual(
            str(query).replace('\n', ' '),
            'SELECT fulltext_search_object.id AS fulltext_search_object_id, fulltext_search_object.title AS '
            'fulltext_search_object_title  FROM fulltext_search_object  WHERE to_tsvector(%(to_tsvector_1)s, '
            'fulltext_search_object.title) @@ to_tsquery(%(to_tsvector_2)s)'
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
