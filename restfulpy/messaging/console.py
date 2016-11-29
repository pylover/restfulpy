
from restfulpy.messaging.messenger import Messenger


class ConsoleMessenger(Messenger):
    def send_from(self, from_, to, subject, body, cc=None, bcc=None, template_string=None, template_filename=None):
        """
        Sending messages by email
        """

        body = self.render_body(body, template_string, template_filename)
        print(body)
