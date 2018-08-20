from nanohttp import Controller, json
from restfulpy.controllers import RootController

import panda
from .availabilities import AvailabilityController
from .email import EmailController
from .member import MemberController
from .password import PasswordController
from .reset_password_token import ResetPasswordTokenController
from .token import TokenController


class ApiV1(Controller):
    emails = EmailController()
    members = MemberController()
    availabilities = AvailabilityController()
    tokens = TokenController()
    resetpasswordtokens = ResetPasswordTokenController()
    passwords = PasswordController()

    @json
    def version(self):
        return {
            'version': panda.__version__
        }


class Root(RootController):
    apiv1 = ApiV1()

