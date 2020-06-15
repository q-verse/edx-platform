"""
Validation utils for qverse registration application.
"""
from csv import Error

from django.core.exceptions import ValidationError

from openedx.features.qverse_features.registration.helpers import get_file_header_row


def validate_admission_file(file):
    """
    Validates that the file is a valid csv file by checking its extension.
    Also checks that the header row has all the required fields.

    Arguments:
        file (models.FileField): The file uploaded by the user
    """
    if not file.name.endswith('.csv'):
        raise ValidationError('Invalid file format. Only csv files are supported.')

    FIELD_NAMES = [
                'regno', 'firstname', 'surname', 'othername', 'levelid',
                'programmeid', 'departmentid', 'mobile', 'email'
                ]
    try:
        file_content = file.read()
        try:
            header_row = get_file_header_row(file_content, 'utf-8')
        except Error:
            header_row = get_file_header_row(file_content, 'utf-16')

    except Exception:
        raise ValidationError('Invalid file encoding format. Only utf-8 and utf-16 file encoding formats are supported.')

    if not all([field_name in header_row for field_name in FIELD_NAMES]):
        raise ValidationError('Invalid content. Required columns are missing.')

    if 'error' in header_row:
        header_row.remove('error')

    if 'status' in header_row:
        header_row.remove('status')

    if len(header_row) != len(FIELD_NAMES):
        raise ValidationError('Invalid content. Remove extra columns.')


def validate_current_level(value):
    """
    Validates the provided current level.

    Arguments:
        value (int): Current educational year at school
    """
    # to avoid circular import
    from openedx.features.qverse_features.registration.models import MAX_LEVEL_CHOICES

    if value < 1 or value > MAX_LEVEL_CHOICES:
        raise ValidationError('', code='invalid')


def validate_programme_choices(value):
    """
    Validates the provided programme choice.

    Arguments:
        value (int): Number representing one of the programme offered by the school
    """
    # to avoid circular import
    from openedx.features.qverse_features.registration.models import MAX_PROGRAMME_CHOICES

    if value < 1 or value > MAX_PROGRAMME_CHOICES:
        raise ValidationError('', code='invalid')
