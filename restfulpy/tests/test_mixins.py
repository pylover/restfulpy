import unittest
from datetime import datetime

from sqlalchemy import Integer, Unicode, not_
from sqlalchemy.sql.expression import desc, asc

from nanohttp import configure

from restfulpy.orm import DeclarativeBase, ActivationMixin, PaginationMixin, FilteringMixin, \
    OrderingMixin, Field, create_engine, init_model, setup_schema, DBSession


class Student(DeclarativeBase, ActivationMixin, PaginationMixin, FilteringMixin, OrderingMixin):
    __tablename__ = 'student'
    id = Field(Integer, primary_key=True)
    name = Field(Unicode(100), max_length=90)


class MixinTestCase(unittest.TestCase):
    __configuration__ = '''
        db:
          uri: sqlite://    # In memory DB
          echo: false
        '''

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)
        cls.engine = create_engine()
        init_model(cls.engine)
        setup_schema()

    def test_activation_mixin(self):
        activated_student = Student()
        activated_student.name = 'activated-student'
        activated_student.activated_at = datetime.now()
        DBSession.add(activated_student)

        deactivated_student = Student()
        deactivated_student.name = 'deactivated-student'
        deactivated_student.activated_at = None
        DBSession.add(deactivated_student)

        DBSession.commit()

        # Test ordering:
        student_list = Student.query.order_by(desc(Student.is_active)).all()
        self.assertIsNotNone(student_list[0].activated_at)
        self.assertIsNone(student_list[-1].activated_at)

        student_list = Student.query.order_by(asc(Student.is_active)).all()
        self.assertIsNotNone(student_list[-1].activated_at)
        self.assertIsNone(student_list[0].activated_at)

        # Test filtering:
        student_list = Student.query.filter(Student.is_active).all()
        for student in student_list:
            self.assertIsNotNone(student.activated_at)

        student_list = Student.query.filter(not_(Student.is_active)).all()
        for student in student_list:
            self.assertIsNone(student.activated_at)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
