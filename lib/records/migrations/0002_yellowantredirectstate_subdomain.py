# Generated by Django 2.0.5 on 2018-06-11 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='yellowantredirectstate',
            name='subdomain',
            field=models.CharField(default='devacc', max_length=128),
            preserve_default=False,
        ),
    ]