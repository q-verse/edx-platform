"""
Unit tests for QVerse registration app models.
"""
import os

from django.core.files.base import ContentFile
from django.test import TestCase

from openedx.features.qverse_features.registration.models import AdmissionData, ProspectiveUser
from openedx.features.qverse_features.registration.tests.factories import (DepartmentFactory,
                                                                           QVerseUserProfileFactory,
                                                                           ProspectiveUserFactory)


class AdmissionDataTests(TestCase):
    """
    Tests for AdmissionData model.
    """
    def setUp(self):
        self.file_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
        DepartmentFactory(number=1)

    def test_bulk_user_registration_with_valid_admission_file(self):
        file_path = os.path.join(self.file_directory, 'admission_file.csv')
        with open(file_path, 'r') as admission_file:
            AdmissionData.objects.create(admission_file=ContentFile(admission_file.read(), 'admission_file.csv'),
                                         description='Testing Batch')

            self.assertEqual(ProspectiveUser.objects.all().count(), 2)
            self.assertEqual(str(AdmissionData.objects.first()), 'Testing Batch')


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
        self.prospective_user = ProspectiveUserFactory()
        self.qverse_profile = QVerseUserProfileFactory(registration_number=self.prospective_user.registration_number)

    def test_qverse_user_profile_string_representation(self):
        self.assertEqual(str(self.qverse_profile), '(0) --- Robot0 Test')


class ProspectiveUserTests(TestCase):
    """
    Tests for ProspectiveUser Model.
    """
    def setUp(self):
        self.prospective_user = ProspectiveUserFactory()

    def test_prospective_user_string_representation(self):
        self.assertEqual(str(self.prospective_user), '(1) --- robot-first-name-1 robot-surname-1')
