# Generated by Django 3.2.12 on 2022-06-29 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0013_auto_20220629_0815'),
    ]

    operations = [
        migrations.AddField(
            model_name='ipifrepo',
            name='primary_email',
            field=models.EmailField(default='made_up@none.net', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ipifrepo',
            name='secondary_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='ipifrepo',
            name='tertiary_email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]
