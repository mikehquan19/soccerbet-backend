# Generated by Django 5.1.1 on 2024-10-11 18:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('league', models.CharField(choices=[('Champions League', 'UCL'), ('Premiere League', 'EPL'), ('La Liga', 'LAL'), ('Bundesliga', 'BUN')], max_length=100)),
                ('match_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('date', models.DateTimeField(verbose_name='The time the match begins')),
                ('home_team', models.CharField(max_length=250)),
                ('home_team_logo', models.URLField(blank=True, null=True)),
                ('away_team', models.CharField(max_length=250)),
                ('away_team_logo', models.URLField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Not Finished', 'NF'), ('Finished', 'FN')], default='Not Finished', max_length=50)),
                ('updated_date', models.DateField(blank=True, null=True, verbose_name="The date the match's status is updated")),
                ('halftime_score', models.CharField(blank=True, max_length=10, null=True)),
                ('fulltime_score', models.CharField(blank=True, max_length=10, null=True)),
                ('penalty', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('league', models.CharField(choices=[('Premiere League', 'EPL'), ('La Liga', 'LAL'), ('Bundesliga', 'BUN')], default='Premiere League', max_length=100)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('nickname', models.CharField(blank=True, max_length=150, null=True)),
                ('logo', models.URLField(blank=True, null=True, verbose_name='logo of the team')),
                ('founded_year', models.IntegerField(verbose_name='The year the team was founded')),
                ('home_stadium', models.CharField(max_length=150)),
                ('stadium_image', models.URLField(blank=True, null=True, verbose_name='Image of the home stadium')),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=200)),
                ('last_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('username', models.CharField(max_length=150, unique=True)),
                ('password', models.CharField(max_length=150)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=12)),
            ],
        ),
        migrations.CreateModel(
            name='HandicapBetInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_type', models.CharField(choices=[('full time', 'full_time'), ('half time', 'half_time')], max_length=50)),
                ('bet_team', models.CharField(max_length=150)),
                ('handicap_cover', models.DecimalField(decimal_places=2, max_digits=5)),
                ('odd', models.DecimalField(decimal_places=2, max_digits=5)),
                ('status', models.CharField(choices=[('Unsettled', 'UN'), ('Settled', 'SE')], default='Unsettled', max_length=50)),
                ('settled_date', models.DateField(blank=True, null=True, verbose_name='The date this handicap bet was settled')),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.match')),
            ],
        ),
        migrations.CreateModel(
            name='MoneylineBetInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_type', models.CharField(choices=[('full time', 'full_time'), ('half time', 'half_time')], max_length=50)),
                ('bet_team', models.CharField(max_length=150)),
                ('odd', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('status', models.CharField(choices=[('Unsettled', 'UN'), ('Settled', 'SE')], default='Unsettled', max_length=50)),
                ('settled_date', models.DateField(blank=True, null=True, verbose_name='The date this moneyline bet was settled')),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.match')),
            ],
        ),
        migrations.CreateModel(
            name='TotalGoalsBetInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_type', models.CharField(choices=[('full time', 'full_time'), ('half time', 'half_time')], max_length=50)),
                ('under_or_over', models.CharField(choices=[('Under', 'Under'), ('Over', 'Over')], max_length=10)),
                ('target_num_goals', models.IntegerField(default=0)),
                ('odd', models.DecimalField(decimal_places=2, max_digits=5)),
                ('status', models.CharField(choices=[('Unsettled', 'UN'), ('Settled', 'SE')], default='Unsettled', max_length=50)),
                ('settled_date', models.DateField(blank=True, null=True, verbose_name='The date this total goals bet was settled')),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.match')),
            ],
        ),
        migrations.CreateModel(
            name='UserHandicapBet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bet_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('bet_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.handicapbetinfo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.user')),
            ],
        ),
        migrations.CreateModel(
            name='UserMoneylineBet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bet_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('bet_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.moneylinebetinfo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.user')),
            ],
        ),
        migrations.CreateModel(
            name='UserTotalGoalsBet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bet_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('bet_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.totalgoalsbetinfo')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='soccerapp.user')),
            ],
        ),
    ]
