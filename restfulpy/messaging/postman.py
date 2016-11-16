
from lemur.models import DBSession
from lemur.messaging.messenger import Messenger
from old.configuration import settings
import smtplib
from email.mime.text import MIMEText


class Postman(Messenger):

    def send_from(self, from_, to, subject, body, cc=None, bcc=None, template_string=None, template_filename=None):
        from lemur.worker.models import SendEmail
        task = SendEmail.schedule(
            from_, to, subject, body,
            cc=cc, bcc=bcc, template_filename=template_filename)
        DBSession.add(task)
        DBSession.commit()

    def smtp_send(self, from_, to, subject, body, cc=None, bcc=None, template_string=None, template_filename=None):
        """
        Sending messages by email
        """
        body = self.render_body(body, template_string, template_filename)

        smtp_config = settings.smtp
        smtp_server = smtplib.SMTP(
            host=smtp_config.host,
            port=smtp_config.port,
            local_hostname=smtp_config.local_hostname
        )
        smtp_server.starttls()
        smtp_server.login(smtp_config.username, smtp_config.password)

        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From'] = from_
        msg['To'] = to
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc

        smtp_server.send_message(msg)
        smtp_server.quit()
