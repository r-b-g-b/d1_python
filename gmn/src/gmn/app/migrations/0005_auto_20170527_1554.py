# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-27 15:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20170523_0137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='localreplica',
            name='pid',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='localreplica_pid', to='app.IdNamespace'),
        ),
    ]
