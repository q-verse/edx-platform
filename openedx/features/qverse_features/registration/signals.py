from __future__ import print_function
from collections import namedtuple

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from openedx.features.qverse_features.registration.models import BulkUserRegistration

UserInfo = namedtuple('UserInfo',
                      ['username', 'email','first_name', 'last_name',
                       'other_name', 'mobile_number', 'level',
                       'programme_and_department']
                     )


@receiver(post_save, sender=BulkUserRegistration)
def make_users_from_csv_file(sender, instance, created, **kwargs):
    # TODO: this would be implemented later once the basic architecture is final.
    pass
