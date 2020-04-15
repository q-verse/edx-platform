"""
Qverse registration application forms.
"""
from django.forms import ModelForm

from openedx.features.qverse_features.registration.models import QVerseUserProfile, ProspectiveUser
from student.helpers import AccountValidationError


class QVerseUserProfileForm(ModelForm):
    """
    Form to add custom registration fields.
    """
    class Meta(object):
        model = QVerseUserProfile
        fields = ('first_name', 'surname', 'registration_number', 'other_name', 'mobile_number', 'current_level',
                  'programme', 'department')
        # edx has field descriptions for default model fields
        # like Text, Select e.t.c but here our field is ForeignKey
        # so we have to give its descriptions separately.
        serialization_options = {
            'department': {
                'field_type': 'select'
            }
        }
        error_messages = {
            'registration_number': {
                'required': 'Please enter your Registration Number.',
            },
            'first_name': {
                'required': 'Please enter your First Name.',
            },
            'surname': {
                'required': 'Please enter your Surname.',
            },
            'current_level': {
                'required': 'Please select a valid Current Level.'
            },
            'department': {
                'required': 'Please select a valid Department'
            },
            'programme': {
                'required': 'Please select the valid Programme that you have been enrolled in.'
            },
        }
        help_texts = {
            'registration_number': 'Enter your registration number provided from your school.',
            'first_name': 'Enter your first name.',
            'surname': 'Enter your surname.',
            'other_name': 'Enter your nick name.',
            'current_level': 'Select your current level in school during admission.',
            'mobile_number': 'Enter your mobile number.',
            'department': 'Select your department.',
            'programme': 'Select the programme that you have been enrolled in.',
        }

    def clean(self):
        """
        Validates that incoming user is a prospective user or not.

        If optional fields of incoming user don't match with the admission data
        we can ignore that. But the required fields of incoming user must match
        with the admission data.
        """
        cleaned_data = super(QVerseUserProfileForm, self).clean()
        try:
            OPTIONAL_FIELDS = ['mobile_number', 'other_name']
            prospective_user = ProspectiveUser.objects.get(
                    registration_number__iexact=cleaned_data['registration_number'])
            for field_name in cleaned_data.keys():
                if field_name in OPTIONAL_FIELDS:
                    continue
                if str(getattr(prospective_user, field_name)).lower() != str(cleaned_data[field_name]).lower():
                    field_name = field_name.replace('_', ' ')
                    error_message = ('Your {0} doesn\'t match with the {0} included '
                                     'in the admission data.').format(field_name)
                    raise AccountValidationError(error_message, field=field_name)
        except ProspectiveUser.DoesNotExist:
            raise AccountValidationError('You are not authorized to register.', field='registration_number')
