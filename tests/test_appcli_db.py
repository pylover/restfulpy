from bddcli import Given, stderr, Application, when, given, status
from nanohttp import settings
from sqlalchemy import Integer, Unicode

from restfulpy import Application as RestfulpyApplication
from restfulpy.db import PostgreSQLManager as DBManager
from restfulpy.orm import DeclarativeBase, Field, DBSession


DBURL = 'postgresql://postgres:postgres@localhost/restfulpy_test'


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
    'tests.test_appcli_db:foo_main'
)



class TestDatabaseAdministrationCommandLine:
    db = None

    @classmethod
    def setup_class(cls):
        foo.configure(force=True)
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
            assert status == 0
            assert self.db.database_exists()
            assert not self.db.table_exists(FooModel.__tablename__)

            when(given + '--drop --schema')
            assert stderr == ''
            assert status == 0
            assert self.db.database_exists()
            assert self.db.table_exists(FooModel.__tablename__)

            when(given + '--drop --mockup')
            assert stderr == ''
            assert status == 0
            with self.db.cursor(
                f'SELECT count(*) FROM foo_model WHERE title = %s',
                ('FooMock', )
            ) as c:
                assert c.fetchone()[0] == 1

            when(given + '--drop --basedata')
            assert stderr == ''
            assert status == 0
            with self.db.cursor(
                f'SELECT count(*) FROM foo_model WHERE title = %s',
                ('FooBase', )
            ) as c:
                assert c.fetchone()[0] == 1

    def test_database_drop(self):

        self.db.create_database(exist_ok=True)
        assert self.db.database_exists()

        with Given(app, ['db', 'drop']):
            assert stderr == ''
            assert status == 0
            assert not self.db.database_exists()

    def test_database_schema_basedata_mockup(self):

        self.db.drop_database()
        self.db.create_database()
        assert self.db.database_exists()

        with Given(app, ['db', 'schema']):
            assert stderr == ''
            assert status == 0
            assert self.db.table_exists(FooModel.__tablename__)

            when(['db', 'basedata'])
            assert stderr == ''
            assert status == 0
            with self.db.cursor(
                f'SELECT count(*) FROM foo_model WHERE title = %s',
                ('FooBase', )
            ) as c:
                assert c.fetchone()[0] == 1

            when(['db', 'mockup'])
            assert stderr == ''
            assert status == 0
            with self.db.cursor(
                f'SELECT count(*) FROM foo_model WHERE title = %s',
                ('FooMock', )
            ) as c:
                assert c.fetchone()[0] == 1


if __name__ == '__main__': # pragma: no cover
    # Use for debugging
    foo.cli_main(['db', 'create'])
