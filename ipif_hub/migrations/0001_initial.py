# Generated by Django 3.2.12 on 2022-03-15 16:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IpifRepo',
            fields=[
                ('id', models.CharField(max_length=300, primary_key=True, serialize=False, unique=True)),
                ('uri', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.CharField(max_length=300, primary_key=True, serialize=False)),
                ('createdBy', models.CharField(max_length=300)),
                ('createdWhen', models.DateField()),
                ('modifiedBy', models.CharField(max_length=300)),
                ('modifiedWhen', models.DateField()),
                ('hubIngestedWhen', models.DateTimeField(auto_now_add=True)),
                ('hubModifiedWhen', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(default='', max_length=300)),
                ('ipif_repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ipif_hub.ipifrepo', verbose_name='IPIF Repository')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('uri', models.URLField(primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=300, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='URI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.CharField(max_length=300, primary_key=True, serialize=False)),
                ('createdBy', models.CharField(max_length=300)),
                ('createdWhen', models.DateField()),
                ('modifiedBy', models.CharField(max_length=300)),
                ('modifiedWhen', models.DateField()),
                ('hubIngestedWhen', models.DateTimeField(auto_now_add=True)),
                ('hubModifiedWhen', models.DateTimeField(auto_now=True)),
                ('statementType_uri', models.URLField(blank=True, null=True)),
                ('statementType_label', models.CharField(blank=True, max_length=300, null=True)),
                ('name', models.CharField(blank=True, max_length=300, null=True)),
                ('role_uri', models.URLField(blank=True, null=True)),
                ('role_label', models.CharField(blank=True, max_length=300, null=True)),
                ('date_sortdate', models.DateField(blank=True, null=True)),
                ('date_label', models.CharField(blank=True, max_length=100, null=True)),
                ('memberOf_uri', models.URLField(blank=True, null=True)),
                ('memberOf_label', models.CharField(blank=True, max_length=300, null=True)),
                ('statementText', models.CharField(blank=True, max_length=1000, null=True)),
                ('ipif_repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ipif_hub.ipifrepo', verbose_name='IPIF Repository')),
                ('places', models.ManyToManyField(blank=True, to='ipif_hub.Place')),
                ('relatesToPerson', models.ManyToManyField(blank=True, to='ipif_hub.Person', verbose_name='relatedToPerson')),
            ],
            options={
                'abstract': False,
                'unique_together': {('id', 'ipif_repo')},
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.CharField(max_length=300, primary_key=True, serialize=False)),
                ('createdBy', models.CharField(max_length=300)),
                ('createdWhen', models.DateField()),
                ('modifiedBy', models.CharField(max_length=300)),
                ('modifiedWhen', models.DateField()),
                ('hubIngestedWhen', models.DateTimeField(auto_now_add=True)),
                ('hubModifiedWhen', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(default='', max_length=300)),
                ('ipif_repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ipif_hub.ipifrepo', verbose_name='IPIF Repository')),
                ('uris', models.ManyToManyField(blank=True, to='ipif_hub.URI')),
            ],
            options={
                'abstract': False,
                'unique_together': {('id', 'ipif_repo')},
            },
        ),
        migrations.AddField(
            model_name='person',
            name='uris',
            field=models.ManyToManyField(blank=True, to='ipif_hub.URI'),
        ),
        migrations.AlterUniqueTogether(
            name='person',
            unique_together={('id', 'ipif_repo')},
        ),
        migrations.CreateModel(
            name='Factoid',
            fields=[
                ('id', models.CharField(max_length=300, primary_key=True, serialize=False)),
                ('createdBy', models.CharField(max_length=300)),
                ('createdWhen', models.DateField()),
                ('modifiedBy', models.CharField(max_length=300)),
                ('modifiedWhen', models.DateField()),
                ('hubIngestedWhen', models.DateTimeField(auto_now_add=True)),
                ('hubModifiedWhen', models.DateTimeField(auto_now=True)),
                ('ipif_repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ipif_hub.ipifrepo', verbose_name='IPIF Repository')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factoids', related_query_name='factoids', to='ipif_hub.person')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factoids', related_query_name='factoids', to='ipif_hub.source')),
                ('statement', models.ManyToManyField(related_name='factoid', related_query_name='factoid', to='ipif_hub.Statement', verbose_name='statements')),
            ],
            options={
                'abstract': False,
                'unique_together': {('id', 'ipif_repo')},
            },
        ),
    ]
