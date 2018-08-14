from datetime import datetime

from sqlalchemy import Integer, Unicode, not_
from sqlalchemy.sql.expression import desc, asc

from restfulpy.orm import DeclarativeBase, ActivationMixin, PaginationMixin,\
    FilteringMixin, OrderingMixin, Field


class Student(
    DeclarativeBase,
    ActivationMixin,
    PaginationMixin,
    FilteringMixin,
    OrderingMixin
):
    __tablename__ = 'student'
    id = Field(Integer, primary_key=True)
    name = Field(Unicode(100), max_length=90)


def test_activation_mixin(db):
    """
    This unittest is wrote to test the combination of mixins
    """
    session = db()

    activated_student = Student()
    activated_student.name = 'activated-student'
    activated_student.activated_at = datetime.utcnow()
    session.add(activated_student)

    deactivated_student = Student()
    deactivated_student.name = 'deactivated-student'
    deactivated_student.activated_at = None
    session.add(deactivated_student)

    session.commit()

    # Test ordering:
    student_list = session.query(Student).\
        order_by(desc(Student.is_active)).all()
    assert student_list[0].activated_at is not None
    assert student_list[-1].activated_at is None

    student_list = session.query(Student).\
        order_by(asc(Student.is_active)).all()
    assert student_list[-1].activated_at is not None
    assert student_list[0].activated_at is None

    # Test filtering:
    student_list = session.query(Student).filter(Student.is_active).all()
    for student in student_list:
       assert student.activated_at is not None

    student_list = session.query(Student).filter(not_(Student.is_active)).all()
    for student in student_list:
        assert student.activated_at is None

