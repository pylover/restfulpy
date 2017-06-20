
import io
import unittest
from os.path import dirname, abspath, join

from nanohttp import settings, configure

from restfulpy.messaging.providers import create_messenger, ConsoleMessenger, SmtpProvider


HERE = abspath(dirname(__file__))


class MessengerFactoryTestCase(unittest.TestCase):
    __configuration__ = '''
        messaging:
          default_messenger: restfulpy.messaging.ConsoleMessenger 
        '''

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)

    def test_messenger_factory(self):
        console_messenger = create_messenger()
        self.assertIsInstance(console_messenger, ConsoleMessenger)

        settings.messaging.default_messenger = 'restfulpy.messaging.providers.SmtpProvider'
        smtp_messenger = create_messenger()
        self.assertIsInstance(smtp_messenger, SmtpProvider)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

