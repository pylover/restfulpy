
from nanohttp import settings

from restfulpy.utils import construct_class_by_name

from restfulpy.messaging.messenger import Messenger


def create_messenger() -> Messenger:
    return construct_class_by_name(settings.messaging.default_messenger)
