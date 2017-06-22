
import io
import unittest
from os.path import dirname, abspath, join

from nanohttp import settings, configure

from restfulpy.messaging.providers import SmtpProvider
from restfulpy.testing.mockup import smtp_server


HERE = abspath(dirname(__file__))


class SmtpProviderTestCase(unittest.TestCase):
    __configuration__ = '''
        smtp:
          host: smtp.example.com
          port: 587
          username: user@example.com
          password: password
          local_hostname: localhost
          tls: false
          auth: false
          ssl: false
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

    def test_smtp_provider(self):
        with smtp_server() as (server, bind):
            settings.smtp.host = bind[0]
            settings.smtp.port = bind[1]

            # Without templates
            SmtpProvider().send(
                'test@example.com',
                'test@example.com',
                'Simple test body',
                cc='test@example.com',
                bcc='test@example.com'
            )

            # With template
            SmtpProvider().send(
                'test@example.com',
                'test@example.com',
                {},
                template_filename='test-email-template.mako'
            )

            # With attachments
            attachment = io.BytesIO(b'This is test attachment file')
            attachment.name = 'path/to/file.txt'
            SmtpProvider().send(
                'test@example.com',
                'test@example.com',
                'email body with Attachment',
                attachments=[attachment]
            )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

