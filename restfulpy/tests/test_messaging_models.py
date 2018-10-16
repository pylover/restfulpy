from nanohttp import settings

from restfulpy.messaging import Email, create_messenger


def test_messaging_model(db):
    __configuration__ = '''
    messaging:
      default_sender: test@example.com
      default_messenger: restfulpy.mockup.MockupMessenger
    '''

    settings.merge(__configuration__)
    session = db()

    mockup_messenger = create_messenger()

    message = Email(
        to='test@example.com',
        subject='Test Subject',
        body={'msg': 'Hello'}
    )

    session.add(message)
    session.commit()

    message.do_({'counter': 1}, {})

    assert mockup_messenger.last_message == {
        'body': {'msg': 'Hello'},
        'subject': 'Test Subject',
        'to': 'test@example.com'
    }

