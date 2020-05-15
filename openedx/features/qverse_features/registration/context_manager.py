"""
Contains context managers of QVerse registration app.
"""
from django.conf import settings


class one_time_password_link_expiry:
    """
    It's a context manager, responsible to set different expiry durations
    for reset password link and one time password link.
    """
    def __init__(self, **kwargs):
        self.last_login = kwargs['last_login']
        self.default_timeout = kwargs['default_timeout']

    def __enter__(self):
        """
        If user have never logged in to the system, we will change
        the expiry duration of reset password link.
        """
        if not self.last_login:
            settings.PASSWORD_RESET_TIMEOUT_DAYS = settings.OTP_LINK_TIMEOUT

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Revert to the original settings.
        """
        settings.PASSWORD_RESET_TIMEOUT_DAYS = self.default_timeout
