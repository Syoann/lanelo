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

    def has_won(self, game):
        """Did player win this game ?"""
        return self in game.winners()

    def play(self, game):
        """Play a game"""
        # Check that the player played this game
        if not game.has_player(self):
            raise(ValueError, 'Player did not play this game !')

        # Did the player win the game ?
        won = int(self.has_won(game))

        # Calculate player's new elo
        self.elo += self._k() * (won - prob_winning(game.get_delta_elo(self)))

        # Add this game to played games
        self.ngames += 1


@python_2_unicode_compatible
class GameMap(models.Model):
    """A game map object"""
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Game(models.Model):
    """
    A game opposing two teams. DO NOT modify teams after the game creation, otherwise the elo rating
    of players will be incorrectly recalculated.
    """
    date = models.DateTimeField()
    game_map = models.ForeignKey('GameMap', on_delete=models.PROTECT, null=True, blank=True)
    team1 = models.ManyToManyField('Player', related_name="team1")
    team2 = models.ManyToManyField('Player', related_name="team2")
    winner = models.CharField(max_length=20, default="team1", choices=[("team1", "Équipe 1"),
                                                                       ("team2", "Équipe 2")])

    def __str__(self):
        return str(self.date)

    def has_player(self, player):
        """Checks if a player has played this game"""
        return player in list(self.team1.all()) + list(self.team2.all())

    def winners(self):
        """Returns winners of the game"""
        if self.winner == "team2":
            return self.team2.all()
        else:
            return self.team1.all()

    def get_delta_elo(self, player=None):
        """
        Return the initial difference in elo (elo(team1) - elo(team2)).
        If player is not None, the delta_elo is elo(team_player) - elo(other_team)
        This attribute is added in a callback function after the two teams are populated
        """
        if player in self.team2.all():
            return -self.delta_elo
        else:
            return self.delta_elo


class TeamBalancer:
    """Create two balanced teams from a list of players"""
    def __init__(self, players):
        self.players = players

    def __partition_players(self, size):
        """Split players in two teams: one of size 'size' and the other of size N - 'size'"""
        min_delta = None
        teams = []

        # Explore all combinations with 1st group of size 'size'
        for players in itertools.combinations(self.players, size):
            team1 = list(set(players))
            team2 = list(set(self.players) - set(players))

            diff = abs(calculate_team_elo(team1) - calculate_team_elo(team2))

            if diff < min_delta or min_delta is None:
                teams = [team1, team2]
                min_delta = diff

        return teams

    def get_teams(self):
        """Return the most balanced teams according to the algorithm"""
        s_teams = [self.__partition_players(size) for size in range(1, len(self.players) / 2 + 1)]
        deltas = [abs(calculate_team_elo(couple[0]) - calculate_team_elo(couple[1])) for couple in s_teams]
        return s_teams[deltas.index(min(deltas))]

    def get_balanced_teams(self):
        """Return the most balanced teams with a similar number of players in both teams"""
        return self.__partition_players(len(self.players) // 2)
