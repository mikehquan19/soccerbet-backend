# Generated by Django 5.1.2 on 2025-01-22 00:03

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0012_alter_comment_created_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='created_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2025, 1, 22, 0, 3, 27, 555459, tzinfo=datetime.timezone.utc)),
        ),
    ]
