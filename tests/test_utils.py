import io
from tempfile import mktemp
from os import mkdir
from os.path import dirname, abspath, join, exists

from restfulpy.utils import import_python_module_by_filename, \
    construct_class_by_name, copy_stream, md5sum, to_camel_case, \
    encode_multipart_data, split_url


HERE = abspath(dirname(__file__))
DATA_DIR = join(HERE, 'data')


if not exists(DATA_DIR):
    mkdir(DATA_DIR)


class MyClassToConstructByName:
    def __init__(self, a):
        self.a = a


def test_import_python_module_by_filename():
    filename = join(DATA_DIR, 'a.py')
    with open(filename, mode='w') as f:
        f.write('b = 123\n')

    module_ = import_python_module_by_filename('a', filename)
    assert module_.b == 123


def test_construct_class_by_name():
    obj = construct_class_by_name(
        'tests.test_utils.MyClassToConstructByName',
        1
    )
    assert obj.a ==  1
    assert obj is not None


def test_copy_stream():
    content = b'This is the initial source file'
    source = io.BytesIO(content)
    target = io.BytesIO()
    copy_stream(source, target)
    target.seek(0)
    assert target.read() == content


def test_md5sum():
    content = b'This is the initial source file'
    source = io.BytesIO(content)
    filename = join(DATA_DIR, 'a.txt')
    with open(filename, mode='wb') as f:
        f.write(content)

    assert md5sum(source) == md5sum(filename)


def test_to_camel_case():
    assert to_camel_case('foo_bar_baz') == 'fooBarBaz'


def test_encode_multipart():
    filename = f'{mktemp()}.txt'
    with open(filename, 'w') as f:
        f.write('abcdefgh\n')

    contenttype, body, length = encode_multipart_data(
        dict(foo='bar'),
        files=dict(bar=filename),
        boundary='MAGIC'
    )
    assert contenttype.startswith('multipart/form')
    assert body.read().decode() == \
        f'--MAGIC\r\nContent-Disposition: form-data; ' \
        f'name="foo"\r\n\r\nbar\r\n--MAGIC\r\nContent-Disposition: ' \
        f'form-data; name="bar"; filename="{filename.split("/")[-1]}"' \
        f'\r\nContent-Type: text/plain\r\n\r\nabcdefgh\n\r\n--MAGIC--\r\n\r\n'
    assert length == 193


def test_split_url():
    url = 'https://www.example.com/id/1?a=1&b=2'
    path, query = split_url(url)

    assert path == 'https://www.example.com/id/1'
    assert query == dict(a='1', b='2')

