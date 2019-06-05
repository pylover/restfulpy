import io
from os.path import dirname, abspath, join

from nanohttp import configure, settings

from restfulpy.messaging.providers import ConsoleMessenger


HERE = abspath(dirname(__file__))


class TestSmtpProvider:
    __configuration__ = f'''
        messaging:
            mako_modules_directory: {join(HERE, '../../data', 'mako_modules')}
            template_dirs:
              - {join(HERE, 'templates')}
        '''

    @classmethod
    def setup_class(cls):
        configure(force=True)
        settings.merge(cls.__configuration__)

    def test_console_messenger(self):
        # Without templates
        ConsoleMessenger().send(
            'test@example.com',
            'test@example.com',
            'Simple test body',
            cc='test@example.com',
            bcc='test@example.com'
        )

        # With template
        ConsoleMessenger().send(
            'test@example.com',
            'test@example.com',
            {},
            template_filename='test-email-template.mako'
        )

        # With attachments
        attachment = io.BytesIO(b'This is test attachment file')
        attachment.name = 'path/to/file.txt'
        ConsoleMessenger().send(
            'test@example.com',
            'test@example.com',
            'email body with Attachment',
            attachments=[attachment]
        )


