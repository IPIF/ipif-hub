# Generated by Django 3.2.12 on 2022-08-05 10:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0022_rename_complete_ingestionjob_is_complete'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingestionjob',
            name='job_output',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='ingestionjob',
            name='job_status',
            field=models.CharField(default='running', max_length=20),
        ),
    ]
