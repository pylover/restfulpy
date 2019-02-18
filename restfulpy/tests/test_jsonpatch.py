from bddrest import response, when, status
from nanohttp import context, json, RestController, HTTPNotFound, HTTPStatus
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import JsonPatchControllerMixin
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase


class Person(DeclarativeBase):
    __tablename__ = 'person'

    id = Field(Integer, primary_key=True)
    title = Field(
        Unicode(50),
        unique=True,
        index=True,
        min_length=2,
        watermark='Title',
        label='Title'
    )


class Root(JsonPatchControllerMixin, RestController):
    __model__ = Person

    @json(prevent_empty_form=True)
    @commit
    def create(self):
        title = context.form.get('title')

        if DBSession.query(Person).filter(Person.title == title).count():
            raise HTTPStatus('600 Already person has existed')

        person = Person(
            title=context.form.get('title')
        )
        DBSession.add(person)
        return person

    @json(prevent_form=True)
    def get(self, title: str):
        person = DBSession.query(Person) \
            .filter(Person.title == title) \
            .one_or_none()

        if person is None:
            raise HTTPNotFound()

        return person

    @json
    @Person.expose
    def list(self):
        return DBSession.query(Person)


class TestJsonPatchMixin(ApplicableTestCase):
    __controller_factory__ = Root

    @classmethod
    def mockup(cls):
        session = cls.create_session()
        cls.person = Person(
            title='already_added',
        )
        session.add(cls.person)
        session.commit()

    def test_jsonpatch(self):
        with self.given(
            'Testing the patch method',
            verb='PATCH',
            url='/',
            json=[
                dict(op='CREATE', path='', value=dict(title='first')),
                dict(op='CREATE', path='', value=dict(title='second'))
            ]
        ):
            assert status == 200
            assert len(response.json) == 2
            assert response.json[0]['id'] is not None
            assert response.json[1]['id'] is not None

            when(
                'Testing the list method using patch',
                json=[dict(op='LIST', path='')]
            )
            assert len(response.json) == 1
            assert len(response.json[0]) == 3

            when(
                'Trying to pass without value',
                json=[
                    dict(op='CREATE', path='', value=dict(title='third')),
                    dict(op='CREATE', path=''),
                ]
            )
            assert status == 400

            when('Trying to pass with empty form', json={})
            assert status == '400 Empty Form'

            id = self.person.id
            when(
                'Prevent Form',
                json=[
                    dict(op='GET', path=f'{id}', value=dict(form='form1')),
                    dict(op='GET', path=f'{id}')
                ]
            )
            assert status == '400 Form Not Allowed'


    def test_jsonpatch_rollback(self):
        with self.given(
            'Testing rollback scenario',
            verb='PATCH',
            url='/',
            json=[
                dict(op='CREATE', path='', value=dict(title='third')),
                dict(op='CREATE', path='', value=dict(title='already_added'))
            ]
        ):
            assert status == '600 Already person has existed'

            when(
                'Trying to get the person that not exist',
                verb='GET',
                url='/third',
                json=None,
            )
            assert status == 404

