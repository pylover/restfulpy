
import unittest

from restfulpy.orm.fulltext_search import fts_escape, to_tsvector


class FulltextSearchTestCase(unittest.TestCase):

    def test_fts_escape(self):
        result = fts_escape('&%!^$*[](){}\\')
        self.assertEquals(result, '\&\%\!\^\$\*\[\]\(\)\{\}\\\\')

    def test_to_tsvector(self):
        result = to_tsvector('a', 'b', 'c')
        self.assertEquals(str(result), 'to_tsvector(:to_tsvector_1, :to_tsvector_2)')


if __name__ == '__main__':
    unittest.main()
