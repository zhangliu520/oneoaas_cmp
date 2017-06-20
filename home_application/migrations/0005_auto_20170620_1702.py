# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home_application', '0004_auto_20170620_1701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vcentervirtualmachine',
            name='guest',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='vcentervirtualmachine',
            name='guest_fullname',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='vcentervirtualmachine',
            name='ipaddress',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterField(
            model_name='vcentervirtualmachine',
            name='power_state',
            field=models.CharField(max_length=50),
        ),
    ]
