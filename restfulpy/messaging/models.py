
from sqlalchemy import Integer, ForeignKey, Unicode, JSON
from sqlalchemy.ext.declarative import declared_attr

from nanohttp import settings
from restfulpy.orm import Field
from restfulpy.taskqueue import Task
from restfulpy.logging_ import get_logger
from .providers import create_messenger

logger = get_logger('messaging')


# noinspection PyAbstractClass
class BaseEmail(Task):
    __abstract__ = True

    from_ = Field(Unicode(100), json='from', default=lambda: settings.messaging.default_sender)
    to = Field(Unicode(100), json='to')
    subject = Field(Unicode(256), json='subject')
    cc = Field(Unicode(100), nullable=True, json='cc')
    bcc = Field(Unicode(100), nullable=True, json='bcc')

    # noinspection PyDefaultArgument,PyMethodParameters
    @declared_attr
    def id(cls):
        return Field(Integer, ForeignKey('task.id'), primary_key=True, json='id')

    @property
    def email_body(self):  # pragma: no cover
        raise NotImplementedError()

    @property
    def template_filename(self):  # pragma: no cover
        raise NotImplementedError

    def do_(self, context, attachments=None):
        messenger = create_messenger()
        messenger.send(
            self.to,
            self.subject,
            self.email_body,
            cc=self.cc,
            bcc=self.bcc,
            template_filename=self.template_filename,
            from_=self.from_,
            attachments=attachments
        )

        logger.info('%s is sent to %s', self.subject, self.to)


# noinspection PyAbstractClass
class Email(BaseEmail):  # pragma: no cover
    __tablename__ = 'email'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__
    }

    body = Field(JSON, json='body')

    @property
    def email_body(self):
        return self.body

