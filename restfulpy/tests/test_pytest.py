import pytest

from sqlalchemy import Integer, String
from nanohttp import settings, contexts
from restfulpy import Application
from restfulpy.configuration import configure
from restfulpy.db import DatabaseManager as DBManager
from restfulpy.orm import setup_schema, session_factory, create_engine,\
    DeclarativeBase, Field, DBSession


class Member(DeclarativeBase):
    __tablename__ = 'members'

    id = Field(Integer, primary_key=True, autoincrement=True)
    username = Field(String(50))


class DatabaseManager:

    session = None
    engine = None

    def __init__(self, configuration):
        self.configure(configuration)

    def configure(self, configuration):
        configure(configuration, force=True)
        settings.db.url = settings.db.test_url

    @classmethod
    def connect(cls) -> 'Session':
        cls.engine = create_engine()
        cls.session = session =session_factory(
            bind=cls.engine,
            expire_on_commit=False
        )

    @classmethod
    def close_all_connections(cls):
        cls.session.close_all()
        cls.engine.dispose()

    def drop_database(self):
        with DBManager() as m:
            m.drop_database()

    def create_database(self):
        with DBManager() as m:
            m.create_database()

    @classmethod
    def create_schema(cls):
        setup_schema(cls.session)
        cls.session.commit()


@pytest.fixture
def db():

    print('Setup')

    builtin_configuration = '''
    db:
      test_url: postgresql://postgres:postgres@localhost/pytest_test
      administrative_url: postgresql://postgres:postgres@localhost/postgres
    logging:
      loggers:
        default:
          level: critical
    '''

    # configure
    database_manager = DatabaseManager(builtin_configuration)

    # drop
    database_manager.drop_database()

    # create
    database_manager.create_database()

    # connect
    database_manager.connect()

    # schema
    database_manager.create_schema()

    #tear dwon
    yield database_manager
    print('Tear down')

    # close all connections
    database_manager.close_all_connections()

    # Drop Db
    database_manager.drop_database()


def test_db(db):

    assert db.session.query(Member).count() == 0

