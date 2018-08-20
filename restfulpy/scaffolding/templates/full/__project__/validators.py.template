import re

from nanohttp import validate


USER_EMAIL_PATTERN = \
    re.compile('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')
USER_TITLE_PATTERN = re.compile('^[a-zA-Z][\w]{5,16}$')

# Password be to have numbers, uppercase, and lowercase
USER_PASSWORD_PATTERN = re.compile('(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).+')

email_validator = validate(
    email=dict(
        required='701 Invalid Email Format',
        pattern=(USER_EMAIL_PATTERN, '701 Invalid Email Format')
    )
)


title_validator = validate(
    title=dict(
        required='705 Invalid Title Format',
        pattern=(USER_TITLE_PATTERN, '705 Invalid Title Format')
    )
)


password_validator = validate(
    password=dict(
        required='702 Invalid Password Length',
        min_length=(6,'702 Invalid Password Length'),
        max_length=(20,'702 Invalid Password Length'),
        pattern=(USER_PASSWORD_PATTERN, '703 Password Not Complex Enough')
    )
)


new_password_validator = validate(
    newPassword=dict(
        required='702 Invalid Password Length',
        min_length=(6,'702 Invalid Password Length'),
        max_length=(20,'702 Invalid Password Length'),
        pattern=(USER_PASSWORD_PATTERN, '703 Password Not Complex Enough')
    )
)

