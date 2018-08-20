from sqlalchemy import Integer, Unicode

from restfulpy.orm import DeclarativeBase, Field, FullTextSearchMixin, \
    fts_escape, to_tsvector


class FullTextSearchObject(FullTextSearchMixin, DeclarativeBase):
    __tablename__ = 'fulltext_search_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))

    __ts_vector__ = to_tsvector(
        title
    )


def test_fts_escape(db):
     result = fts_escape('&%!^$*[](){}\\')
     assert result == '\&\%\!\^\$\*\[\]\(\)\{\}\\\\'


def test_to_tsvector(db):
    result = to_tsvector('a', 'b', 'c')
    assert str(result) == 'to_tsvector(:to_tsvector_1, :to_tsvector_2)'


def test_activation_mixin(db):
    session = db()
    query = session.query(FullTextSearchObject)
    query = FullTextSearchObject.search('a', query)
    query_str = str(query)

    assert str(query) == \
        'SELECT fulltext_search_object.id AS fulltext_search_object_id, '\
        'fulltext_search_object.title AS fulltext_search_object_title \nFROM '\
        'fulltext_search_object \nWHERE to_tsvector(%(to_tsvector_1)s, '\
        'fulltext_search_object.title) @@ to_tsquery(%(to_tsvector_2)s)'

