"""
Unit tests for QVerse registration app models.
"""
import mock
import os

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase

from openedx.features.qverse_features.registration.models import BulkUserRegistration, QVerseUserProfile
from openedx.features.qverse_features.registration.tests.factories import DepartmentFactory, QVerseUserProfileFactory
from student.models import UserProfile


class BulkUserRegistrationTests(TestCase):
    """
    Tests for BulkUserRegistration model.
    """
    def setUp(self):
        self.file_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
        DepartmentFactory(number=1)

    @mock.patch(
        'openedx.features.qverse_features.registration.signals.get_current_site',
        autospec=True
    )
    @mock.patch(
        'openedx.features.qverse_features.registration.signals.send_bulk_mail_to_newly_created_students.delay',
        autospec=True
    )
    def test_bulk_user_registration_with_valid_admission_file(self, mocked_mail, mocked_site):
        file_path = os.path.join(self.file_directory, 'admission_file.csv')
        with open(file_path, 'r') as admission_file:
            BulkUserRegistration.objects.create(admission_file=ContentFile(admission_file.read(), 'admission_file.csv'),
                                                description='Testing Batch')

            self.assertEqual(User.objects.all().count(), 2)
            self.assertEqual(UserProfile.objects.all().count(), 2)
            self.assertEqual(QVerseUserProfile.objects.all().count(), 2)
            self.assertTrue(mocked_site.called)
            self.assertTrue(mocked_mail.called)
            self.assertEqual(str(BulkUserRegistration.objects.first()), 'Testing Batch')


class DepartmentTests(TestCase):
    """
    Tests for Department model.
    """
    def setUp(self):
        self.department = DepartmentFactory(number=1, name='Demo Department')

    def test_department_string_representation(self):
        self.assertEqual(str(self.department), '1: Demo Department')


class QVerseUserProfileTests(TestCase):
    """
    Tests for QVerseUserProfile Model.
    """
    def setUp(self):
        self.qverse_profile = QVerseUserProfileFactory()

    def test_qverse_user_profile_string_representation(self):
        self.assertEqual(str(self.qverse_profile), '(ROBOT0) --- Robot0 Test')
