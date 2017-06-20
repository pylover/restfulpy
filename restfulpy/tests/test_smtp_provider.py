
import unittest

from nanohttp import settings, configure

from restfulpy.messaging.providers import SmtpProvider
from restfulpy.testing.mockup import smtp_server


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
        '''

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)

    def test_smtp_provider(self):
        with smtp_server() as (server, bind):
            settings.smtp.host = bind[0]
            settings.smtp.port = bind[1]

            SmtpProvider().send(
                'test@example.com',
                'test@example.com',
                'Simple test body'
            )


if __name__ == '__main__':
    unittest.main()

