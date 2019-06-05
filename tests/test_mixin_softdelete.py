import pytest
from sqlalchemy import Unicode

from restfulpy.orm import DeclarativeBase, Field, SoftDeleteMixin


class SoftDeleteCheckingModel(SoftDeleteMixin, DeclarativeBase):
    __tablename__ = 'soft_delete_checking_model'

    title = Field(Unicode(50), primary_key=True)


def test_soft_delete_mixin(db):
    session = db()

    instance = SoftDeleteCheckingModel(
        title='test title'
    )
    session.add(instance)
    session.commit()
    instance.assert_is_not_deleted()
    with pytest.raises(ValueError):
        instance.assert_is_deleted()

    instance = session.query(SoftDeleteCheckingModel).one()
    instance.soft_delete()
    session.commit()
    instance.assert_is_deleted()
    with pytest.raises(ValueError):
        instance.assert_is_not_deleted()

    query = session.query(SoftDeleteCheckingModel)
    assert SoftDeleteCheckingModel.filter_deleted(query).count() == 1
    assert SoftDeleteCheckingModel.exclude_deleted(query).count() == 0

    instance.soft_undelete()
    session.commit()
    instance.assert_is_not_deleted()
    with pytest.raises(ValueError):
        instance.assert_is_deleted()

    assert SoftDeleteCheckingModel.filter_deleted(query).count() == 0
    assert SoftDeleteCheckingModel.exclude_deleted(query).count() == 1

    session.delete(instance)
    with pytest.raises(AssertionError):
        session.commit()

