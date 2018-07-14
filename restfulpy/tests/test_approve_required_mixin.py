from sqlalchemy import Integer, Unicode

from restfulpy.orm import DeclarativeBase, Field, ApproveRequiredMixin


class ApproveRequiredObject(ApproveRequiredMixin, DeclarativeBase):
    __tablename__ = 'approve_required_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


def test_approve_required_mixin(db):
    session = db(expire_on_commit=True)

    object1 = ApproveRequiredObject(
        title='object 1',
    )

    session.add(object1)
    session.commit()
    assert not object1.is_approved
    assert session.query(ApproveRequiredObject)\
        .filter(ApproveRequiredObject.is_approved).count() == 0

    object1.is_approved = True
    assert object1.is_approved
    session.commit()

    object1 = session.query(ApproveRequiredObject).one()
    assert  object1.is_approved

    json = object1.to_dict()
    assert 'isApproved' in json

    assert  session.query(ApproveRequiredObject)\
        .filter(ApproveRequiredObject.is_approved).count() == 1

    assert ApproveRequiredObject.filter_approved(session=session).count() == 1

    assert not ApproveRequiredObject.import_value(
        ApproveRequiredObject.is_approved, 'false'
    )
    assert not ApproveRequiredObject.import_value(
        ApproveRequiredObject.is_approved, 'FALSE'
    )
    assert not ApproveRequiredObject.import_value(
        ApproveRequiredObject.is_approved, 'False'
    )
    assert ApproveRequiredObject.import_value(
        ApproveRequiredObject.is_approved, 'true'
    )
    assert ApproveRequiredObject.import_value(
        ApproveRequiredObject.is_approved, 'TRUE'
    )
    assert ApproveRequiredObject.import_value(
        ApproveRequiredObject.is_approved, 'True'
    )

    assert ApproveRequiredObject.import_value(
        ApproveRequiredObject.title, 'title'
    ) == 'title'

