# Generated by Django 5.0.6 on 2024-12-07 10:14

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Chat', '0006_alter_chatroommessages_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatroommessages',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2024, 12, 7, 15, 59, 14, 154577)),
        ),
    ]
