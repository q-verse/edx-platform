"""
Factories for QVerse registration app unit tests.
"""
import factory
import factory.fuzzy
import string

from openedx.features.qverse_features.registration.models import (Department, QVerseUserProfile, ProspectiveUser,
                                                                  MAX_LEVEL_CHOICES, MAX_PROGRAMME_CHOICES)
from student.tests.factories import UserFactory


class DepartmentFactory(factory.django.DjangoModelFactory):
    """
    Creates department.
    """
    class Meta(object):
        model = Department
        django_get_or_create = ('name', 'number', )

    name = factory.Sequence(u'Department_{0}'.format)
    number = factory.Sequence(int)


class QVerseUserProfileFactory(factory.django.DjangoModelFactory):
    """
    Creates QVerseUserProfile.
    """
    class Meta(object):
        model = QVerseUserProfile
        django_get_or_create = ('user', 'registration_number', )

    user = factory.SubFactory(UserFactory)
    department = factory.SubFactory(DepartmentFactory)
    registration_number = factory.LazyAttribute(u'{0.user.username}'.format)
    other_name = factory.Sequence(u'robot-{0}'.format)
    mobile_number = factory.fuzzy.FuzzyText(length=11, chars=string.digits)
    current_level = factory.fuzzy.FuzzyInteger(1, MAX_LEVEL_CHOICES)
    programme = factory.fuzzy.FuzzyInteger(1, MAX_PROGRAMME_CHOICES)


class ProspectiveUserFactory(factory.django.DjangoModelFactory):
    """
    Creates ProspectiveUser.
    """
    class Meta(object):
        model = ProspectiveUser
        django_get_or_create = ('registration_number', )

    registration_number = factory.Sequence(u'{0}'.format)
    email = factory.Sequence(u'robot+test+{0}@edx.org'.format)
    department = factory.SubFactory(DepartmentFactory)
    first_name = factory.Sequence(u'robot-first-name-{0}'.format)
    surname = factory.Sequence(u'robot-surname-{0}'.format)
    other_name = factory.Sequence(u'robot-other-name-{0}'.format)
    mobile_number = factory.fuzzy.FuzzyText(length=11, chars=string.digits)
    current_level = factory.fuzzy.FuzzyInteger(1, MAX_LEVEL_CHOICES)
    programme = factory.fuzzy.FuzzyInteger(1, MAX_PROGRAMME_CHOICES)
