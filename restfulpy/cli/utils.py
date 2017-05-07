
import subprocess
from datetime import datetime


class ProgressBar:

    def __init__(self, total):
        self._value = 0
        self.total = total
        self.start_time = None

    def increment(self):
        self._value += 1
        self._invalidate()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        self._invalidate()

    @property
    def percent(self):
        return self._value * 100 // self.total

    @property
    def time(self):
        td = datetime.now() - self.start_time
        return '%.2d:%.2d' % (td.seconds // 60, td.seconds % 60)

    @property
    def estimated_time(self):
        if self.value is 0:
            et = 0
        else:
            td = datetime.now() - self.start_time
            et = td.total_seconds() * (self.total / self.value - 1)
        return '%.2d:%.2d' % (int(et) // 60, int(et) % 60)

    @property
    def marks(self):
        scale = 2
        v = self.percent // scale
        return '%s%s' % ('#' * int(v), '.' * int(100 // scale - v))

    def _invalidate(self):
        detailed = ('%%%dd/%%d' % len(str(self.total))) % (self._value, self.total)
        percent = '%3d%%' % self.percent
        progress = '|%s|' % self.marks
        print(' '.join((detailed, percent, progress, self.time, self.estimated_time)), end='\r', flush=True)

    def __enter__(self):
        self.start_time = datetime.now()
        self._invalidate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._invalidate()
        print()


class LineReaderProgressBar(ProgressBar):
    """
    A proxy for IO file, with progressbar for reading file line by line.
    
    """
    def __init__(self, filename, mode='r'):
        self.filename = filename
        self.file = open(filename, mode)
        super().__init__(self.file_len(filename))

    @staticmethod
    def file_len(filename):
        p = subprocess.Popen(['wc', '-l', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, err = p.communicate()
        if p.returncode != 0:
            raise IOError(err)
        return int(result.strip().split()[0])

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.__exit__(exc_type, exc_val, exc_tb)
        return super().__exit__(exc_type, exc_val, exc_tb)

    def readline(self):
        self.increment()
        return self.file.readline()

    def __iter__(self):
        return self

    def __next__(self):
        self.increment()
        return self.file.__next__()
