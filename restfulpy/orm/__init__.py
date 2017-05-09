
import functools
from os.path import exists

from nanohttp import settings, context
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.ext.declarative import declarative_base
from alembic import config, command

from restfulpy.orm.field import Field, relationship, composite
from restfulpy.orm.mixines import ModifiedMixin, SoftDeleteMixin, TimestampMixin, ActivationMixin, PaginationMixin, \
    FilteringMixin, OrderingMixin, OrderableMixin, ApproveRequiredMixin, FullTextSearchMixin
from restfulpy.orm.metadata import MetadataField
from restfulpy.orm.models import BaseModel
from restfulpy.orm.fulltext_search import to_tsvector

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

# There are two convenient ways for you to spare some typing.
# You can have a query property on all your model classes by doing this:
DeclarativeBase.query = DBSession.query_property()


def create_engine(uri=None, echo=None):
    return sa_create_engine(uri or settings.db.uri, echo=echo or settings.db.echo)


def init_model(engine):
    """
    Call me before using any of the tables or classes in the model.
    :param engine: SqlAlchemy engine to bind the session
    :return:
    """

    if DBSession.registry.has():
        DBSession.remove()

    DBSession.configure(bind=engine)


def drop_all(session=None):
    session = session or DBSession
    # noinspection PyUnresolvedReferences
    engine = session.bind
    metadata.drop_all(bind=engine)


def setup_schema(session=None):
    session = session or DBSession
    # noinspection PyUnresolvedReferences
    engine = session.bind
    metadata.create_all(bind=engine)

    if hasattr(settings, 'migration') and exists(settings.migration.directory):
        alembic_cfg = config.Config()
        alembic_cfg.set_main_option("script_location", settings.migration.directory)
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
        alembic_cfg.config_file_name = settings.migration.ini
        command.stamp(alembic_cfg, "head")


def create_thread_unsafe_session():
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
