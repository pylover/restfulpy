import fcntl, termios, struct
import subprocess
from datetime import datetime


def terminal_size():
    h, w, hp, wp = struct.unpack(
        'HHHH',
        fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
    )
    return w, h


class ProgressBar:

    def __init__(self, total):
        self._value = 0
        self.total = total
        self.start_time = None
        try:
            self.terminal_width = terminal_size()[0]
        except OSError:
            self.terminal_width = 120

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
        td = datetime.utcnow() - self.start_time
        return 'time: %.2d:%.2d' % (td.seconds // 60, td.seconds % 60)

    @property
    def estimated_time(self):
        if self.value is 0:
            et = 0
        else:
            td = datetime.utcnow() - self.start_time
            et = td.total_seconds() * (self.total / self.value - 1)
        return 'eta: %.2d:%.2d' % (int(et) // 60, int(et) % 60)

    @property
    def marks(self):
        scale = 2
        v = self.percent // scale
        return '%s%s' % ('#' * int(v), '.' * int(100 // scale - v))

    def get_progressbar_color(self):
        percent = self.percent
        if percent < 10:
            return red
        elif percent < 20:
            return lightred
        elif percent < 30:
            return yellow
        elif percent < 40:
            return lightyellow
        elif percent < 50:
            return violet
        elif percent < 60:
            return lightviolet
        elif percent < 70:
            return beige
        elif percent < 80:
            return lightbeige
        elif percent < 90:
            return blue
        elif percent < 100:
            return lightblue
        else:
            return green

    def _invalidate(self):
        detailed = \
            ('%%%dd/%%d' % len(str(self.total))) % (self._value, self.total)
        percent = '%3d%%' % self.percent
        progress = '|%s|' % self.marks
        line = ' '.join((
            detailed,
            self.get_progressbar_color(),
            percent,
            progress,
            clear,
            self.time,
            yellow,
            self.estimated_time,
            clear
        ))
        print(line, end='', flush=False)
        print(' ' * (self.terminal_width - len(line)), end='\r', flush=True)

    def __enter__(self):
        self.start_time = datetime.utcnow()
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
        p = subprocess.Popen(
            ['wc', '-l', filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
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


# default color
clear = '\33[22;24;25;27;28;39;49m'

# foreground colors:
black = '\33[30m'
red = '\33[31m'
green = '\33[32m'
yellow = '\33[33m'
blue = '\33[34m'
violet = '\33[35m'
beige = '\33[36m'
white = '\33[37m'
grey = '\33[90m'
gray = '\33[90m'
lightred = '\33[91m'
lightgreen = '\33[92m'
lightyellow = '\33[93m'
lightblue = '\33[94m'
lightviolet = '\33[95m'
lightbeige = '\33[96m'
lightwhite = '\33[97m'

# background colors:
bblack = '\33[40m'
bred = '\33[41m'
bgreen = '\33[4m'
byellow = '\33[43m'
bblue = '\33[44m'
bviolet = '\33[45m'
bbeige = '\33[46m'
bwhite = '\33[47m'
bgrey = '\33[100m'
bgray = '\33[100m'
blightred = '\33[101m'
blightgreen = '\33[102m'
blightyellow = '\33[103m'
blightblue = '\33[104m'
blightviolet = '\33[105m'
blightbeige = '\33[106m'
blightwhite = '\33[107m'

# styles
bold = '\33[1m'
italic = '\33[3m'
