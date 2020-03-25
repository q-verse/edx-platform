"""
Django models for qverse registration app.
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_noop

from openedx.features.qverse_features.registration.validators import (validate_admission_file,
                                                                      validate_current_level,
                                                                      validate_programme_choices)


# explicitly saving lengths of these generators
# as these would be used in validtors.py for
# validations. As these are the generators they would
# be exhausted after single use, so we couldn't get their
# length in validators.py
MAX_PROGRAMME_CHOICES = 6
PROGRAMME_CHOICES = (
    (1, ugettext_noop('Undergraduate Studies')),
    (2, ugettext_noop('Postgraduate Studies')),
    (3, ugettext_noop('Matured Student Programme (MSP)')),
    (4, ugettext_noop('Diploma')),
    (5, ugettext_noop('Pre-Science')),
    (6, ugettext_noop('Sandwish')),
)
MAX_LEVEL_CHOICES = 9
LEVEL_CHOICES = ((i, ugettext_noop('Year ' + str(i))) for i in range(1, MAX_LEVEL_CHOICES + 1))
APP_LABEL = 'registration'


class BulkUserRegistration(models.Model):
    """
    Saves csv records for bulk user registration.
    """
    admission_file = models.FileField(
        upload_to='qverse_registration_csvs/',
        blank=False,
        null=True,
        validators=[validate_admission_file]
    )
    description = models.CharField(max_length=100, blank=False, null=True)

    class Meta(object):
        app_label = APP_LABEL

    def __str__(self):
        return self.description


class Department(models.Model):
    """
    Represents educational departments.
    """
    number = models.IntegerField(unique=True, validators=[MinValueValidator(1)])
    name = models.CharField(unique=True, max_length=50)

    class Meta(object):
        app_label = APP_LABEL

    def save(self, *args, **kwargs):
        """
        Make sure that all the department names are saved in db in title case.

        This would help us to ensure unique constraint.
        """
        self.name = self.name.title()
        return super(Department, self).save(*args, **kwargs)

    def __str__(self):
        return '{}: {}'.format(self.number, self.name)


class QVerseUserProfile(models.Model):
    """
    Represents qverse user profile.

    This model is also used to add custom registration fields.
    """
    class Meta:
        app_label = APP_LABEL
        verbose_name_plural = 'Qverse User Profiles'

    user = models.OneToOneField(User, unique=True, db_index=True,
                                related_name='qverse_profile', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, db_index=True, null=True, on_delete=models.SET_NULL)
    registration_number = models.CharField(unique=True, max_length=30, db_index=True)
    other_name = models.CharField(blank=True, max_length=50)
    mobile_number = models.CharField(blank=True, max_length=20)
    current_level = models.IntegerField(choices=LEVEL_CHOICES,
                                        validators=[validate_current_level, MaxValueValidator(99)])
    programme = models.IntegerField(db_index=True, choices=PROGRAMME_CHOICES, validators=[validate_programme_choices])

    def save(self, *args, **kwargs):
        """
        Make sure that all the registration numbers are saved in db in upper case.

        This would help us to ensure unique constraint of registration number.
        """
        self.registration_number = self.registration_number.title()
        return super(QVerseUserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return '({}) --- {}'.format(self.registration_number, self.user.profile.name)
