# Generated by Django 5.0.6 on 2024-12-14 18:58

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat', '0008_alter_chatroommessages_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='category',
            field=models.CharField(default='General', max_length=100),
        ),
        migrations.AlterField(
            model_name='chatroommessages',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 15, 0, 43, 12, 421494)),
        ),
    ]
