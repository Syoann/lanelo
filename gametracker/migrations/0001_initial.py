# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-23 19:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('winner', models.CharField(choices=[('team1', '\xc9quipe 1'), ('team2', '\xc9quipe 2')], default='team1', max_length=20)),
                ('game_file', models.FileField(blank=True, null=True, upload_to='games/')),
            ],
        ),
        migrations.CreateModel(
            name='GameMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('firstname', models.CharField(blank=True, default=None, max_length=50)),
                ('lastname', models.CharField(blank=True, default=None, max_length=50)),
                ('ngames', models.PositiveIntegerField(default=0)),
                ('elo', models.PositiveIntegerField(default=1400)),
                ('init_elo', models.PositiveIntegerField(default=1400)),
                ('avatar', models.ImageField(blank=True, default=None, upload_to='avatars/')),
            ],
        ),
        migrations.AddField(
            model_name='game',
            name='game_map',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='gametracker.GameMap'),
        ),
        migrations.AddField(
            model_name='game',
            name='team1',
            field=models.ManyToManyField(related_name='team1', to='gametracker.Player'),
        ),
        migrations.AddField(
            model_name='game',
            name='team2',
            field=models.ManyToManyField(related_name='team2', to='gametracker.Player'),
        ),
    ]
