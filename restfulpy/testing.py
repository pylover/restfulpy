import os
import re
from os import path
import pytest
from bddrest import Given, when
from nanohttp import settings
import shutil

import restfulpy
from .mockup import MockupApplication
from .configuration import configure
from .db import DatabaseManager as DBManager
from .orm import setup_schema, session_factory, create_engine, init_model, \
    DBSession


LEGEND = '''

### Legend

#### Pagination

| Param  | Meaning            |
| ------ | ------------------ |
| take   | Rows per page      |
| skip   | Skip N rows        |

#### Search & Filtering

You can search and filter the result via query-string:

```
/path/to/resotrce?field=[op]value1[,value2]
```

| Operator  | Meaning | Example         |
| --------- | ------- | --------------- |
|           | =       | id=2            |
| !         | !=      | id=!2           |
| >         | >       | id=>2           |
| >=        | >=      | id=>=2          |
| <         | <       | id=<2           |
| <=        | <=      | id=<=2          |
| %         | LIKE    | title=u%s       |
| ~,%       | ILIKE   | title=~u%s      |
| IN()      | IN      | id=IN(2,3,4)    |
| !IN()     | NOT IN  | id=!IN(2,3,4)   |
| BETWEEN() | BETWEEN | id=BETWEEN(2,9) |

#### Sorting

You can sort like this:

```
/path/to/resource?sort=[op]value
```

| Operator  | Meaning |
| --------- | ------- |
|           | ASC     |
| \\-        | DESC    |

'''


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
    def _connect(*a, expire_on_commit=False, **kw):
        new_session = session_factory(
            bind=engine,
            *a,
            expire_on_commit=expire_on_commit,
            **kw
        )
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
    __application_factory__ = MockupApplication
    __controller_factory__ = None
    __configuration__ = None
    __story_directory__ = None
    __api_documentation_directory__ = None
    _engine = None
    _sessions = []
    _authentication_token = None
    __metadata__ = None

    @classmethod
    def configure_application(cls):
        cls.__application__.configure(force=True)
        settings.merge('''
          logging:
            loggers:
              default:
                level: critical
        ''')

        if cls.__configuration__:
            settings.merge(cls.__configuration__)

        # Overriding the db uri becase this is a test session, so db.test_uri
        # will be used instead of the db.uri
        settings.db.url = settings.db.test_url

    @classmethod
    def create_session(cls, *a, expire_on_commit=False, **kw):
        new_session = session_factory(
            bind=cls._engine,
            *a,
            expire_on_commit=expire_on_commit,
            **kw
        )
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
        while True:
            try:
                s = cls._sessions.pop()
                s.close()
            except IndexError:
                break

        DBSession.remove()
        if cls._engine is not None:
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
        try:
            cls.initialize_orm()
            cls.mockup()
        except:
            cls.teardown_class()
            raise

    @classmethod
    def teardown_class(cls):
        cls.cleanup_orm()
        cls.copy_legend()

    @classmethod
    def copy_legend(cls):
        if cls.__api_documentation_directory__ is None:
            return

        target_filename = path.join(
            cls.__api_documentation_directory__,
            f'LEGEND-restfulpy--v{restfulpy.__version__}.md',
        )
        if path.exists(target_filename):
            return

        with open(target_filename, 'w') as f:
            f.write(LEGEND)

    @classmethod
    def _ensure_directory(cls, d):
        if not path.exists(d):
            os.makedirs(d, exist_ok=True)

    @classmethod
    def _get_document_filename(cls, directory, story):
        cls._ensure_directory(directory)
        title = story.title.lower().replace(' ', '-')
        title = title.replace('/', '-or-')
        url_parts = story.base_call.url.split('/')
        if len(url_parts) >= 3:
            entity = url_parts[2]
        elif len(url_parts) == 2:
            entity = 'root'
        else:
            raise ValueError(
                'Url should be started with /apiv1/ following entity name'
            )

        filename = path.join(
            directory,
            f'{story.base_call.verb}-{entity}--{title}'
        )
        return filename

    @classmethod
    def _get_story_filename(cls, story):
        filename = cls._get_document_filename(cls.__story_directory__, story)
        return f'{filename}.yml'

    @classmethod
    def _get_markdown_filename(cls, story):
        filename = cls._get_document_filename(
            cls.__api_documentation_directory__,
            story
        )
        return f'{filename}.md'

    @classmethod
    def _get_field_info(cls, resource, verb, name):
        for k in cls.__metadata__:
            if re.match(k, resource):
                return cls.__metadata__[k].get(name)
        return None

    def given(self, *a, autodoc=True, **kw):
        if self._authentication_token is not None:
            kw.setdefault('authorization', self._authentication_token)

        if self.__story_directory__:
            kw['autodump'] = self._get_story_filename

        if autodoc and self.__api_documentation_directory__:
            kw['autodoc'] = self._get_markdown_filename

        if self.__metadata__:
            kw['fieldinfo'] = self._get_field_info

        return Given(self.__application__, *a, **kw)

    def when(self, *a, **kw):
        if self._authentication_token is not None:
            kw.setdefault('authorization', self._authentication_token)
        return when(*a, **kw)

    def login(self, form, url='/apiv1/sessions', verb='POST'):
        with self.given(
                None,
                url,
                verb,
                form=form
            ) as story:
            response = story.response
            assert response.status == '200 OK'
            assert 'token' in response.json
            self._authentication_token = response.json['token']

    def logout(self):
        self._authentication_token = None

