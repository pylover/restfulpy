# -*- coding: utf-8 -*-
from sqlalchemy import Table, Column, Integer, ForeignKey, create_engine, Unicode
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
__author__ = 'vahid'

Base = declarative_base()

person_addresses_table = Table('person_addresses', Base.metadata,
    Column('left_id', Integer, ForeignKey('left.id')),
    Column('right_id', Integer, ForeignKey('right.id'))
)


class Person(Base):
    __tablename__ = 'left'
    id = Column(Integer, primary_key=True)
    addresses = relationship("Address", secondary=person_addresses_table, backref="persons")
    name = Column(Unicode)


class Address(Base):
    __tablename__ = 'right'
    id = Column(Integer, primary_key=True)
    phone = Column(Unicode)


engine = create_engine('sqlite://', echo=True)
Base.metadata.create_all(engine)
session_factory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=True,
    twophase=False)

if __name__ == '__main__':
    session = session_factory()
    vahid = Person(name='vahid')
    work = Address(phone='09122451075')
    vahid.addresses.append(work)

    session.add(vahid)
    session.commit()
    session.close()

    vahid = session.query(Person).one()
    assert len(vahid.addresses) == 1

    work = vahid.addresses[0]
    vahid.addresses.remove(work)
    assert len(vahid.addresses) == 0
    session.commit()

    vahid = session.query(Person).filter(Person.id == 2000).one()



