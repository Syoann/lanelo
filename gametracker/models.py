# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
import math
import itertools

# Create your models here.

@python_2_unicode_compatible
class Player(models.Model):
    name = models.CharField(max_length=50)
    firstname = models.CharField(max_length=50, default=None, blank=True)
    lastname = models.CharField(max_length=50, default=None, blank=True)
    ngames = models.PositiveIntegerField(default=0)
    elo = models.PositiveIntegerField(default=1400)
    def __str__(self):
        return self.name

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
    winner = models.CharField(max_length=20, choices=[("team1", "Équipe 1"), ("team2", "Équipe 2")], default="team1")
    def __str__(self):
        return str(self.date)

    def update_elo(self):
        elo_calc = EloCalculator(Team(self.team1), Team(self.team2), self.winner)
        return elo_calc.calc()       
 
class Team:
    """A team is a group of players. An Elo can be calculated for the team"""
    def __init__(self, players):
        self.players = players
        self.elo = self._calc_elo()

    def add_player(self, player):
        self.players.extend(player)
        self.elo = self._calc_elo

    def get_elo(self):
        return self.elo

    def _calc_elo(self):
        # Multiplicative factor for multiplayer teams
        MP_FACTOR = 300

        elos = [p.elo for p in self.players]
        return sum(elos) / float(len(elos)) + MP_FACTOR * math.log(len(elos), 2)


class TeamBalancer:
    """Create two balanced teams from a list of players"""
    def __init__(self, players):
        self.players = players
        self.result = {"team1": None, "team2": None, "team1eq": None, "team2eq": None}

    def balance(self):
        min_delta = None;
        min_delta_eq = None;

        # For all combinations of players in 2 teams, compare elo and save teams with minimum elo difference
        # Moreover, retain teams with even number of players and minimum elo difference
        for size in xrange(1, len(self.players) / 2 + 1):
            for players_list in itertools.combinations(self.players, size):
                team1 = Team(players_list)
                team2 = Team(tuple(set(self.players) - set(players_list)))

                diff = abs(team1.get_elo() - team2.get_elo())

                if diff < min_delta or min_delta is None:
                    (self.result["team1"], self.result["team2"]) = (team1, team2)
                    min_delta = diff

                if size >= len(self.players) / 2 and (diff < min_delta_eq or min_delta_eq is None):
                    (self.result["team1eq"], self.result["team2eq"]) = (team1, team2)
                    min_delta_eq = diff

        if set([self.result["team1eq"], self.result["team2eq"]]) == set([self.result["team1"], self.result["team2"]]):
            (self.result["team1eq"], self.result["team2eq"]) = (None, None)

        return self.result

class EloCalculator:
    def __init__(self, team1, team2, winner="team1"):
        self.teams = { "team1": team1, "team2": team2 }
        self.winner = winner

    def pD(self, team_name="team1"):
        """Probability to win a game based on elo difference"""

        delta = self.teams["team1"].get_elo() - self.teams["team2"].get_elo()
        if team_name == "team2":
            delta = -delta

        return 1 / (1 + 10**(-delta/250))

    def K(self, ngames):
        """Factor regulating the variation of elo points after a game"""
        if ngames >= 0 :
            return 200 / (math.sqrt(ngames) + 10) + 5 
        else:
            return None

    def new_elo(self, player):
        if player in self.teams["team1"].players:
            return player.elo + self.K(player.ngames) * (int(self.winner == "team1") - self.pD("team1"))
        elif player in self.teams["team2"].players:
            return player.elo + self.K(player.ngames) * (int(self.winner == "team2") - self.pD("team2"))
        else:
            return None

    def calc(self):
        players = []
        for team_name, team in self.teams.item():
            for player in team:
                new_elo = player.elo + self.K(player.ngames) * (int(self.winner == team_name) - self.pD(team_name))
                players.append(Player(player.name, player.firstname, player.lastname, player.ngames+1, new_elo))

        return players
