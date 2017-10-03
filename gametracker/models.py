# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import math
import itertools

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from utils import *


@python_2_unicode_compatible
class Player(models.Model):
    name = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50, default=None, blank=True)
    lastname = models.CharField(max_length=50, default=None, blank=True)
    ngames = models.PositiveIntegerField(default=0)
    elo = models.PositiveIntegerField(default=1400)

    def __str__(self):
        return self.name

    def _k(self):
        """Factor regulating the variation of elo points after a game"""
        if self.ngames >= 0:
            return 200 / (math.sqrt(self.ngames) + 10) + 5
        else:
            raise ValueError("The number of games is a negative number !", self.ngames)


@python_2_unicode_compatible
class GameMap(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Game(models.Model):
    date = models.DateTimeField()
    game_map = models.ForeignKey('GameMap', on_delete=models.PROTECT, null=True, blank=True)
    team1 = models.ManyToManyField('Player', related_name="team1")
    team2 = models.ManyToManyField('Player', related_name="team2")
    winner = models.CharField(max_length=20, default="team1", choices=[("team1", "Équipe 1"),
                                                                       ("team2", "Équipe 2")])

    def __str__(self):
        return str(self.date)


class TeamBalancer:
    """Create two balanced teams from a list of players"""
    def __init__(self, players):
        self.players = players

    def __partition_players(self, size):
        """Split players in two teams: one of size 'size' and the other of size N - 'size'"""
        min_delta = None
        teams = []

        for players in itertools.combinations(self.players, size):
            team1 = list(set(players))
            team2 = list(set(self.players) - set(players))

            diff = abs(calculate_team_elo(team1) - calculate_team_elo(team2))

            if diff < min_delta or min_delta is None:
                teams = [team1, team2]
                min_delta = diff

        return teams

    def get_teams(self):
        min_delta = None
        balanced_teams = None
        # For all combinations of players in 2 teams, compare elo
        # and save teams with minimum elo difference.
        for size in xrange(1, len(self.players) / 2 + 1):
            teams = self.__partition_players(size)
            min_d = abs(calculate_team_elo(teams[0]) - calculate_team_elo(teams[1]))

            if min_d < min_delta or min_delta is None:
                min_delta = min_d
                balanced_teams = teams

        return balanced_teams

    def get_balanced_teams(self):
        return self.__partition_players(len(self.players) // 2)



class PlayerGameStats(object):
    """Calculate and store statistics of a player in a game"""
    def __init__(self, player, game):
        self.player = player
        self.game = game

        self.team = None
        self.ennemy_team = None
        self.won = False

        # Check the team and the result here instead of checking it in every method
        if self.player in self.game.team1.all():
            self.team = self.game.team1.all()
            self.ennemy_team = self.game.team2.all()
            if self.game.winner == "team1":
                self.won = True
        elif self.player in self.game.team2.all():
            self.team = self.game.team2.all()
            self.ennemy_team = self.game.team1.all()
            if self.game.winner == "team2":
                self.won = True
        else:
            raise ValueError('Player is not in team1 nor in team2 of this game !', self.player)

    def get_elo_after(self):
        """Returns elo rating of the player after the game"""
        return self.player.elo + self.get_elo_var()

    def get_elo_var(self):
        """Elo rating variation after this match"""
        delta_elo = calculate_team_elo(self.team) - calculate_team_elo(self.ennemy_team)
        return self.player._k() * (int(self.won) - prob_winning(delta_elo))
