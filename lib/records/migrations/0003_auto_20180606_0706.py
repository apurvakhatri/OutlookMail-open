# Generated by Django 2.0.5 on 2018-06-06 07:06

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0002_yellowusertoken_subscription_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='yellowusertoken',
            name='outlook_refresh_token',
            field=models.CharField(default=1, max_length=2048),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='yellowusertoken',
            name='token_update',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
    ]
