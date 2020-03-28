import logging
from csv import DictReader, DictWriter, Error, Sniffer

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string

from openedx.features.qverse_features.registration.models import BulkUserRegistration, QVerseUserProfile, Department
from openedx.features.qverse_features.registration.tasks import send_bulk_mail_to_newly_created_students
from student.models import UserProfile


LOGGER = logging.getLogger(__name__)
# User creation statuses
USER_CREATED = 'Created'
USER_UPDATED = 'Updated'
USER_CREATION_FAILED = 'Failed'


@receiver(post_save, sender=BulkUserRegistration)
def create_users_from_csv_file(sender, instance, created, **kwargs):
    """
    Creates/Updates users, their profiles and sends registration emails.

    Reads data from given csv file having user details. Then creates/updates
    edx user, edx user profile and qverse user profile accordingly. It
    writes the status of creation/update on the given file by adding an
    extra column named 'status' in it. It handles all the exceptions raised by
    any function called inside it. Also sends the registration email to newly
    created users.

    Arguments:
        sender (ModelBase): responsible to initiate the signal
        instance (BulkUserRegistration): newly created/updated object of BulkUserRegistration
        created (bool): Is created/updated?
        kwargs (dict): Other info
    """
    csv_file = None
    dialect = None
    try:
        csv_file = open(instance.admission_file.path, 'r')
        dialect = Sniffer().sniff(csv_file.readline())
        csv_file.seek(0)
    except IOError as error:
        LOGGER.exception('({}) --- {}'.format(error.filename, error.strerror))
        return
    dict_reader = DictReader(csv_file, delimiter=dialect.delimiter if dialect else ',')
    # The header of uploaded csv might be in uppercase, lowercase or in camel case
    # so to make our code independent to case just turn all the keys of reader into lower case.
    # Also in python standard library for csv there is an option named skipinitialwhitespaces
    # which is only applied for leading whitespaces and there is no option for trailing
    # whitespaces. So, we will have to handle that case ourselves
    reader = (dict((k.strip().lower(), v.strip() if v else v) for k, v in row.items()) for row in dict_reader)
    output_file_rows = []
    try:
        for row in reader:
            row['status'] = ''
            if _validate_single_csv_row(row):
                try:
                    # Creating/Updating edX User, edX User Profile and QVerse User Profile
                    # will be an atomic operation. If one operation fails the previous
                    # successfull operations will be reverted and no changes will be applied.
                    with transaction.atomic():
                        edx_user = _create_or_update_edx_user(row)
                        _create_or_update_edx_user_profile(edx_user)
                        _create_or_update_qverse_user_profile(edx_user, row)
                except IntegrityError as error:
                    LOGGER.exception('Error while creating/updating ({}) user and its '
                                     'profiles with the following errors {}.'.format(row.get('regno'), error))
                    row['status'] = USER_CREATION_FAILED
            else:
                LOGGER.exception('Error while creating/updating ({}) user and its profiles because of invalid values '
                                 'of required fields.'.format(row.get('regno')))
                row['status'] = USER_CREATION_FAILED

            output_file_rows.append(row)
    except Error as err:
        LOGGER.exception('Error while traversing {} file content with following error {}.'
                         .format(instance.admission_file.path, err))
    csv_file.close()
    _write_status_on_csv_file(instance.admission_file.path, output_file_rows)
    new_students = [student for student in output_file_rows if student.get('status') == USER_CREATED]
    send_bulk_mail_to_newly_created_students.delay(new_students)


def _create_or_update_edx_user(user_info):
    """
    Creates/Updates edx user from given information.

    Arguments:
        user_info (dict): A dict containing user information

    Returns:
        edx_user (User): A newly created/updated User object
    """
    user_data = {
                    'email': user_info.get('email'),
                    'first_name': user_info.get('firstname'),
                    'last_name': user_info.get('surname'),
                    'is_active': True
                }

    edx_user, created = User.objects.update_or_create(username=user_info.get('regno'), defaults=user_data)
    if created:
        user_info['password'] = get_random_string()
        edx_user.set_password(user_info['password'])
        edx_user.save()
        LOGGER.info('{} user has been created.'.format(edx_user.username))
    else:
        LOGGER.info('{} user has been updated.'.format(edx_user.username))
    return edx_user


def _create_or_update_edx_user_profile(edx_user):
    """
    Creates/Updates edx user profile.

    Arguments:
        edx_user (User): An edx user instance whose profile is going to be created/updated
    """
    full_name = '{} {}'.format(edx_user.first_name, edx_user.last_name)
    _, created = UserProfile.objects.update_or_create(user=edx_user, defaults={'name': full_name})
    if created:
        LOGGER.info('{} edx profile has been created.'.format(edx_user.username))
    else:
        LOGGER.info('{} edx profile has been updated.'.format(edx_user.username))


def _create_or_update_qverse_user_profile(edx_user, user_info):
    """
    Creates/Updates qverse user profile.

    It also stores the status of the creation/update in the receiving list which
    contains the content which will be written on output file.

    Arguments:
        edx_user (User): An edx user instance whose qverse profile is going to be created/updated
        user_info (dict): User info whose profile is going to be created/updated
    """
    department = None
    try:
        department = Department.objects.get(number=user_info.get('departmentid'))
    except Department.DoesNotExist:
        LOGGER.exception('The Department with id {} does not exist.'.format(user_info.get('departmentid')))
        user_info['status'] = USER_CREATION_FAILED
        return

    qverse_profile_data = {
                            'current_level': user_info.get('levelid'),
                            'other_name': user_info.get('othername'),
                            'mobile_number': user_info.get('mobile'),
                            'programme': user_info.get('programmeid'),
                            'department': department,
                            'registration_number': user_info.get('regno')
                          }
    _, created = QVerseUserProfile.objects.update_or_create(user=edx_user, defaults=qverse_profile_data)
    if created:
        LOGGER.info('{} qverse profile has been created.'.format(edx_user.username))
        user_info['status'] = USER_CREATED
    else:
        LOGGER.info('{} qverse profile has been updated.'.format(edx_user.username))
        user_info['status'] = USER_UPDATED


def _write_status_on_csv_file(filename, output_file_rows):
    """
    Writes on the given file.

    Arguments:
        filename (str): Complete path of the output file
        output_file_rows (list): List of CSV file rows
    """
    try:
        with open(filename, 'w') as csv_file:
            if output_file_rows:
                writer = DictWriter(csv_file, fieldnames=output_file_rows[0].keys())
                writer.writeheader()
                for row in output_file_rows:
                    writer.writerow(row)
    except IOError as error:
        LOGGER.error('(filename) --- {}'.format(filename, error.strerror))


def _validate_single_csv_row(row):
    """
    Validates that row contains certian values for required fields.

    Arguments:
        row (dict): Contains the single row of data from CSV file
    """
    OPTIONAL_FIELDS = [
        'mobile', 'othername', 'status'
    ]
    required_values = [value for (key, value) in row.items() if key not in OPTIONAL_FIELDS]
    return all(required_values)
