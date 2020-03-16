"""
Validation utils for qverse registration application.
"""
from django.core.exceptions import ValidationError


def validate_file_extension(file):
    """
    Validates that file is a valid csv file by checking its extension.
    """
    if not file.name.endswith('.csv'):
        raise ValidationError('', code='invalid')


def validate_current_level(value):
    """
    Validates the provided current level.
    """
    # to avoid circular import
    from openedx.features.qverse_features.registration.models import MAX_LEVEL_CHOICES

    if not 1 <= value <= MAX_LEVEL_CHOICES:
        raise ValidationError('', code='invalid')


def validate_programme_choices(value):
    """
    Validates the provided programme choice.
    """
    # to avoid circular import
    from openedx.features.qverse_features.registration.models import MAX_PROGRAMME_CHOICES

    if not 1 <= value <= MAX_PROGRAMME_CHOICES:
        raise ValidationError('', code='invalid')
