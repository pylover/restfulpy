from sqlalchemy import Unicode, Integer

from restfulpy.orm import DeclarativeBase, Field, ModifiedMixin


class ModificationCheckingModel(ModifiedMixin, DeclarativeBase):
    __tablename__ = 'modification_checking_model'
    __exclude__ = {'age'}

    title = Field(Unicode(50), primary_key=True)
    age = Field(Integer)


class ModificationExcludelessModel(ModifiedMixin, DeclarativeBase):
    __tablename__ = 'modification_checking_excludeless_model'

    title = Field(Unicode(50), primary_key=True)
    age = Field(Integer)


def test_modified_mixin(db):
    session = db()

    instance = ModificationCheckingModel(
        title='test title',
        age=1,
    )
    session.add(instance)

    excludeless_instance = ModificationExcludelessModel(
        title='test title',
        age=1,
    )
    session.add(excludeless_instance)
    session.commit()

    assert instance.modified_at is None
    assert instance.created_at is not None
    assert instance.last_modification_time == instance.created_at

    instance = session.query(ModificationCheckingModel).one()
    assert instance.modified_at is None
    assert instance.created_at is not None
    assert instance.last_modification_time == instance.created_at

    instance.age = 2
    session.commit()
    assert instance.modified_at is None
    assert instance.created_at is not None
    assert instance.last_modification_time == instance.created_at

    instance.title = 'Edited title'
    session.commit()
    assert instance.modified_at is not None
    assert instance.created_at is not None
    assert instance.last_modification_time == instance.modified_at

    instance = session.query(ModificationCheckingModel).one()
    assert instance.modified_at is not None
    assert instance.created_at is not None
    assert instance.last_modification_time == instance.modified_at

    excludeless_instance.age = 3
    session.commit()
    assert excludeless_instance.modified_at is not None
    assert excludeless_instance.created_at is not None
    assert excludeless_instance.last_modification_time == \
        excludeless_instance.modified_at

