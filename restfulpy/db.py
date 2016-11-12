
from urllib.parse import urlparse

from sqlalchemy import create_engine
from nanohttp import settings


class DatabaseManager(object):

    def __init__(self):

        self.db_uri = settings.db.uri
        self.db_name = urlparse(self.db_uri).path.lstrip('/')
        self.admin_uri = settings.db.administrative_uri
        self.admin_db_name = urlparse(settings.db.administrative_uri).path.lstrip('/')
        if self.db_uri.startswith('sqlite'):
            raise NotImplementedError("Sqlite database management is not supported yet.")

    def __enter__(self):
        self.engine = create_engine(self.admin_uri)
        self.connection = self.engine.connect()
        self.connection.execute('commit')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        self.engine.dispose()

    def exists_database(self):
        r = self.connection.execute('SELECT 1 FROM pg_database WHERE datname = \'%s\'' % self.db_name)
        try:
            ret = r.cursor.fetchall()
            return ret
        finally:
            r.cursor.close()

    def create_database(self):
        self.connection.execute('CREATE DATABASE %s' % self.db_name)
        self.connection.execute('commit')

    def create_database_if_not_exists(self):
        if not self.exists_database():
            self.create_database()

    def drop_database(self):
        self.connection.execute('DROP DATABASE IF EXISTS %s' % self.db_name)
        self.connection.execute('commit')
