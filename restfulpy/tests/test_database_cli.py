from bddcli import Given, stderr, Application, when, given
from nanohttp import settings
from sqlalchemy import Integer, Unicode

from restfulpy import Application as RestfulpyApplication
from restfulpy.db import DatabaseManager as DBManager
from restfulpy.orm import DeclarativeBase, Field, session_factory, \
    create_engine, metadata


BASEDATA_TITLE = 'foo as basedata'
MOCKUP_TITLE = 'foo as mockup'


class SessionManager:

    def __init__(self):
        self.engine = create_engine(settings.db.url)
        self.session = self.create_session(expire_on_commit=True)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        self.engine.dispose()

    def create_session(self, *a, expire_on_commit=False, **kw):
            new_session = session_factory(
                bind=self.engine,
                *a,
                expire_on_commit=expire_on_commit,
                **kw
            )
            return new_session


class FooModel(DeclarativeBase):
    __tablename__ = 'foo_model'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class FooApplication(RestfulpyApplication):
    __configuration__ = '''
      db:
        url: postgresql://postgres:postgres@localhost/foo_test
        administrative_url: postgresql://postgres:postgres@localhost/postgres
    '''

    def insert_basedata(self, *args):
        with SessionManager() as session:
            basedata_foo = FooModel(title=BASEDATA_TITLE)
            session.add(basedata_foo)
            session.commit()

    def insert_mockup(self, *args):
        with SessionManager() as session:
            mockup_foo = FooModel(title=MOCKUP_TITLE)
            session.add(mockup_foo)
            session.commit()


foo = FooApplication(name='database')


def foo_main():
    return foo.cli_main()


app = Application(
    'foo',
    'restfulpy.tests.test_database_cli:foo_main'
)


class DBTestCase:

    _engine = None
    _connection = None

    @classmethod
    def setup_class(cls):
        foo.configure(force=True)
        cls.tablename = FooModel.__tablename__
        cls.db_url, cls.db_name = settings.db.url.rsplit('/', 1)
        cls._engine = create_engine(cls.db_url)
        cls._connection = cls._engine.connect()

        with DBManager(url=settings.db.url) as m:
            m.drop_database()
            m.create_database()

    @classmethod
    def teardown_class(cls):
        cls.close_connections()
        with DBManager(url=settings.db.url) as m:
            m.drop_database()

    @classmethod
    def close_connections(cls):
        cls._connection.close()
        cls._engine.dispose()

    @classmethod
    def map_tables(cls):
        with SessionManager() as session:
            metadata.create_all(bind=session.bind)

    @property
    def is_database_exists(self):
        r = self._connection.execute(
            f'SELECT 1 FROM pg_database WHERE datname = \'{self.db_name}\''
        )
        try:
            ret = r.cursor.fetchall()
            return True if ret else False
        finally:
            r.cursor.close()

    @property
    def is_table_exists(self):
        engine = create_engine(settings.db.url)
        result = engine.dialect.has_table(engine, self.tablename)
        engine.dispose()
        return result


class TestDatabaseCreation(DBTestCase):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        with DBManager(url=settings.db.url) as m:
            m.drop_database()

    def test_database_create(self):

        with Given(app, ['db', 'create']), SessionManager() as session:
            assert stderr == ''
            assert self.is_database_exists == True

            when(given + '--drop --schema --mockup --basedata')
            assert stderr == ''
            assert self.is_database_exists == True
            assert self.is_table_exists == True

            assert session.query(FooModel) \
                .filter(FooModel.title == BASEDATA_TITLE) \
                .one()
            assert session.query(FooModel) \
                .filter(FooModel.title == MOCKUP_TITLE) \
                .one()


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


if __name__ == '__main__': # pragma: no cover
    foo.cli_main(['db', 'create'])

