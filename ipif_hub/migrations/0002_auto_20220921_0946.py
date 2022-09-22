# Generated by Django 3.2.15 on 2022-09-21 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipif_hub', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='uris',
            field=models.ManyToManyField(blank=True, related_name='persons', to='ipif_hub.URI'),
        ),
        migrations.AlterField(
            model_name='source',
            name='uris',
            field=models.ManyToManyField(blank=True, related_name='sources', to='ipif_hub.URI'),
        ),
    ]