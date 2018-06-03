import base64
import ujson

from restfulpy.messaging import Messenger
from restfulpy.principal import JwtPrincipal
from restfulpy.application import Application


# noinspection PyAbstractClass
class MockupApplication(Application):
    builtin_configuration = '''
    db:
      test_url: postgresql://postgres:postgres@localhost/restfulpy_test
      administrative_url: postgresql://postgres:postgres@localhost/postgres
    logging:
      loggers:
        default:
          level: critical
    '''

    def configure(self, files=None, context=None, **kwargs):
        _context = dict(
            process_name='restfulpy_unittests'
        )
        if context:
            _context.update(context)
        super().configure(files=files, context=_context, **kwargs)

class MockupMessenger(Messenger):
    _last_message = None

    @property
    def last_message(self):
        return self.__class__._last_message

    @last_message.setter
    def last_message(self, value):
        self.__class__._last_message = value

    def send(
            self,
            to, subject, body,
            cc=None,
            bcc=None,
            template_string=None,
            template_filename=None,
            from_=None,
            attachments=None
    ):
        self.last_message = {
            'to': to,
            'body': body,
            'subject': subject
        }


class UnsafePrincipal(JwtPrincipal):  # pragma: no cover
    @classmethod
    def load(cls, encoded, force=False):
        decoded = base64.b64decode('%s=' % encoded.split('.')[1])  # To avoid padding exception
        payload = ujson.loads(decoded)
        return cls(payload)
