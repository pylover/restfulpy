from nanohttp import json, context, HTTPStatus, HTTPForbidden, \
    HTTPNotFound
from restfulpy.controllers import ModelRestController
from restfulpy.orm import DBSession, commit
from restfulpy.authorization import authorize

from ..models import Foo


class FooController(ModelRestController):
    __model__ = Foo

    @authorize
    @json(prevent_empty_form=True)
    @Foo.validate(strict=True)
    @Foo.expose
    @commit
    def create(self):
        title = context.form.get('title')

        if DBSession.query(Foo).filter(Foo.title == title).count():
            raise HTTPStatus('604 Title Is Already Registered')

        foo = Foo()
        foo.update_from_request()
        DBSession.add(foo)
        return foo

    @authorize
    @json(prevent_empty_form=True)
    @Foo.validate
    @Foo.expose
    @commit
    def edit(self, id):

        foo = DBSession.query(Foo) \
            .filter(Foo.id == id) \
            .one_or_none()

        if foo is None:
            raise HTTPNotFound(f'Foo with id: {id} is not registered')

        foo.update_from_request()
        return foo

    @authorize
    @json(prevent_form=True)
    @Foo.expose
    @commit
    def get(self, id):

        foo = DBSession.query(Foo) \
            .filter(Foo.id == id) \
            .one_or_none()

        if foo is None:
            raise HTTPNotFound(f'Foo with id: {id} is not registered')

        return foo

    @authorize
    @json(prevent_form=True)
    @Foo.expose
    @commit
    def delete(self, id):

        foo = DBSession.query(Foo) \
            .filter(Foo.id == id) \
            .one_or_none()

        if foo is None:
            raise HTTPNotFound(f'Foo with id: {id} is not registered')

        DBSession.delete(foo)
        return foo

    @authorize
    @json(prevent_form=True)
    @Foo.expose
    @commit
    def list(self):
        return DBSession.query(Foo)

