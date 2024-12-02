# Generated by Django 5.0.6 on 2024-12-03 14:12

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat', '0005_alter_chatroom_online_users_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatroom',
            name='online_users',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AlterField(
            model_name='chatroommessages',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 3, 19, 57, 37, 19167)),
        ),
    ]
