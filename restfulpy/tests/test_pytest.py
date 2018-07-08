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

    _session = None
    _engine = None
    _sessions = []

    def configure(self, configuration):
        configure(configuration, force=True)
        settings.db.url = settings.db.test_url

    @classmethod
    def create_engine(cls):
        cls._engine = create_engine()
        cls._session = cls.connect()

    @classmethod
    def connect(cls, *args, **kw):
        session = session_factory(bind=cls._engine, *args, **kw)
        cls._sessions.append(session)
        return session

    @classmethod
    def close_all_connections(cls):
        cls._session.close()

        # Closing all sessions created by the test writer
        for s in cls._sessions:
            s.close()

        cls._engine.dispose()

    def drop_database(self):
        with DBManager() as m:
            m.drop_database()

    def create_database(self):
        with DBManager() as m:
            m.create_database()

    @classmethod
    def create_schema(cls):
        setup_schema(cls._session)
        cls._session.commit()


@pytest.fixture
def connect():
    builtin_configuration = '''
    db:
      test_url: postgresql://postgres:postgres@localhost/pytest_test
      administrative_url: postgresql://postgres:postgres@localhost/postgres
    logging:
      loggers:
        default:
          level: critical
    '''

    database_manager = DatabaseManager()
    database_manager.configure(builtin_configuration)


    # Drop the previosely created db if exists.
    database_manager.drop_database()

    database_manager.create_database()
    database_manager.create_engine()
    database_manager.create_schema()

    yield database_manager.connect

    database_manager.close_all_connections()
    database_manager.drop_database()


def test_db(connect):
    session = connect()
    assert session.query(Member).count() == 0

