"""
Qverse registration application celery tasks.
"""
from celery.task import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from edx_ace import ace
from edx_ace.recipient import Recipient

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.qverse_features.registration.message_types import RegistrationNotification


LOGGER = get_task_logger(__name__)
ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


@task(routing_key=ACE_ROUTING_KEY)
def send_bulk_mail_to_newly_created_students(new_students, site_id):
    """
    A celery task, responsible to send registration email to newly created users.

    Arguments:
        students (list): A list of dicts containing information about newly created
                         users
        site_id (int): Current site id
    """
    site = Site.objects.get(id=site_id)
    context = {
        'site_name': site.domain
    }
    for new_student in new_students:
        user = None
        try:
            user = User.objects.get(username=new_student.get('regno'))
        except User.DoesNotExist:
            LOGGER.exception('User having registration number ({}) does not exist.'.format(new_student.get('regno')))
            continue

        with emulate_http_request(site=site, user=user):
            context.update(get_base_template_context(site))
            context.update(new_student)
            message = RegistrationNotification().personalize(
                recipient=Recipient(username=user.username, email_address=user.email),
                language='en',
                user_context=context,
            )

            try:
                LOGGER.info('Attempting to send registration notification to newly created user ({}).'
                            .format(user.username))
                ace.send(message)
                LOGGER.info('Success: Task sending registration notification for new user ({}) creation.'
                            .format(user.username))

            except Exception:
                LOGGER.exception('Failure: Task sending registration notification for new user ({}) creation.'
                                 .format(user.username))
