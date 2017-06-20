
import io
import unittest
from os.path import dirname, abspath, join

from nanohttp import configure

from restfulpy.messaging.providers import ConsoleMessenger


HERE = abspath(dirname(__file__))


class SmtpProviderTestCase(unittest.TestCase):
    __configuration__ = '''
        messaging:
            mako_modules_directory: %s
            template_dirs:
              - %s
        ''' % (
        join(HERE, 'data', 'mako_modules'),
        join(HERE, 'templates'),
    )

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)

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


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

