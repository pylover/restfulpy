
import functools
from os.path import exists

from nanohttp import settings, context
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.ext.declarative import declarative_base
from alembic import config, command

from .field import Field, relationship, composite, synonym
from .metadata import MetadataField
from .mixins import ModifiedMixin, SoftDeleteMixin, TimestampMixin, \
    ActivationMixin, PaginationMixin, FilteringMixin, OrderingMixin, \
    ApproveRequiredMixin, FullTextSearchMixin, AutoActivationMixin, \
    DeactivationMixin
from .models import BaseModel
from .fulltext_search import to_tsvector, fts_escape
from .types import FakeJson

# Global session manager: DBSession() returns the Thread-local
# session object appropriate for the current web request.
session_factory = sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=True,
    twophase=False)

DBSession = scoped_session(session_factory)

# Global metadata.
metadata = MetaData()

DeclarativeBase = declarative_base(cls=BaseModel, metadata=metadata)


def create_engine(url=None, echo=None):
    return sa_create_engine(url or settings.db.url, echo=echo or settings.db.echo)


def init_model(engine):
    """
    Call me before using any of the tables or classes in the model.
    :param engine: SqlAlchemy engine to bind the session
    :return:
    """
    DBSession.remove()
    DBSession.configure(bind=engine)


def drop_all(session=None):  # pragma: no cover
    session = session or DBSession
    engine = session.bind
    metadata.drop_all(bind=engine)


def setup_schema(session=None):  # pragma: no cover
    session = session or DBSession
    engine = session.bind
    metadata.create_all(bind=engine)

    if hasattr(settings, 'migration') and exists(settings.migration.directory):
        alembic_cfg = config.Config()
        alembic_cfg.set_main_option("script_location", settings.migration.directory)
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
        alembic_cfg.config_file_name = settings.migration.ini
        command.stamp(alembic_cfg, "head")


def create_thread_unsafe_session():  # pragma: no cover
    return session_factory()


def commit(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        if hasattr(context, 'jsonpatch'):
            return func(*args, **kwargs)

        try:
            result = func(*args, **kwargs)
            DBSession.commit()
            return result
        except:
            if DBSession.is_active:
                DBSession.rollback()
            raise

    return wrapper
