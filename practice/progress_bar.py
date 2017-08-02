import time

from restfulpy.cli.utils import ProgressBar


if __name__ == '__main__':
    with ProgressBar(100) as p:
        for i in range(100):
            time.sleep(.4)
            p.increment()
