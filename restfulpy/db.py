import os
from os.path import exists
from urllib.parse import urlparse

from nanohttp import settings
from sqlalchemy import create_engine


class AbstractDatabaseManager(object):

    def __init__(self):
        self.db_url = settings.db.url
        self.db_name = urlparse(self.db_url).path.lstrip('/')
        self.admin_url = settings.db.administrative_url
        self.admin_db_name = \
            urlparse(settings.db.administrative_url).path.lstrip('/')

    def __enter__(self):
        self.engine = create_engine(self.admin_url)
        self.connection = self.engine.connect()
        self.connection.execute('commit')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        self.engine.dispose()

    def create_database_if_not_exists(self):
        if not self.database_exists():
            self.create_database()

    def database_exists(self):  # pragma: no cover
        raise NotImplementedError()

    def create_database(self):  # pragma: no cover
        raise NotImplementedError()

    def drop_database(self):  # pragma: no cover
        raise NotImplementedError()


class PostgresManager(AbstractDatabaseManager):

    def __enter__(self):
        super().__enter__()
        self.connection.execute('commit')
        return self

    def database_exists(self):
        r = self.connection.execute(
            f'SELECT 1 FROM pg_database WHERE datname = \'{self.db_name}\''
        )
        try:
            ret = r.cursor.fetchall()
            return ret
        finally:
            r.cursor.close()

    def create_database(self):
        self.connection.execute(f'CREATE DATABASE {self.db_name}')
        self.connection.execute(f'COMMIT')

    def drop_database(self):
        self.connection.execute(f'DROP DATABASE IF EXISTS {self.db_name}')
        self.connection.execute(f'COMMIT')


class SqliteManager(AbstractDatabaseManager):

    def __init__(self):
        super().__init__()
        self.filename = self.db_url.replace('sqlite:///', '')

    def database_exists(self):
        return exists(self.filename)

    def create_database(self):
        if self.database_exists():
            raise RuntimeError(f'The file is already exists: {self.filename}')
        print(f'Creating: {self.filename}')
        open(self.filename, 'a').close()

    def drop_database(self):
        print('Removing: %s' % self.filename)
        os.remove(self.filename)


class DatabaseManager(AbstractDatabaseManager):

    def __new__(cls, *args, **kwargs):
        url = settings.db.url
        if url.startswith('sqlite'):
            manager_class = SqliteManager
        elif url.startswith('postgres'):
            manager_class = PostgresManager
        else:
            raise ValueError(f'Unsupported database url: {url}')

        return manager_class(*args, **kwargs)

