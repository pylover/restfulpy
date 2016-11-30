
from nanohttp import settings

from restfulpy.utils import construct_class_by_name

from restfulpy.messaging.providers import Messenger
from restfulpy.messaging.models import Email


def create_messenger() -> Messenger:
    return construct_class_by_name(settings.messaging.default_messenger)
