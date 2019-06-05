from sqlalchemy import Integer, String

from restfulpy.orm import DeclarativeBase, Field


class Member(DeclarativeBase):
    __tablename__ = 'members'

    id = Field(Integer, primary_key=True, autoincrement=True)
    username = Field(String(50))


def test_db(db):
    session = db()
    assert session.query(Member).count() == 0

