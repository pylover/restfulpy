import asyncore
import contextlib
import io
import smtpd
import threading
from http.server import BaseHTTPRequestHandler, HTTPStatus, HTTPServer
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

from . import datetimehelpers
from .messaging import Messenger
from .mimetypes_ import guess_type
from .utils import copy_stream
from .application import Application


SERVER_LOCK = threading.Event()


@contextlib.contextmanager
def mockup_http_server(app=None, handler_class=WSGIRequestHandler,
                server_class=WSGIServer, bind=('', 0)):
    server = server_class(bind, handler_class)
    if app:
        assert isinstance(server, WSGIServer)
        server.set_app(app)
    thread = threading.Thread(
        target=server.serve_forever,
        name='sa-media test server.',
        daemon=True
    )
    thread.start()
    url = 'http://localhost:%s' % server.server_address[1]
    yield server, url
    server.shutdown()
    thread.join()


def mockup_http_static_server(content: bytes = b'Simple file content.',
                              content_type: str = None, **kwargs):
    class StaticMockupHandler(BaseHTTPRequestHandler):  # pragma: no cover
        def serve_text(self):
            self.send_header('Content-Type', "text/plain")
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Last-Modified', self.date_time_string())
            self.end_headers()
            self.wfile.write(content)

        def serve_static_file(self, filename):
            self.send_header('Content-Type', guess_type(filename))
            with open(filename, 'rb') as f:
                self.serve_stream(f)

        def serve_stream(self, stream):
            buffer = io.BytesIO()
            self.send_header(
                'Content-Length',
                str(copy_stream(stream, buffer))
            )
            self.end_headers()
            buffer.seek(0)
            try:
                copy_stream(buffer, self.wfile)
            except ConnectionResetError:
                pass

        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            if isinstance(content, bytes):
                self.serve_text()
            elif isinstance(content, str):
                self.serve_static_file(content)
            else:
                self.send_header('Content-Type', content_type)
                self.serve_stream(content)

    return simple_http_server(
        None,
        handler_class=StaticMockupHandler,
        server_class=HTTPServer,
        **kwargs
    )


class MockupSMTPServer(smtpd.SMTPServer):

    def __init__(self, bind):
        super().__init__(bind, None, decode_data=False)
        self.server_address = self.socket.getsockname()[:2]
        SERVER_LOCK.set()

    def process_message(*args, **kwargs):
        pass


@contextlib.contextmanager
def mockup_smtp_server(bind=('localhost', 0)):
    server = MockupSMTPServer(bind)
    thread = threading.Thread(target=asyncore.loop, daemon=True)
    thread.start()
    SERVER_LOCK.wait()
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
        if attachments:
            for attachment in attachments:
                assert hasattr(attachment, 'name')
        self.last_message = {
            'to': to,
            'body': body,
            'subject': subject
        }


@contextlib.contextmanager
def mockup_localtimezone(timezone):
    backup = datetimehelpers.localtimezone
    if callable(timezone):
        datetimehelpers.localtimezone = timezone
    else:
        datetimehelpers.localtimezone = lambda: timezone

    yield

    datetimehelpers.localtimezone = backup


class MockupApplication(Application):
    __configuration__ = '''
     db:
       url: postgresql://postgres:postgres@localhost/restfulpy_dev
       test_url: postgresql://postgres:postgres@localhost/restfulpy_test
       administrative_url: postgresql://postgres:postgres@localhost/postgres
    '''

