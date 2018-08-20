from nanohttp import json, context, HTTPStatus, HTTPForbidden
from restfulpy.controllers import ModelRestController
from restfulpy.orm import DBSession, commit

from ..models import Member
from ..tokens import RegisterationToken
from ..validators import title_validator, password_validator


class MemberController(ModelRestController):
    __model__ = Member

    @json(prevent_empty_form=True)
    @title_validator
    @password_validator
    @Member.expose
    @commit
    def register(self):
        title = context.form.get('title')
        password = context.form.get('password')
        ownership_token = context.form.get('ownershipToken')

        if DBSession.query(Member.title).filter(Member.title == title).count():
            raise HTTPStatus('604 Title Is Already Registered')

        regiteration_token_payload = RegisterationToken.load(ownership_token)
        email = regiteration_token_payload['email']

        if DBSession.query(Member.email).filter(Member.email == email).count():
            raise HTTPStatus('601 Email Address Is Already Registered')

        member = Member(email=email, title=title, password=password)
        DBSession.add(member)
        principal = member.create_jwt_principal()
        context.response_headers.add_header(
            'X-New-JWT-Token',
            principal.dump().decode('utf-8')
        )
        return member

    @json
    @Member.expose
    def get(self, id):
        try:
            id = int(id)
        except:
            raise HTTPForbidden()

        if id != context.identity.payload['memberId']:
            raise HTTPForbidden()

        member = DBSession.query(Member).filter(Member.id == id).one_or_none()
        if not member:
            raise HTTPForbidden()

        return member

