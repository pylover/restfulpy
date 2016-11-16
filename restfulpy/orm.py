
import re
import cgi
from datetime import datetime, date, time
from decimal import Decimal

from nanohttp import HttpBadRequest, settings
from sqlalchemy import Column, Unicode, String, DateTime, Integer, event, create_engine as sa_create_engine
from sqlalchemy.orm import SynonymProperty, validates, object_session, relationship as sa_relationship, \
    scoped_session, sessionmaker
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import declarative_base
from alembic import config, command

from restfulpy.utils import format_iso_datetime, format_iso_time
from restfulpy.exceptions import ValidationError


# noinspection PyAbstractClass
class Field(Column):

    @property
    def can_validate(self):
        return 'pattern' in self.info or \
            'min_length' in self.info or \
            'max_length' in self.info

    def __init__(self,
                 *args,
                 json=None,
                 readonly=None,
                 max_length=None,
                 min_length=None,
                 pattern=None,
                 protected=None,
                 watermark=None,
                 **kwargs):
        info = dict()

        if json is not None:
            info['json'] = json

        if readonly is not None:
            info['readonly'] = readonly

        if protected is not None:
            info['protected'] = protected

        if watermark is not None:
            info['watermark'] = watermark

        if max_length is not None:
            info['max_length'] = max_length

        if min_length is not None:
            info['min_length'] = min_length

        if pattern is not None:
            info['pattern'] = pattern

        if args and isinstance(args[0], (Unicode, String)):
            info['max_length'] = args[0].length

        super(Field, self).__init__(*args, info=info, **kwargs)

    def _validate_pattern(self, value):
        if value is None:
            return
        if not re.match(self.info['pattern'], value):
            raise ValidationError(self.name, 'Cannot match "%s" with field acceptable pattern' % value)
        return value

    def _validate_length(self, value, min_length, max_length):
        if value is None:
            return

        if not isinstance(value, str):
            raise ValidationError(self.name, 'Invalid type: %s' % type(value))
        value_length = len(value)
        if min_length is not None:
            if value_length < min_length:
                raise ValidationError(self.name, 'Please enter at least %d characters.' % min_length)

        if max_length is not None:
            if value_length > max_length:
                raise ValidationError(self.name, 'Cannot enter more that : %d in this field.' % max_length)

    def validate(self, value):
        if 'pattern' in self.info:
            self._validate_pattern(value)

        if 'min_length' in self.info or 'max_length' in self.info:
            self._validate_length(value, self.info.get('min_length'), self.info.get('max_length'))
        return value

    @property
    def is_attachment(self):
        return 'attachment' in self.info


def relationship(*args, json=None, **kwargs):
    info = dict()
    if json is not None:
        info['json'] = json
    return sa_relationship(*args, info=info, **kwargs)


class MetadataField(object):
    def __init__(self, json_name, key, type_=str, default_=None, optional=None,
                 pattern=None, max_length=None, min_length=None, message='Invalid value',
                 watermark=None):
        self.json_name = json_name
        self.key = key[1:] if key.startswith('_') else key
        self.type_ = type_
        self.default_ = default_
        self.optional = optional
        self.pattern = pattern
        self.max_length = max_length
        self.min_length = min_length
        self.message = message
        self.watermark = watermark

    @property
    def type_name(self):
        return self.type_ if isinstance(self.type_, str) else self.type_.__name__

    def to_json(self):
        return dict(
            name=self.json_name,
            key=self.key,
            type_=self.type_name,
            default=self.default_,
            optional=self.optional,
            pattern=self.pattern,
            maxLength=self.max_length,
            minLength=self.min_length,
            message=self.message,
            watermark=self.watermark,
        )

    @classmethod
    def from_column(cls, c, info=None):
        if not info:
            info = c.info
        json_name = info['json']
        result = []

        if 'attachment' in info:
            result.append(cls(
                '%sUrl' % json_name,
                '%s_url' % c.key,
                type_='url',
                message=info.get('message') if 'message' in info else 'Invalid File'
            ))

            result.append(cls(
                '%sThumbnails' % json_name,
                '%s_thumbnails' % c.key,
                type_='dict',
                message=info.get('message') if 'message' in info else 'Invalid File'
            ))

        else:
            key = c.key

            if hasattr(c, 'default') and c.default:
                default_ = c.default.arg if c.default.is_scalar else 'function(...)'
            else:
                default_ = ''

            if 'unreadable' in info and info['unreadable']:
                type_ = 'str'
            elif hasattr(c, 'type'):
                type_ = c.type.python_type
            elif hasattr(c, 'target'):
                type_ = c.target.name
            else:
                raise AttributeError('Unable to recognize type of the column: %s' % c.name)

            result.append(cls(
                json_name,
                key,
                type_=type_,
                default_=default_,
                optional=c.nullable if hasattr(c, 'nullable') else None,
                pattern=info.get('pattern'),
                max_length=info.get('max_length') if 'max_length' in info else
                (c.type.length if hasattr(c, 'type') and hasattr(c.type, 'length') else None),
                min_length=info.get('min_length'),
                message=info.get('message') if 'message' in info else 'Invalid Value',
                watermark=info.get('watermark') if 'watermark' in info else None,
            ))

        return result


class BaseModel(object):
    __pagination__ = 'server'
    _key_serializer = None

    @classmethod
    def get_column(cls, column):
        if isinstance(column, str):
            mapper = inspect(cls)
            return mapper.columns[column]
        if isinstance(column, SynonymProperty):
            return column.parent.columns[column.name]
        return column

    @classmethod
    def convert_value(cls, column, v):
        c = cls.get_column(column)
        if isinstance(c, Column):
            if c.type.python_type is bool and not isinstance(v, bool):
                return str(v).lower() == 'true'
        return v

    @classmethod
    def prepare_for_export(cls, column, v):
        param_name = column.info['json']
        result = {}

        if isinstance(v, datetime):
            result.update({
                param_name: None if not v or v == datetime.min else format_iso_datetime(v),
            })

        elif isinstance(v, date):
            result.update({
                param_name: None if not v or v == datetime.min else v.isoformat(),
            })

        elif isinstance(v, time):
            result[param_name] = format_iso_time(v)

        elif v is None:
            result[param_name] = v

        elif hasattr(v, 'to_json'):
            result[param_name] = v.to_json()

        elif isinstance(v, Decimal):
            result[param_name] = str(v)

        elif isinstance(v, set):
            result[param_name] = list(v)

        else:
            result[param_name] = v

        return result

    @classmethod
    def from_request(cls, request):
        model = cls()
        # noinspection PyUnresolvedReferences
        DBSession.add(model)
        model.update_from_request(request)
        return model

    @classmethod
    def json_metadata(cls):
        fields = {}
        result = {
            'pagination': cls.__pagination__,
            'fields': fields
        }
        for c in cls.iter_json_columns(relationships=True, include_readonly_columns=True):
            metadata_fields = MetadataField.from_column(cls.get_column(c), info=c.info)
            for f in metadata_fields:
                fields[f.key] = f
        return result

    def update_from_request(self, request):
        for column, value in self.extract_data_from_request(request):
            if isinstance(column, Field) and column.is_attachment:
                if value is not None and (isinstance(value, cgi.FieldStorage) or hasattr(value, 'read')):
                    getattr(self, column.key[1:]).from_request(request, column, value)
            else:
                if 'unreadable' in column.info and (not value or (isinstance(value, str) and not value.strip())):
                    continue
                setattr(
                    self,
                    column.key[1:] if column.key.startswith('_') else column.key,
                    self.convert_value(column, value))

    @classmethod
    def iter_columns(cls, relationships=True, synonyms=True, use_inspection=True):
        if use_inspection:
            mapper = inspect(cls)
            for c in mapper.columns:
                yield c

            if synonyms:
                for c in mapper.synonyms:
                    yield c

            if relationships:
                for c in mapper.relationships:
                    yield c
        else:
            # noinspection PyUnresolvedReferences
            for c in cls.__table__.c:
                yield c

    @classmethod
    def iter_json_columns(cls, include_readonly_columns=True, **kw):
        for c in cls.iter_columns(**kw):
            if 'json' in c.info:
                if not include_readonly_columns:
                    if c.info.get('readonly'):
                        continue
                    else:
                        yield c
                else:
                    yield c

    @classmethod
    def extract_data_from_request(cls, request):
        for c in cls.iter_json_columns():
            param_name = c.info['json']

            if 'readonly' in c.info and c.info['readonly'] and \
                    (param_name in request.form_dict or (request.files and param_name in request.files)):
                raise HttpBadRequest('Invalid parameter: %s' % c.info['json'])

            if param_name in request.form_dict:
                yield c, request.form_dict[param_name]
            elif request.files and param_name in request.files:
                yield c, request.files[param_name][0]

    def to_json(self):
        result = {}
        for c in self.iter_json_columns():
            if 'protected' in c.info and c.info['protected']:
                continue
            if isinstance(c, Field) and c.is_attachment:
                value = getattr(self, c.key[1:])
                result.update(value.to_json())
            else:
                result.update(self.prepare_for_export(c, getattr(self, c.key)))
        return result

    @property
    def _session(self):
        return object_session(self)


@event.listens_for(BaseModel, 'class_instrument')
def receive_class_instrument(cls):
    for field in cls.iter_columns(relationships=False, synonyms=False, use_inspection=False):
        if not isinstance(field, Field) or not field.can_validate:
            continue
        method_name = 'validate_%s' % field.name
        if not hasattr(cls, method_name):
            def validator(self, key, value):
                return self.get_column(key).validate(value)

            setattr(cls, method_name, validates(field.name)(validator))


class TimestampMixin(object):
    created_at = Field(DateTime, default=datetime.now, nullable=False, json='createdAt', readonly=True)


class ModifiedMixin(TimestampMixin):
    modified_at = Field(DateTime, nullable=True, json='modifiedAt', readonly=True)

    @property
    def last_modification_time(self):
        return self.modified_at if self.modified_at else self.created_at

    # noinspection PyUnusedLocal
    @staticmethod
    def on_update(mapper, connection, target):
        target.modified_at = datetime.now()

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_update', cls.on_update)


class OrderableMixin(object):
    order = Field("order", Integer, default=0, nullable=False)
    __mapper_args__ = dict(order_by=order)

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


def create_engine():
    return sa_create_engine(settings.db.uri, echo=settings.db.echo)


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

    alembic_cfg = config.Config()
    alembic_cfg.set_main_option("script_location", settings.migration.directory)
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
    alembic_cfg.config_file_name = settings.migration.ini
    command.stamp(alembic_cfg, "head")
