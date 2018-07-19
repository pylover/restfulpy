import pytest
from bddrest import Given, when
from nanohttp import settings

from .application import Application
from .configuration import configure
from .db import DatabaseManager as DBManager
from .orm import setup_schema, session_factory, create_engine, init_model, \
    DBSession


@pytest.fixture(scope='module')
def db():
    builtin_configuration = '''
    db:
      test_url: postgresql://postgres:postgres@localhost/pytest_test
      administrative_url: postgresql://postgres:postgres@localhost/postgres
    logging:
      loggers:
        default:
          level: warning
    '''
    configure(builtin_configuration, force=True)

    # Overriding the db uri becase this is a test session, so db.test_uri will
    # be used instead of the db.uri
    settings.db.url = settings.db.test_url

    # Drop the previosely created db if exists.
    with DBManager() as m:
        m.drop_database()
        m.create_database()

    # An engine to create db schema and bind future created sessions
    engine = create_engine()

    # A session factory to create and store session to close it on tear down
    sessions = []
    def _connect(*a, **kw):
        new_session = session_factory(bind=engine, *a, **kw)
        sessions.append(new_session)
        return new_session

    session = _connect(expire_on_commit=True)

    # Creating database objects
    setup_schema(session)
    session.commit()

    # Closing the session to free the connection for future sessions.
    session.close()

    # Preparing and binding the application shared scoped session, due the
    # some errors when a model trying use the mentioned session internally.
    init_model(engine)

    yield _connect

    # Closing all sessions created by the test writer
    for s in sessions:
        s.close()
    DBSession.close_all()
    engine.dispose()

    # Dropping the previously created database
    with DBManager() as m:
        m.drop_database()


class TestCase:
    pass


class ApplicableTestCase:
    __application__ = None
    __application_factory__ = Application
    __controller_factory__ = None
    __configuration__ = None
    _engine = None
    _sessions = []
    _authentication_token = None

    @classmethod
    def configure_application(cls):
        cls.__application__.configure(force=True)
        settings.merge('''
            db:
              test_url: postgresql://postgres:postgres@localhost/pytest_test
              administrative_url: >
                       postgresql://postgres:postgres@localhost/postgres
            logging:
              loggers:
                default:
                  level: critical
        ''')

        # Overriding the db uri becase this is a test session, so db.test_uri
        # will be used instead of the db.uri
        settings.db.url = settings.db.test_url

        if cls.__configuration__:
            settings.merge(cls.__configuration__)

    @classmethod
    def create_session(cls, *a, **kw):
        new_session = session_factory(bind=cls._engine, *a, **kw)
        cls._sessions.append(new_session)
        return new_session

    @classmethod
    def initialize_orm(cls):
        # Drop the previosely created db if exists.
        with DBManager() as m:
            m.drop_database()
            m.create_database()

        # An engine to create db schema and bind future created sessions
        cls._engine = create_engine()

        # A session factory to create and store session
        # to close it on tear down
        session = cls.create_session(expire_on_commit=True)

        # Creating database objects
        setup_schema(session)
        session.commit()

        # Closing the session to free the connection for future sessions.
        session.close()

        cls.__application__.initialize_orm(cls._engine)

    @classmethod
    def mockup(cls):
        """This is a template method so this is optional to override and you
        haven't call the super when overriding it, because there isn't any.
        """
        pass

    @classmethod
    def cleanup_orm(cls):
        # Closing all sessions created by the test writer
        for s in cls._sessions:
            s.close()
            cls._sessions.remove(s)

        DBSession.remove()
        cls._engine.dispose()

        # Dropping the previousely created database
        with DBManager() as m:
            m.drop_database()

    @classmethod
    def setup_class(cls):
        if cls.__application__ is None:
            parameters = {}
            if cls.__controller_factory__ is not None:
                parameters['root'] = cls.__controller_factory__()

            cls.__application__ = cls.__application_factory__(
                'Restfulpy testing application',
                **parameters,
            )

        cls.configure_application()
        cls.initialize_orm()
        cls.mockup()

    @classmethod
    def teardown_class(cls):
        cls.cleanup_orm()

    def given(self, *a, **kw):
        if self._authentication_token is not None:
            kw.setdefault('authorization', self._authentication_token)
        return Given(self.__application__, *a, **kw)

    def when(self, *a, **kw):
        if self._authentication_token is not None:
            kw.setdefault('authorization', self._authentication_token)
        return when(*a, **kw)

    def login(self, email, password, url='/apiv1/sessions', verb='POST'):
        with self.given(
                None,
                url,
                verb,
                form=dict(email=email, password=password)
            ) as story:
            response = story.response
            assert response.status == '200 OK'
            assert response.headers['X-Identity'] == '1'
            assert 'token' in response.json
            self._authentication_token = response.json['token']

    def logout(self):
        self._authentication_token = None

