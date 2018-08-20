from nanohttp import json, context, settings
from restfulpy.controllers import RestController
from restfulpy.orm import DBSession, commit

from ..models import Member, ResetPasswordEmail
from ..tokens import ResetPasswordToken
from ..validators import email_validator


class ResetPasswordTokenController(RestController):

    @json(prevent_empty_form=True)
    @email_validator
    @commit
    def ask(self):
        email = context.form.get('email')

        if not DBSession.query(Member.email) \
                .filter(Member.email == email) \
                .count():
            return dict(email=email)

        token = ResetPasswordToken(dict(email=email))
        DBSession.add(
            ResetPasswordEmail(
                to=email,
                subject='Reset your CAS account password',
                body={
                    'reset_password_token': token.dump(),
                    'reset_password_callback_url':
                    settings.reset_password.callback_url
                }
            )
        )
        return dict(email=email)

