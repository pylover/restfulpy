import io
from os import mkdir
from os.path import dirname, abspath, join, exists

from restfulpy.utils import import_python_module_by_filename, \
    construct_class_by_name, copy_stream, md5sum


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
        'restfulpy.tests.test_utils.MyClassToConstructByName',
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

