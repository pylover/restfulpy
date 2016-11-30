
from restfulpy.messaging import Messenger


class MockupMessenger(Messenger):
    _last_body = None

    @property
    def last_body(self):
        return self.__class__._last_body

    @last_body.setter
    def last_body(self, value):
        self.__class__._last_body = value

    def send(self, to, subject, body, cc=None, bcc=None, template_string=None, template_filename=None, from_=None):
        self.last_body = {
            'to': to,
            'body': body,
            'subject': subject
        }
