from os.path import basename
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from mako.lookup import TemplateLookup
from nanohttp import settings, LazyAttribute

from restfulpy.utils import construct_class_by_name


class Messenger(object):
    """
    The abstract base class for everyone messaging operations
    """

    def render_body(self, body, template_filename=None):
        if template_filename:
            mako_template = self.lookup.get_template(template_filename)
        else:
            mako_template = None

        if mako_template:
            return mako_template.render(**body)
        else:
            return body

    @LazyAttribute
    def lookup(self):
        return TemplateLookup(
            module_directory=settings.messaging.mako_modules_directory,
            directories=settings.messaging.template_dirs,
            input_encoding='utf8'
        )

    def send(self, to, subject, body, cc=None, bcc=None, template_filename=None, from_=None, attachments=None):
        raise NotImplementedError


class SmtpProvider(Messenger):

    def send(self, to, subject, body, cc=None, bcc=None, template_filename=None, from_=None, attachments=None):
        """
        Sending messages with SMTP server
        """
        # FIXME: Exception handling

        body = self.render_body(body, template_filename)

        smtp_config = settings.smtp
        smtp_server = smtplib.SMTP(
            host=smtp_config.host,
            port=smtp_config.port,
            local_hostname=smtp_config.local_hostname
        )
        smtp_server.starttls()
        smtp_server.login(smtp_config.username, smtp_config.password)

        from_ = from_ or smtp_config.username

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_
        msg['To'] = to
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc

        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        if attachments:
            for attachment in attachments:
                assert hasattr(attachment, 'name')
                attachment_part = MIMEApplication(attachment.read(), Name=basename(attachment.name))
                attachment_part['Content-Disposition'] = 'attachment; filename="%s"' % basename(attachment.name)
                msg.attach(attachment_part)

        smtp_server.send_message(msg)
        smtp_server.quit()


class ConsoleMessenger(Messenger):
    def send(self, to, subject, body, cc=None, bcc=None, template_filename=None, from_=None, attachments=None):
        """
        Sending messages by email
        """

        body = self.render_body(body, template_filename)
        print(body)


def create_messenger() -> Messenger:
    return construct_class_by_name(settings.messaging.default_messenger)
