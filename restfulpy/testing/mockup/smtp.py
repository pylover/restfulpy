
import smtpd
import asyncore
import threading
import contextlib


SERVER_LOCK = threading.Event()


class MockupSMTPServer(smtpd.SMTPServer):

    def __init__(self, bind):
        super().__init__(bind, None, decode_data=False)
        self.server_address = self.socket.getsockname()[:2]
        SERVER_LOCK.set()

    def process_message(*args, **kwargs):
        pass


@contextlib.contextmanager
def smtp_server(bind=('localhost', 0)):
    server = MockupSMTPServer(bind)
    thread = threading.Thread(target=asyncore.loop, daemon=True)
    thread.start()
    SERVER_LOCK.wait()
    yield server, server.server_address
    # server.close()
    asyncore.close_all() #ignore_all=True)
    # thread.join()
