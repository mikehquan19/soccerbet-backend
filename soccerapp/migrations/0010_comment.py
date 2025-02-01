# Generated by Django 5.1.2 on 2025-01-19 07:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0009_rename_totalgoalsbetinfo_totalobjectsbetinfo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField()),
                ('content', models.TextField()),
                ('replyToUsername', models.CharField(default='', max_length=150)),
                ('likes', models.ManyToManyField(blank=True, related_name='like_users', to='soccerapp.user')),
                ('replyToComment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='soccerapp.comment')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.team')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.user')),
            ],
            options={
                'ordering': ['team', 'created_time'],
            },
        ),
    ]
