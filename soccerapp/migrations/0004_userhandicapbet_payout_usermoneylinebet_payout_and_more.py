# Generated by Django 5.1.2 on 2024-12-15 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soccerapp', '0003_alter_match_options_userhandicapbet_created_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userhandicapbet',
            name='payout',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='usermoneylinebet',
            name='payout',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='usertotalgoalsbet',
            name='payout',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
