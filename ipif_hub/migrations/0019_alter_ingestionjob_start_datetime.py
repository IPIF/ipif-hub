# Generated by Django 3.2.12 on 2022-08-05 10:04

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0018_ingestionjob'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingestionjob',
            name='start_datetime',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]