import base64
import io
import os
from os.path import split

from .mimetypes_ import guess_type


def encode_multipart_data(fields: dict = None, files: dict = None):  # pragma: no cover
    boundary = ''.join([
        '-----',
        base64.urlsafe_b64encode(os.urandom(27)).decode()
    ])
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
        line = (l if isinstance(l, bytes) else l.encode()) + crlf
        length += len(line)
        body.write(line)
    body.seek(0)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body, length



