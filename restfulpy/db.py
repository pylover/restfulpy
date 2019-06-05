import os
import contextlib
from os.path import exists
from urllib.parse import urlparse

import psycopg2
from nanohttp import settings
from sqlalchemy import create_engine


class PostgreSQLManager:
    connection = None

    def __init__(self, url=None):
        self.db_url = url or settings.db.url
        self.db_name = urlparse(self.db_url).path.lstrip('/')
        self.admin_url = settings.db.administrative_url
        self.admin_db_name = \
            urlparse(settings.db.administrative_url).path.lstrip('/')

    def __enter__(self):
        self.admin_engine = create_engine(self.admin_url)
        self.connection = self.admin_engine.connect()
        self.connection.execute('commit')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        self.admin_engine.dispose()

    def database_exists(self):
        r = self.connection.execute(
            f'SELECT 1 FROM pg_database WHERE datname = \'{self.db_name}\''
        )
        try:
            ret = r.cursor.fetchall()
            return ret
        finally:
            r.cursor.close()

    def create_database(self, exist_ok=False):
        if exist_ok and self.database_exists():
            return
        self.connection.execute(f'CREATE DATABASE {self.db_name}')
        self.connection.execute(f'COMMIT')

    def drop_database(self):
        self.connection.execute(f'DROP DATABASE IF EXISTS {self.db_name}')
        self.connection.execute(f'COMMIT')

    @contextlib.contextmanager
    def cursor(self, query=None, args=None):
        connection = psycopg2.connect(self.db_url)
        cursor = connection.cursor()
        if query:
            cursor.execute(query, args)

        yield cursor
        cursor.close()
        connection.close()

    def table_exists(self, name):
        with self.cursor(
            f'select to_regclass(%s)',
            (f'public.{name}',)
        ) as c:
            return c.fetchone()[0] is not None
