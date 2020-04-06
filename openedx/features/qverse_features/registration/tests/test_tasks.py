"""
Tests for QVerse registration app tasks.
"""
import mock

from django.test import TestCase

from openedx.features.qverse_features.registration.tasks import send_bulk_mail_to_newly_created_students
from student.tests.factories import UserFactory


class RegistrationTasksTests(TestCase):
    """
    Tests for registration tasks.
    """
    @mock.patch(
        'openedx.features.qverse_features.registration.tasks.ace.send',
        autospec=True
    )
    def test_send_bulk_mail_to_newly_created_students(self, mocked_mail):
        student_count = 4
        new_students = [{'regno': UserFactory().username} for i in range(1, student_count+1)]
        send_bulk_mail_to_newly_created_students(new_students, 1)
        self.assertEqual(mocked_mail.call_count, student_count)
