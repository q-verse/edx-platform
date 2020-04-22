"""
Unit tests QVerse registration app forms.
"""
from ddt import ddt, data, unpack

from django.test import SimpleTestCase

from openedx.features.qverse_features.registration.forms import QVerseUserProfileForm


@ddt
class QVerseUserProfileFormTests(SimpleTestCase):

    def setUp(self):
        self.form = QVerseUserProfileForm()

    @data(
        ('first_name', 'Enter your first name.'),
        ('surname', 'Enter your surname.'),
        ('registration_number', 'Enter your registration number provided from your school.'),
        ('other_name', 'Enter your nick name.'),
        ('mobile_number', 'Enter your mobile number.'),
        ('current_level', 'Select your current level in school during admission.'),
        ('programme', 'Select the programme that you have been enrolled in.'),
        ('department', 'Select your department.')
    )
    @unpack
    def test_form_help_texts(self, field_name, help_text):
        self.assertEqual(self.form.fields[field_name].help_text, help_text)

    @data(
        ('first_name', 'Please enter your First Name.'),
        ('surname', 'Please enter your Surname.'),
        ('registration_number', 'Please enter your Registration Number.'),
        ('current_level', 'Please select a valid Current Level.'),
        ('programme', 'Please select the valid Programme that you have been enrolled in.'),
        ('department', 'Please select a valid Department'),
    )
    @unpack
    def test_form_error_messages_for_required_fields(self, field_name, error_message):
        self.assertEqual(self.form.fields[field_name].error_messages['required'], error_message)
