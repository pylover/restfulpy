from sqlalchemy import Integer, Unicode

from restfulpy.orm import DeclarativeBase, Field, DeactivationMixin


class DeactiveObject(DeactivationMixin, DeclarativeBase):
    __tablename__ = 'deactive_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


def test_deactivation_mixin(db):
    session = db()

    object1 = DeactiveObject(
        title='object 1',
    )

    session.add(object1)
    session.commit()

    assert object1.is_active == False
    assert session.query(DeactiveObject).filter(DeactiveObject.is_active)\
        .count() == 0

    object1.is_active = True

    assert object1.is_active == True
    session.commit()
    object1 = session.query(DeactiveObject).one()
    assert object1.is_active == True
    assert object1.deactivated_at is None
    assert object1.activated_at is not None

    object1.is_active = False
    assert object1.is_active == False
    session.commit()
    object1 = session.query(DeactiveObject).one()

    assert object1.is_active == False
    assert object1.activated_at is None
    assert object1.deactivated_at is not None

