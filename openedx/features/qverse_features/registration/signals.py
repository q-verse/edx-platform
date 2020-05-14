"""
Signals for qverse registration application.
"""
import logging
import re
from csv import DictReader, DictWriter, Error, Sniffer

from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string

from openedx.core.djangoapps.theming.helpers import get_current_site, get_current_request
from openedx.features.qverse_features.registration.models import (BulkUserRegistration, QVerseUserProfile,
                                                                  Department, REGISTRATION_NUMBER_MAX_LENGTH,
                                                                  SURNAME_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
                                                                  MOBILE_NUMBER_MAX_LENGTH, OTHER_NAME_MAX_LENGTH,
                                                                  MAX_LEVEL_CHOICES, MAX_PROGRAMME_CHOICES)
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
        CsvRowValidator.prepare_csv_row_validator()
        for row in reader:
            row['status'] = ''
            row['error'] = ''
            is_valid_row, errors = CsvRowValidator.validate_csv_row(row)

            if is_valid_row:
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
                    row['error'] = error
            else:
                LOGGER.exception('Error while creating/updating ({}) user and its profiles because of invalid values '
                                 'of required fields with the following errors {}.'.format(row.get('regno'), errors))
                row['status'] = USER_CREATION_FAILED
                row['error'] = errors

            output_file_rows.append(row)
    except Error as err:
        LOGGER.exception('Error while traversing {} file content with following error {}.'
                         .format(instance.admission_file.path, err))
    csv_file.close()
    _write_status_on_csv_file(instance.admission_file.path, output_file_rows)
    new_students = [student for student in output_file_rows if student.get('status') == USER_CREATED]
    site = get_current_site()
    protocol = 'https' if get_current_request().is_secure() else 'http'
    send_bulk_mail_to_newly_created_students.delay(new_students, site.id, protocol)


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
        edx_user.set_password(get_random_string())
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
    department = Department.objects.get(number=user_info.get('departmentid'))
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
                # to maintain the order of fields in csv
                fieldnames = [
                    'regno', 'email', 'firstname', 'surname', 'othername', 'mobile',
                    'departmentid', 'programmeid', 'levelid', 'status', 'error'
                ]
                writer = DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for row in output_file_rows:
                    writer.writerow(row)
    except IOError as error:
        LOGGER.error('(filename) --- {}'.format(filename, error.strerror))


class CsvRowValidator(object):
    """
    Validates single CSV row data.
    """
    validated_regno = set()

    def __init__(self, row):
        self.regno = row['regno']
        self.email = row['email']
        self.first_name = row['firstname']
        self.surname = row['surname']
        self.other_name = row['othername']
        self.mobile_number = row['mobile']
        self.department_id = row['departmentid']
        self.programme_id = row['programmeid']
        self.current_level = row['levelid']
        self.errors = []

    @staticmethod
    def prepare_csv_row_validator():
        """
        Cleans all the static variables of the class to get ready for the validation
        of new file.
        """
        CsvRowValidator.validated_regno.clear()

    @staticmethod
    def validate_csv_row(row):
        """
        Validates that each CSV contains all the required fields and all field
        values are according to the acceptance criteria.

        Arguments:
            row (dict): A dictionary containing user information

        Returns:
            flag (boolean): Shows that the provided row contains valid data or not
            errors (str): Contains errors related to provided row
        """
        error = CsvRowValidator._validate_required_fields_presence(row)
        if error:
            return False, error

        row_validator = CsvRowValidator(row)
        row_validator._validate_field_values()
        if row_validator.errors:
            # to write multiple lines
            # in a single cell of csv
            errors = '"{}"'.format('\n'.join(row_validator.errors))
            return False, errors

        return True, None

    @staticmethod
    def _validate_required_fields_presence(row):
        """
        Validates that given row contains all the required fields.

        Arguments:
            row (dict): A dictionary containing user information

        Returns:
            error (str): Contains error related to provided row
        """
        OPTIONAL_FIELDS = [
            'mobile', 'othername', 'status', 'error'
        ]
        required_values = [value.strip() if value else value for (key, value) in row.items() if key not in OPTIONAL_FIELDS]
        all_values_available = all(required_values)

        if not all_values_available:
            return 'Please provide values for all required fields.'

    @staticmethod
    def _has_symbols(value):
        """
        Validates that the provided value doesn't contain any symbol.

        Arguments:
            value (str): A string which is to be validated

        Returns:
            flag (bool): Shows that provided value is valid or not
        """
        return not bool(re.match('^[A-Za-z0-9 ]*$', value))

    def _validate_field_values(self):
        """
        Validates the values of all the given fields of single CSV row.
        """
        self._validate_registration_number()
        self._validate_unique_regno_in_single_csv_file()
        self._validate_email_address()
        self._validate_unique_email_constraint()
        self._validate_first_name()
        self._validate_surname()
        self._validate_other_name()
        self._validate_current_level()
        self._validate_department_number()
        self._validate_programme_id()
        self._validate_mobile_number()

    def _validate_unique_regno_in_single_csv_file(self):
        """
        Validates that there should be only one occurrence of one particular
        registration number with valid related data in the uploaded CSV file.
        """
        is_user_exist = User.objects.filter(username=self.regno).exists()
        if is_user_exist and self.regno in CsvRowValidator.validated_regno:
            self.errors.append('An entry with registration number {} already exists in this file.'.format(self.regno))
        else:
            CsvRowValidator.validated_regno.add(self.regno)

    def _validate_email_address(self):
        try:
            validate_email = EmailValidator()
            validate_email(self.email)
        except ValidationError:
            self.errors.append('Please provide a valid email address.')

    def _validate_unique_email_constraint(self):
        try:
            user = User.objects.get(email=self.email)
            if user.username != self.regno:
                self.errors.append('{} is already associated with another user account.'.format(self.email))
        except User.DoesNotExist:
            pass

    def _validate_department_number(self):
        try:
            if not Department.objects.filter(number=self.department_id).exists():
                self.errors.append('Department number {} does not exist.'.format(self.department_id))
        except ValueError:
            self.errors.append('Please provide a valid integer value for department id.')

    def _validate_registration_number(self):
        if len(self.regno) > REGISTRATION_NUMBER_MAX_LENGTH:
            self.errors.append('Registration number is more than {} characters long.'.format(REGISTRATION_NUMBER_MAX_LENGTH))

        if not self.regno.isalnum():
            self.errors.append('Please provide some valid alpha numeric value for registration number.')

    def _validate_first_name(self):
        if len(self.first_name) > FIRST_NAME_MAX_LENGTH:
            self.errors.append('First name is more than {} characters long.'.format(FIRST_NAME_MAX_LENGTH))

        if CsvRowValidator._has_symbols(self.first_name):
            self.errors.append('Please don\'t include any symbol in the first name.')

    def _validate_surname(self):
        if len(self.surname) > SURNAME_MAX_LENGTH:
            self.errors.append('Surname is more than {} characters long.'.format(SURNAME_MAX_LENGTH))

        if CsvRowValidator._has_symbols(self.surname):
            self.errors.append('Please don\'t include any symbol in the surname.')

    def _validate_other_name(self):
        if len(self.other_name) > OTHER_NAME_MAX_LENGTH:
            self.errors.append('Other name is more than {} characters long.'.format(OTHER_NAME_MAX_LENGTH))

        if CsvRowValidator._has_symbols(self.other_name):
            self.errors.append('Please don\'t include any symbol in the other name.')

    def _validate_mobile_number(self):
        if len(self.mobile_number) > MOBILE_NUMBER_MAX_LENGTH:
            self.errors.append('Mobile number is more than {} characters long.'.format(MOBILE_NUMBER_MAX_LENGTH))

    def _validate_programme_id(self):
        try:
            programme_id = int(self.programme_id)
            if programme_id < 1 or programme_id > MAX_PROGRAMME_CHOICES:
                self.errors.append('Programme ID must be greater than 0 and smaller than {}.'.format(MAX_PROGRAMME_CHOICES+1))
        except ValueError:
            self.errors.append('Programme ID is not an integer value.')

    def _validate_current_level(self):
        try:
            current_level = int(self.current_level)
            if int(current_level) < 1 or int(current_level) > MAX_LEVEL_CHOICES:
                self.errors.append('Level ID must be greater than 0 and smaller than {}.'.format(MAX_LEVEL_CHOICES+1))
        except ValueError:
            self.errors.append('Level ID is not an integer value.')
