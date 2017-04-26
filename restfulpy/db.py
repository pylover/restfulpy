
import os
from os.path import exists
from urllib.parse import urlparse

from sqlalchemy import create_engine
from nanohttp import settings


class AbstractDatabaseManager(object):

    def __init__(self):
        self.db_uri = settings.db.uri
        self.db_name = urlparse(self.db_uri).path.lstrip('/')
        self.admin_uri = settings.db.administrative_uri
        self.admin_db_name = urlparse(settings.db.administrative_uri).path.lstrip('/')

    def __enter__(self):
        self.engine = create_engine(self.admin_uri)
        self.connection = self.engine.connect()
        self.connection.execute('commit')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        self.engine.dispose()

    def create_database_if_not_exists(self):
        if not self.database_exists():
            self.create_database()

    def database_exists(self):
        raise NotImplementedError()

    def create_database(self):
        raise NotImplementedError()

    def drop_database(self):
        raise NotImplementedError()


class PostgresManager(AbstractDatabaseManager):

    def __enter__(self):
        super().__enter__()
        self.connection.execute('commit')
        return self

    def database_exists(self):
        r = self.connection.execute('SELECT 1 FROM pg_database WHERE datname = \'%s\'' % self.db_name)
        try:
            ret = r.cursor.fetchall()
            return ret
        finally:
            r.cursor.close()

    def create_database(self):
        self.connection.execute('CREATE DATABASE %s' % self.db_name)
        self.connection.execute('commit')

    def drop_database(self):
        self.connection.execute('DROP DATABASE IF EXISTS %s' % self.db_name)
        self.connection.execute('commit')


class SqliteManager(AbstractDatabaseManager):

    def __init__(self):
        super().__init__()
        self.filename = self.db_uri.replace('sqlite:///', '')

    def database_exists(self):
        return exists(self.filename)

    def create_database(self):
        if self.database_exists():
            raise RuntimeError('The file is already exists: %s' % self.filename)
        print('Creating: %s' % self.filename)
        open(self.filename, 'a').close()

    def drop_database(self):
        print('Removing: %s' % self.filename)
        os.remove(self.filename)


# noinspection PyAbstractClass
class DatabaseManager(AbstractDatabaseManager):

    def __new__(cls, *args, **kwargs):
        uri = settings.db.uri
        if uri.startswith('sqlite'):
            manager_class = SqliteManager
        elif uri.startswith('postgres'):
            manager_class = PostgresManager
        else:
            raise ValueError('Unsupported database uri: %s' % uri)

        return manager_class(*args, **kwargs)
