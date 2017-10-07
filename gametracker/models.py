# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import math
import itertools

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from utils import calculate_team_elo, prob_winning


@python_2_unicode_compatible
class Player(models.Model):
    name = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50, default=None, blank=True)
    lastname = models.CharField(max_length=50, default=None, blank=True)
    ngames = models.PositiveIntegerField(default=0)
    elo = models.PositiveIntegerField(default=1400)
    init_elo = models.PositiveIntegerField(default=1400)

    def __str__(self):
        return self.name

    def _k(self):
        """Factor regulating the variation of elo points after a game"""
        if self.ngames >= 0:
            return 200 / (math.sqrt(self.ngames) + 10) + 5
        else:
            raise ValueError("The number of games is a negative number !", self.ngames)

    def play(self, game):
        """Play a game"""
        # Did the player win the game ?
        won = int(self in game.winners())

        # Calculate player's new elo
        self.elo += self._k() * (won - prob_winning(game.delta_elo(self)))

        # Add this game to played games
        self.ngames += 1


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

    def winners(self):
        if self.winner == "team1":
            return self.team1.all()
        elif self.winner == "team2":
            return self.team2.all()
        else:
            raise(ValueError, 'Neither team1 nor team2 won the game!')

    def delta_elo(self, player=None):
        if player is None or player in self.team1.all():
            return calculate_team_elo(self.team1.all()) - calculate_team_elo(self.team2.all())
        elif player in self.team2.all():
            return calculate_team_elo(self.team2.all()) - calculate_team_elo(self.team1.all())


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
        for size in range(1, len(self.players) / 2 + 1):
            teams = self.__partition_players(size)
            min_d = abs(calculate_team_elo(teams[0]) - calculate_team_elo(teams[1]))

            if min_d < min_delta or min_delta is None:
                min_delta = min_d
                balanced_teams = teams

        return balanced_teams

    def get_balanced_teams(self):
        return self.__partition_players(len(self.players) // 2)
