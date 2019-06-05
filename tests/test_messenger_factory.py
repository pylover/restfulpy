from os.path import dirname, abspath

from nanohttp import settings, configure

from restfulpy.messaging.providers import create_messenger, ConsoleMessenger,\
    SmtpProvider


HERE = abspath(dirname(__file__))

def test_messenger_factory():

    __configuration__ = '''
        messaging:
          default_messenger: restfulpy.messaging.ConsoleMessenger
        '''
    configure(force=True)
    settings.merge(__configuration__)

    console_messenger = create_messenger()
    assert isinstance(console_messenger, ConsoleMessenger)

    settings.messaging.default_messenger =\
        'restfulpy.messaging.providers.SmtpProvider'
    smtp_messenger = create_messenger()
    assert isinstance(smtp_messenger, SmtpProvider)

