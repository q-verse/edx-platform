"""
Qverse registration application forms.
"""
from django.forms import ModelForm

from openedx.features.qverse_features.registration.models import QVerseUserProfile


class QVerseUserProfileForm(ModelForm):
    """
    Form to add custom registration fields.
    """
    class Meta(object):
        model = QVerseUserProfile
        fields = ('registration_number', 'other_name', 'mobile_number', 'current_level',
                  'programme', 'department')
        # edx has field descriptions for default model fields
        # like Text, Select e.t.c but here our field is ForeignKey
        # so we have to give its descriptions separately.
        serialization_options = {
            'department': {
                'field_type': 'select'
            }
        }
