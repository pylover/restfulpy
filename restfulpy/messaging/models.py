
from sqlalchemy import Integer, ForeignKey, Unicode, JSON

from nanohttp import settings
from restfulpy.orm import Field
from restfulpy.taskqueue import Task
from restfulpy.messaging import create_messenger
from restfulpy.logging_ import get_logger

logger = get_logger('messaging')


class Email(Task):
    __tablename__ = 'email'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__
    }

    id = Field(Integer, ForeignKey('task.id'), primary_key=True, json='id')
    from_ = Field(Unicode(100), json='from', default=lambda: settings.messaging.default_sender)
    to = Field(Unicode(100), json='to')
    subject = Field(Unicode(256), json='subject')
    body = Field(JSON, json='body')
    cc = Field(Unicode(100), nullable=True, json='cc')
    bcc = Field(Unicode(100), nullable=True, json='bcc')

    @property
    def template_filename(self):
        raise NotImplementedError

    @property
    def email_body(self):
        return self.body

    def do_(self, context):
        messenger = create_messenger()
        messenger.send(
            self.to,
            self.subject,
            self.email_body,
            cc=self.cc,
            bcc=self.bcc,
            template_filename=self.template_filename,
            from_=self.from_,
        )

        logger.info('%s is sent to %s', self.subject, self.to)
