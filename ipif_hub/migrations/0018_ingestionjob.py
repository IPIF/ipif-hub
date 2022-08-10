# Generated by Django 3.2.12 on 2022-08-05 10:03

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0017_auto_20220728_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='IngestionJob',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('complete', models.BooleanField(default=False)),
                ('start_datetime', models.DateTimeField(default=datetime.datetime(2022, 8, 5, 10, 3, 59, 347695))),
                ('end_datetime', models.DateTimeField(blank=True, default=None, null=True)),
                ('job_type', models.CharField(choices=[('file batch upload', 'file batch upload')], max_length=20)),
                ('ipif_repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ipif_hub.ipifrepo')),
            ],
        ),
    ]