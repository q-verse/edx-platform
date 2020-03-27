"""
Contains message types which will be used by edx ace.
"""
from openedx.core.djangoapps.ace_common.message import BaseMessageType


class RegistrationNotification(BaseMessageType):
    """
    A message for notifying user that he/she has been registered.
    """
    pass
