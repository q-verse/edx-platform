"""
Validation utils for qverse registration application.
"""
from csv import reader, Sniffer
import io

from django.core.exceptions import ValidationError


def validate_admission_file(file):
    """
    Validates that the file is a valid csv file by checking its extension.
    Also checks that the header row has all the required fields.

    Arguments:
        file (models.FileField): The file uploaded by the user
    """
    if not file.name.endswith('.csv'):
        raise ValidationError('', code='invalid')

    FIELD_NAMES = [
                'regno', 'firstname', 'surname', 'othername', 'levelid',
                'programmeid', 'departmentid', 'mobile', 'email'
                ]
    decoded_file = file.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    header_row = []
    try:
        dialect = Sniffer().sniff(io_string.readline())
        io_string.seek(0)
        header_row = reader(io_string, delimiter=dialect.delimiter).next()
        header_row = [heading.lower().strip() for heading in header_row]
    except StopIteration:
        raise ValidationError('', code='invalid')

    if not all(field_name in header_row for field_name in FIELD_NAMES):
        raise ValidationError('', code='invalid')

    if 'error' in header_row:
        header_row.remove('error')

    if 'status' in header_row:
        header_row.remove('status')

    if len(header_row) != len(FIELD_NAMES):
        raise ValidationError('', code='invalid')


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
