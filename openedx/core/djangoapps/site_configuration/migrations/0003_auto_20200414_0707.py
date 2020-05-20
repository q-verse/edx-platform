# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-04-14 09:52
from __future__ import unicode_literals

from django.db import migrations

DEFAULT_EDLY_CLIENT_THEME_CONFIGURATION = {
    "COLORS": {
        "primary": "#3E99D4",
        "secondary": "#3E99D4"
    },
    "FONTS": {
        "base-font": "Open Sans, sans-serif",
        "heading-font": "Open Sans, sans-serif",
        "font-path": "https://fonts.googleapis.com/css?family=Open+Sans&display=swap"
    },
    "BRANDING": {
        "logo": "https://edly-cloud-static-assets.s3.amazonaws.com/default-branding/logo.png",
        "logo-white": "https://edly-cloud-static-assets.s3.amazonaws.com/default-branding/logo-white.png",
        "favicon": "https://edly-cloud-static-assets.s3.amazonaws.com/default-branding/favicon.ico"
    }
}


def populate_default_site_configurations(apps, schema_editor):
    site_configurations = apps.get_model('site_configuration', 'SiteConfiguration')
    for site_configuration in site_configurations.objects.all():
        if not site_configuration.values:
            site_configuration.values = DEFAULT_EDLY_CLIENT_THEME_CONFIGURATION
            site_configuration.save()


class Migration(migrations.Migration):
    dependencies = [
        ('site_configuration', '0002_auto_20160720_0231'),
    ]

    operations = [
        migrations.RunPython(populate_default_site_configurations),
    ]
