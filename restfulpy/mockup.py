import asyncore
import contextlib
import io
import smtpd
import threading
from mimetypes import guess_type
from http.server import BaseHTTPRequestHandler, HTTPStatus, HTTPServer
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

from . import datetimehelpers
from .messaging import Messenger
from .utils import copy_stream
from .application import Application


@contextlib.contextmanager
def mockup_smtp_server(bind=('localhost', 0)):
    SMTP_SERVER_LOCK = threading.Event()
    class MockupSMTPServer(smtpd.SMTPServer):
        def __init__(self, bind):
            super().__init__(bind, None, decode_data=False)
            self.server_address = self.socket.getsockname()[:2]
            SMTP_SERVER_LOCK.set()

        def process_message(*args, **kwargs):
            pass


    server = MockupSMTPServer(bind)
    thread = threading.Thread(target=asyncore.loop, daemon=True)
    thread.start()
    SMTP_SERVER_LOCK.wait()
    yield server, server.server_address
    asyncore.close_all()


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


@contextlib.contextmanager
def mockup_localtimezone(timezone):
    backup = datetimehelpers.localtimezone
    datetimehelpers.localtimezone = timezone if callable(timezone) \
        else lambda: timezone

    yield

    datetimehelpers.localtimezone = backup


class MockupApplication(Application):
    __configuration__ = '''
     db:
       url: postgresql://postgres:postgres@localhost/restfulpy_dev
       test_url: postgresql://postgres:postgres@localhost/restfulpy_test
       administrative_url: postgresql://postgres:postgres@localhost/postgres
    '''

