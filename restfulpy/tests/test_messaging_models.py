from nanohttp import settings

from restfulpy.messaging import BaseEmail, create_messenger
from restfulpy.orm import Field, FakeJson


class Welcome(BaseEmail):
    __tablename__ = 'welcome'

    __mapper_args__ = {
        'polymorphic_identity': 'welcome'
    }

    body = Field(FakeJson, json='body')

    @property
    def email_body(self):
        return self.body

    @property
    def template_filename(self):
        return None


def test_messaging_model(db):
    __configuration__ = '''
    messaging:
      default_sender: test@example.com
      default_messenger: restfulpy.mockup.MockupMessenger
    '''

    settings.merge(__configuration__)
    session = db()

    mockup_messenger = create_messenger()

    # noinspection PyArgumentList
    message = Welcome(
        to='test@example.com',
        subject='Test Subject',
        body={'msg': 'Hello'}
    )

    session.add(message)
    session.commit()

    message.do_({})

    # noinspection PyUnresolvedReferences

    assert mockup_messenger.last_message == {
        'body': {'msg': 'Hello'},
        'subject': 'Test Subject',
        'to': 'test@example.com'
    }

