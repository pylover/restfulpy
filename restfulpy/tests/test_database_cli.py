from bddcli import Given, stderr, Application, when, given
from nanohttp import settings
from sqlalchemy import Integer, Unicode

from restfulpy import Application as RestfulpyApplication
from restfulpy.db import PostgreSQLManager as DBManager
from restfulpy.orm import DeclarativeBase, Field, session_factory, \
    create_engine, metadata, DBSession


DBURL = 'postgresql://postgres:postgres@localhost/foo_test'


class FooModel(DeclarativeBase):
    __tablename__ = 'foo_model'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class FooApplication(RestfulpyApplication):
    __configuration__ = f'''
      db:
        url: {DBURL}
    '''

    def insert_basedata(self, *args):
        DBSession.add(FooModel(title='FooBase'))
        DBSession.commit()

    def insert_mockup(self, *args):
        DBSession.add(FooModel(title='FooMock'))
        DBSession.commit()


foo = FooApplication(name='Foo')


def foo_main():
    return foo.cli_main()


app = Application(
    'foo',
    'restfulpy.tests.test_database_cli:foo_main'
)



class TestDatabaseAdministrationCommandLine:
    db = None

    @classmethod
    def setup_class(cls):
        foo.configure(force=True)
        settings.db.url = settings.db.test_url
        cls.db = DBManager(DBURL)
        cls.db.__enter__()

    @classmethod
    def teardown_class(cls):
        cls.db.__exit__(None, None, None)

    def test_database_create(self):

        self.db.drop_database()
        assert not self.db.database_exists()

        with Given(app, ['db', 'create']):
            assert stderr == ''
            assert self.db.database_exists()
            assert not self.db.table_exists(FooModel.__tablename__)

            when(given + '--drop --schema')
            assert stderr == ''
            assert self.db.database_exists()
            assert self.db.table_exists(FooModel.__tablename__)

            when(given + '--drop --mockup')
            assert stderr == ''
            with self.db.cursor(
                f'SELECT count(*) FROM foo_model WHERE title = %s',
                ('FooMock', )
            ) as c:
                assert c.fetchone()[0] == 1

            when(given + '--drop --basedata')
            assert stderr == ''
            with self.db.cursor(
                f'SELECT count(*) FROM foo_model WHERE title = %s',
                ('FooBase', )
            ) as c:
                assert c.fetchone()[0] == 1

"""
class TestDatabaseDrop(DBTestCase):

    def test_database_drop(self):

        with Given(app, ['db', 'drop']):
            assert stderr == ''
            assert self.is_database_exists == False


class TestDatabaseSchema(DBTestCase):

    def test_database_schema(self):

        with Given(app, ['db', 'schema']):
            assert stderr == ''
            assert self.is_database_exists == True
            assert self.is_table_exists == True


class TestDatabaseBasedata(DBTestCase):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.map_tables()

    def test_database_basedata(self):

        with Given(app, ['db', 'basedata']), SessionManager() as session:
            assert stderr == ''
            assert self.is_database_exists == True
            assert self.is_table_exists == True

            assert session.query(FooModel) \
                .filter(FooModel.title == BASEDATA_TITLE) \
                .one()


class TestDatabaseMockup(DBTestCase):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.map_tables()

    def test_database_mockup(self):

        with Given(app, ['db', 'mockup']), SessionManager() as session:
            assert stderr == ''
            assert self.is_database_exists == True
            assert self.is_table_exists == True

            assert session.query(FooModel) \
                .filter(FooModel.title == MOCKUP_TITLE) \
                .one()

"""

if __name__ == '__main__': # pragma: no cover
    foo.cli_main(['db', 'create'])
