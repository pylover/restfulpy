import threading
import contextlib
import io
import base64
from os import urandom
from os.path import split
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus

from restfulpy.mimetypes_ import guess_type
from restfulpy.utils import copy_stream


@contextlib.contextmanager
def simple_http_server(handler_class, server_class=HTTPServer, app=None, bind=('', 0)):
    server = server_class(bind, handler_class)
    if app:
        server.set_app(app)
    thread = threading.Thread(target=server.serve_forever, name='sa-media test server.', daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join()


def encode_multipart_data(fields: dict = None, files: dict = None):  # pragma: no cover
    boundary = ''.join(['-----', base64.urlsafe_b64encode(urandom(27)).decode()])
    crlf = b'\r\n'
    lines = []

    if fields:
        for key, value in fields.items():
            lines.append('--' + boundary)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append('')
            lines.append(value)

    if files:
        for key, file_path in files.items():
            filename = split(file_path)[1]
            lines.append('--' + boundary)
            lines.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"' %
                (key, filename))
            lines.append(
                'Content-Type: %s' %
                (guess_type(filename) or 'application/octet-stream'))
            lines.append('')
            lines.append(open(file_path, 'rb').read())

    lines.append('--' + boundary + '--')
    lines.append('')

    body = io.BytesIO()
    length = 0
    for l in lines:
        # noinspection PyTypeChecker
        line = (l if isinstance(l, bytes) else l.encode()) + crlf
        length += len(line)
        body.write(line)
    body.seek(0)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body, length


def mockup_http_static_server(content: bytes = b'Simple file content.', content_type: str = None, **kwargs):
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
            self.send_header('Content-Length', str(copy_stream(stream, buffer)))
            self.end_headers()
            buffer.seek(0)
            try:
                copy_stream(buffer, self.wfile)
            except ConnectionResetError:
                pass

        # noinspection PyPep8Naming
        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            if isinstance(content, bytes):
                self.serve_text()
            elif isinstance(content, str):
                self.serve_static_file(content)
            else:
                self.send_header('Content-Type', content_type)
                # noinspection PyTypeChecker
                self.serve_stream(content)

    return simple_http_server(StaticMockupHandler, **kwargs)
