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

    def get_elo(self):
        """Calculate elo for the team"""
        # Multiplicative factor for multiplayer teams
        MP_FACTOR = 300
        elos = [p.elo for p in self.players]
        return float(sum(elos)) / len(self.players) + MP_FACTOR * math.log(len(self.players), 2)


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

    def pW(self):
        """Probability to win a game based on elo difference.
           returns a tuple (p_win(team1), p_win(team2)"""
        pw = {}
        delta_elo = self.teams["team1"].get_elo() - self.teams["team2"].get_elo()
        
        pw["team1"] = 1 / (1 + 10**(-delta_elo / 250))
        pw["team2"] = 1 / (1 + 10**(delta_elo / 250))
        return pw

    def K(self, ngames):
        """Factor regulating the variation of elo points after a game"""
        if ngames >= 0 :
            return 200 / (math.sqrt(ngames) + 10) + 5 
        else:
            raise ValueError("The number of games is a negative number !", ngames)

    def _team_elo_var(self, team_name):
        """Game component of the variation of elo"""
        return int(self.winner == team_name) - self.pW()[team_name]

    def new_elo(self, player):
        if player in self.teams["team1"].players:
            return player.elo + self.K(player.ngames) * self._team_elo_var("team1")
        elif player in self.teams["team2"].players:
            return player.elo + self.K(player.ngames) * self._team_elo_var("team2")
        else:
            raise ValueError("The player is not part of team1 nor team2 !", player)
