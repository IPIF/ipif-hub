# Generated by Django 3.2.12 on 2022-06-15 12:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0007_rename_endpoint_url_ipifrepo_endpoint_uri'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ipifrepo',
            name='ids_are_local',
        ),
    ]
