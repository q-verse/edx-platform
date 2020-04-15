"""
Register qverse registration app models for django admin.
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from openedx.features.qverse_features.registration.models import (AdmissionData,
                                                                  Department,
                                                                  QVerseUserProfile,
                                                                  ProspectiveUser)


admin.site.register(AdmissionData)
admin.site.register(Department)
admin.site.register(QVerseUserProfile)
admin.site.register(ProspectiveUser)
