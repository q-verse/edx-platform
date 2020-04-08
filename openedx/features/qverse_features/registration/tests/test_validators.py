"""
Tests for QVerse registration models validators.
"""
from ddt import ddt, data
import os

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from openedx.features.qverse_features.registration.models import MAX_LEVEL_CHOICES, MAX_PROGRAMME_CHOICES
from openedx.features.qverse_features.registration.validators import (validate_admission_file,
                                                                      validate_current_level,
                                                                      validate_programme_choices)


@ddt
class RegistrationValidatorsTests(SimpleTestCase):
    """
    Tests for registration validators.
    """
    def test_registration_admission_file_having_valid_data(self):
        validation_error_raised = False
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/admission_file.csv')
        with open(file_path, 'r') as admission_file:
            try:
                validate_admission_file(admission_file)
            except ValidationError:
                validation_error_raised = True

        self.assertFalse(validation_error_raised)

    def test_registration_admission_file_having_invalid_data(self):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/invalid_admission_file.csv')
        with open(file_path, 'r') as invalid_admission_file:
            self.assertRaises(ValidationError, validate_admission_file, invalid_admission_file)

    @data(
        1, MAX_LEVEL_CHOICES
    )
    def test_validate_current_level_with_valid_values(self, current_level):
        validation_error_raised = False
        try:
            validate_current_level(current_level)
        except ValidationError:
            validation_error_raised = True

        self.assertFalse(validation_error_raised)

    @data(
        0, MAX_LEVEL_CHOICES + 1
    )
    def test_validate_current_level_with_invalid_values(self, current_level):
        self.assertRaises(ValidationError, validate_current_level, current_level)

    @data(
        1, MAX_PROGRAMME_CHOICES
    )
    def test_validate_programme_choices_with_valid_values(self, programme_choice):
        validation_error_raised = False
        try:
            validate_programme_choices(programme_choice)
        except ValidationError:
            validation_error_raised = True

        self.assertFalse(validation_error_raised)

    @data(
        0, MAX_PROGRAMME_CHOICES + 1
    )
    def test_validate_programme_choices_with_invalid_values(self, programme_choice):
        self.assertRaises(ValidationError, validate_programme_choices, programme_choice)
