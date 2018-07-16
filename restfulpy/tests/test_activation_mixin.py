from sqlalchemy import Integer, Unicode

from restfulpy.orm import DeclarativeBase, Field, ActivationMixin, \
    AutoActivationMixin


class ActiveObject(ActivationMixin, DeclarativeBase):
    __tablename__ = 'active_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class AutoActiveObject(AutoActivationMixin, DeclarativeBase):
    __tablename__ = 'auto_active_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


def test_activation_mixin(db):
    session = db(expire_on_commit=False)

    object1 = ActiveObject(
        title='object 1',
    )

    session.add(object1)
    session.commit()
    assert not object1.is_active
    assert session.query(ActiveObject)\
        .filter(ActiveObject.is_active)\
        .count() == 0

    object1.is_active = True
    assert object1.is_active
    session.commit()

    object1 = session.query(ActiveObject).one()
    assert object1.is_active

    assert 'isActive' in object1.to_dict()

    assert session.query(ActiveObject)\
        .filter(ActiveObject.is_active)\
        .count() == 1
    assert ActiveObject.filter_activated(session.query(ActiveObject)).count()\
        == 1

    assert not ActiveObject.import_value(ActiveObject.is_active, 'false')
    assert not ActiveObject.import_value(ActiveObject.is_active, 'FALSE')
    assert not ActiveObject.import_value(ActiveObject.is_active, 'False')
    assert ActiveObject.import_value(ActiveObject.is_active, 'true')
    assert ActiveObject.import_value(ActiveObject.is_active, 'TRUE')
    assert ActiveObject.import_value(ActiveObject.is_active, 'True')
    assert ActiveObject.import_value(ActiveObject.title, 'title') == 'title'


def test_auto_activation(db):
    session = db()
    object1 = AutoActiveObject(
        title='object 1',
    )

    session.add(object1)
    session.commit()
    assert object1.is_active
    assert session.query(AutoActiveObject)\
        .filter(AutoActiveObject.is_active)\
        .count() == 1


def test_metadata():
    # Metadata
    object_metadata = ActiveObject.json_metadata()
    fields = object_metadata['fields']

    assert 'id' in fields
    assert 'title' in fields
    assert 'isActive' in fields

