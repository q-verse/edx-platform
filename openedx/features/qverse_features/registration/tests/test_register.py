"""
Tests for account creation.
"""
from ddt import ddt, data, unpack

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from openedx.features.qverse_features.registration.models import QVerseUserProfile, ProspectiveUser
from openedx.features.qverse_features.registration.tests.factories import DepartmentFactory, ProspectiveUserFactory

from student.models import UserProfile

OVERRIDDEN_FEATURES = settings.FEATURES.copy()
OVERRIDDEN_FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION'] = True


@ddt
@override_settings(
    REGISTRATION_EXTENSION_FORM='openedx.features.qverse_features.registration.forms.QVerseUserProfileForm',
    FEATURES=OVERRIDDEN_FEATURES
)
class CreateAccountTests(TestCase):
    """
    Tests for account creation.
    """
    def setUp(self):
        super(CreateAccountTests, self).setUp()
        self.department = DepartmentFactory(__sequence=1)
        self.prospective_user = ProspectiveUserFactory(department=self.department, current_level=1, programme=1)

        self.url = reverse('create_account')
        self.params = {
            'username': 'test_user',
            'email': self.prospective_user.email,
            'password': u'testpass',
            'first_name': self.prospective_user.first_name,
            'surname': self.prospective_user.surname,
            'honor_code': 'true',
            'terms_of_service': 'true',
            'registration_number': self.prospective_user.registration_number,
            'current_level': self.prospective_user.current_level,
            'programme': self.prospective_user.programme,
            'department': self.prospective_user.department.number,
            'other_name': self.prospective_user.other_name,
            'mobile_number': self.prospective_user.mobile_number
        }

    def test_create_user_with_all_required_valid_fields(self):
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username=self.params['username'])
        edx_user_profile = UserProfile.objects.get(user=user)
        qverse_user_profile = QVerseUserProfile.objects.get(user=user)

        name = '{} {}'.format(self.prospective_user.first_name, self.prospective_user.surname)
        self.assertEqual(edx_user_profile.name, name)
        self.assertEqual(qverse_user_profile.registration_number, self.params['registration_number'].upper())
        self.assertEqual(qverse_user_profile.current_level, self.params['current_level'])
        self.assertEqual(qverse_user_profile.programme, self.params['programme'])
        self.assertEqual(qverse_user_profile.department.number, self.params['department'])
        self.assertEqual(qverse_user_profile.other_name, self.params['other_name'])
        self.assertEqual(qverse_user_profile.mobile_number, self.params['mobile_number'])
        self.assertEqual(ProspectiveUser.objects.all().count(), 0)

    @data(
        ({'registration_number': 'DEMO123'}, 'You are not authorized to register.'),
        ({'programme': 2}, 'Your programme doesn\'t match with the programme included in the admission data.'),
        ({'programme': 2}, 'Your programme doesn\'t match with the programme included in the admission data.'),
        ({'first_name': 1}, 'Your first name doesn\'t match with the first name included in the admission data.'),
        ({'surname': 1}, 'Your surname doesn\'t match with the surname included in the admission data.'),
        ({'current_level': 2}, ('Your current level doesn\'t match with the '
                                'current level included in the admission data.')),
    )
    @unpack
    def test_create_user_with_invalid_unmatched_data_for_required_fields(self, invalid_params, error_message):
        """
        Test that if the required registration data doesn't match
        with the data stored for prospective users, an appropriate
        message should be sent.
        """
        self.params.update(invalid_params)
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['value'], error_message)
        self.assertEqual(User.objects.all().count(), 0)
        self.assertEqual(UserProfile.objects.all().count(), 0)
        self.assertEqual(QVerseUserProfile.objects.all().count(), 0)
