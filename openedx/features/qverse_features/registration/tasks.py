"""
Qverse registration application celery tasks.
"""
from celery.task import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from edx_ace import ace
from edx_ace.recipient import Recipient

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.qverse_features.registration.message_types import RegistrationNotification


LOGGER = get_task_logger(__name__)
ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY')


@task(routing_key=ACE_ROUTING_KEY)
def send_bulk_mail_to_newly_created_students(students):
    """
    A celery task, responsible to send registration email to newly created users.

    Arguments:
        students (list): A list of dicts containing information about newly created/updated
                         users
    """
    new_students = [student for student in students if student.get('status') == 'Created']
    _assign_relevent_user_to_student(new_students)
    # Don't use get_current_site in loop
    # it will return None after first iteration
    site = get_current_site()
    context = get_base_template_context(site)
    for new_student in new_students:
        if new_student.get('user'):
            user = new_student['user']
            context.update(_get_user_context_for_email(new_student))
            message = RegistrationNotification().personalize(
                recipient=Recipient(username=user.username, email_address=user.email),
                language='en',
                user_context=context,
            )

            with emulate_http_request(site=site, user=user):
                try:
                    LOGGER.info('Attempting to send registration notification to newly created user ({}).'
                                .format(user.username))
                    ace.send(message)
                    LOGGER.info('Success: Task sending registration notification for new user ({}) creation.'
                                .format(user.username))

                except Exception:
                    LOGGER.info('Failure: Task sending registration notification for new user ({}) creation.'
                                .format(user.username))


def _assign_relevent_user_to_student(students):
    """
    Assigns relevent user object to a certain student record.

    Arguments:
        students (list): A list of dicts containing information related to
                         newly created/updated users (learners)
    """
    for student in students:
        try:
            student['user'] = User.objects.get(username=student.get('regno'))
        except User.DoesNotExist:
            student['user'] = None


def _get_user_context_for_email(student):
    """
    Sets user context for the registration email.

    Arguments:
        student (dict): Contains information regarding a newly created/updated
                        user (learner)

    Returns:
        user_context (dict): Contains student information which will be needed in
                             email templates
    """
    user_context = student.copy()
    user_context.pop('user', None)
    user_context['site_name'] = configuration_helpers.get_value(
        'SITE_NAME',
        settings.SITE_NAME
    )
    return user_context
