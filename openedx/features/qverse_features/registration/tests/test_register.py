"""
Tests for account creation.
"""
from ddt import ddt, data

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from openedx.features.qverse_features.registration.models import (QVerseUserProfile,
                                                                  MAX_LEVEL_CHOICES,
                                                                  MAX_PROGRAMME_CHOICES)
from openedx.features.qverse_features.registration.tests.factories import DepartmentFactory

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
        DepartmentFactory(number=1)
        self.username = 'test_user'
        self.url = reverse('create_account')
        self.params = {
            'username': self.username,
            'email': 'test@example.org',
            'password': u'testpass',
            'name': 'Test User',
            'honor_code': 'true',
            'terms_of_service': 'true',
            'registration_number': self.username,
            'current_level': 1,
            'programme': 2,
            'department': 1,
            'other_name': 'tester',
            'mobile_number': '090078601'
        }

    def test_create_user_with_all_required_valid_fields(self):
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username=self.username)
        edx_user_profile = UserProfile.objects.get(user=user)
        qverse_user_profile = QVerseUserProfile.objects.get(user=user)

        self.assertEqual(edx_user_profile.name, self.params['name'])
        self.assertEqual(qverse_user_profile.registration_number, self.params['registration_number'].upper())
        self.assertEqual(qverse_user_profile.current_level, self.params['current_level'])
        self.assertEqual(qverse_user_profile.programme, self.params['programme'])
        self.assertEqual(qverse_user_profile.department.number, self.params['department'])
        self.assertEqual(qverse_user_profile.other_name, self.params['other_name'])
        self.assertEqual(qverse_user_profile.mobile_number, self.params['mobile_number'])

    @data(
        {'current_level': 0, 'programme': 2, 'department': 1},
        {'current_level': MAX_LEVEL_CHOICES+1, 'programme': 2, 'department': 1},
        {'current_level': 1, 'programme': 0, 'department': 1},
        {'current_level': 1, 'programme': MAX_PROGRAMME_CHOICES+1, 'department': 1},
        {'current_level': 1, 'programme': 2, 'department': 3},
    )
    def test_create_user_with_invalid_fields(self, invalid_params):
        self.params.update(invalid_params)
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.all().count(), 0)
        self.assertEqual(UserProfile.objects.all().count(), 0)
        self.assertEqual(QVerseUserProfile.objects.all().count(), 0)
