# Generated by Django 3.2.12 on 2022-07-28 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0016_auto_20220629_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipifrepo',
            name='batch_is_canonical',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='ipifrepo',
            name='rest_write_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
