"""
Signals for qverse registration application.
"""
import logging
from csv import DictReader, DictWriter, Error, Sniffer

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver

from openedx.features.qverse_features.registration.models import (AdmissionData, Department, ProspectiveUser,
                                                                  QVerseUserProfile, REGISTRATION_NUMBER_MAX_LENGTH,
                                                                  SURNAME_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
                                                                  MOBILE_NUMBER_MAX_LENGTH, OTHER_NAME_MAX_LENGTH,
                                                                  MAX_LEVEL_CHOICES, MAX_PROGRAMME_CHOICES)


LOGGER = logging.getLogger(__name__)
# Prospectice User creation statuses
PROSPECTIVE_USER_CREATED = 'Saved'
PROSPECTIVE_USER_UPDATED = 'Updated'
PROSPECTIVE_USER_CREATION_FAILED = 'Failed'


@receiver(post_save, sender=AdmissionData)
def create_prospective_users_from_csv_file(sender, instance, created, **kwargs):
    """
    Creates/Updates prospective users.

    Reads data from given csv file having user details. Then creates/updates
    prospective users accordingly. It writes the status of creation/update/failure
    on the given file by adding an extra column named 'status' in it. In case of
    any error occurred, it writes it on the given file by adding an extra column
    named 'error'.

    Arguments:
        sender (ModelBase): responsible to initiate the signal
        instance (AdmissionData): newly created/updated object of AdmissionData
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
            row['error'] = ''
            is_valid_row, errors = _validate_single_csv_row(row)
            if is_valid_row:
                try:
                    if QVerseUserProfile.objects.filter(registration_number=row['regno']).exists():
                        row['status'] = PROSPECTIVE_USER_CREATION_FAILED
                        row['error'] = 'A user with this registration number ({}) already exists.'.format(row['regno'])
                        output_file_rows.append(row)
                        continue

                    department = Department.objects.get(number=row['departmentid'])
                    user_data = {
                        'email': row['email'],
                        'first_name': row['firstname'],
                        'surname': row['surname'],
                        'other_name': row['othername'],
                        'department': department,
                        'current_level': row['levelid'],
                        'programme': row['programmeid'],
                        'mobile_number': row['mobile']
                    }
                    _, created = ProspectiveUser.objects.update_or_create(registration_number=row['regno'],
                                                                          defaults=user_data)
                    if created:
                        row['status'] = PROSPECTIVE_USER_CREATED
                    else:
                        row['status'] = PROSPECTIVE_USER_UPDATED
                except (IntegrityError, Department.DoesNotExist, ValidationError) as error:
                    LOGGER.exception('Error while creating/updating ({}) prospective user '
                                     'with the following errors {}.'.format(row.get('regno'), error))
                    row['status'] = PROSPECTIVE_USER_CREATION_FAILED
                    if type(error) == IntegrityError:
                        row['error'] = 'Duplicate entry for email {}'.format(row['email'])
                    else:
                        row['error'] = error.message

            else:
                LOGGER.exception('Error while creating/updating ({}) prospective user and because of invalid values '
                                 'of required fields with the following errors ({}).'.format(row.get('regno'), errors))
                row['status'] = PROSPECTIVE_USER_CREATION_FAILED
                row['error'] = errors

            output_file_rows.append(row)
    except Error as err:
        LOGGER.exception('Error while traversing {} file content with following error {}.'
                         .format(instance.admission_file.path, err))
    csv_file.close()
    _write_status_on_csv_file(instance.admission_file.path, output_file_rows)


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


def _validate_single_csv_row(row):
    """
    Validates that row contains certian values for required fields.

    Arguments:
        row (dict): Contains the single row of data from CSV file

    Returns:
        status (bool): Tells that csv row is valid or not
        errors (str): Returns all the errors if occurred
    """
    OPTIONAL_FIELDS = [
        'mobile', 'othername', 'status', 'error'
    ]
    required_values = [value.strip() if value else value for (key, value) in row.items() if key not in OPTIONAL_FIELDS]
    all_values_available = all(required_values)

    if not all_values_available:
        return False, 'Please provide values for all required fields.'

    errors = []
    if len(row['regno']) > REGISTRATION_NUMBER_MAX_LENGTH:
        errors.append('Registration number is more than {} characters long.'.format(REGISTRATION_NUMBER_MAX_LENGTH))

    if len(row['firstname']) > FIRST_NAME_MAX_LENGTH:
        errors.append('First name is more than {} characters long.'.format(FIRST_NAME_MAX_LENGTH))

    if len(row['surname']) > SURNAME_MAX_LENGTH:
        errors.append('Surname is more than {} characters long.'.format(SURNAME_MAX_LENGTH))

    if len(row['othername']) > OTHER_NAME_MAX_LENGTH:
        errors.append('Other name is more than {} characters long.'.format(OTHER_NAME_MAX_LENGTH))

    if len(row['mobile']) > MOBILE_NUMBER_MAX_LENGTH:
        errors.append('Mobile number is more than {} characters long.'.format(MOBILE_NUMBER_MAX_LENGTH))

    try:
        if int(row['levelid']) < 1 or int(row['levelid']) > MAX_LEVEL_CHOICES:
            errors.append('Level ID must be greater than 0 and smaller than {}.'.format(MAX_LEVEL_CHOICES+1))
    except ValueError:
        errors.append('Level ID is not an integer value.')

    try:
        if int(row['programmeid']) < 1 or int(row['programmeid']) > MAX_PROGRAMME_CHOICES:
            errors.append('Programme ID must be greater than 0 and smaller than {}.'.format(MAX_PROGRAMME_CHOICES+1))
    except ValueError:
        errors.append('Programme ID is not an integer value.')

    if errors:
        # to write multiple lines
        # in a single cell of csv
        errors = '"{}"'.format('\n'.join(errors))
        return False, errors

    return True, None
