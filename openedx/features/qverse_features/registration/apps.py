"""
Qverse registration application configuration.
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class RegistrationConfig(AppConfig):
    """
    Configuration class for openedx.features.qverse_features.registrations Django application.
    """
    name = 'openedx.features.qverse_features.registration'

    def ready(self):
        """
        Registers signal handlers at startup.
        """
        super(RegistrationConfig, self).ready()
        from openedx.features.qverse_features.registration import signals
