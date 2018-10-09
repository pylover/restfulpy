from nanohttp import json, context, settings, HTTPStatus
from restfulpy.controllers import RestController
from restfulpy.orm import DBSession, commit

from ..models import Member, RegisterEmail
from ..tokens import RegistrationToken
from ..validators import email_validator


class EmailController(RestController):

    @json(prevent_empty_form=True)
    @email_validator
    @commit
    def claim(self):
        email = context.form.get('email')

        if DBSession.query(Member.email).filter(Member.email == email).count():
            raise HTTPStatus('601 Email Address Is Already Registered')

        token = RegistrationToken(dict(email=email))
        DBSession.add(
            RegisterEmail(
                to=email,
                subject='Register your CAS account',
                body={
                    'registration_token': token.dump(),
                    'registration_callback_url':
                    settings.registration.callback_url
                }
            )
        )
        return dict(email=email)

