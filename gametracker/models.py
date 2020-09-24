from __future__ import unicode_literals

from django.db import models


class Person(models.Model):
    """Person playing. Should be unique"""
    name = models.CharField(max_length=50, db_index=True)
    firstname = models.CharField(max_length=50, default=None, blank=True)
    lastname = models.CharField(max_length=50, default=None, blank=True)

    ngames = models.PositiveIntegerField(default=0)
    elo = models.PositiveIntegerField(default=0)
    init_elo = models.PositiveIntegerField(default=1400)

    avatar = models.ImageField(upload_to='avatars/', default=None, blank=True)

    def __str__(self):
        return self.name

    def get_elo(self):
        return self.elo


class Identity(models.Model):
    """Correspondance between a person and a pseudonyme. A person can have multiple pseudonymes"""
    person = models.ForeignKey('Person', on_delete=models.CASCADE, default=None,
                               null=True, blank=True)
    pseudo = models.CharField(max_length=50)

    def __str__(self):
        return self.pseudo


class Player(models.Model):
    """Player in a game"""
    identity = models.ForeignKey('Identity', on_delete=models.SET_NULL, default=None, null=True, blank=True)
    number = models.PositiveSmallIntegerField(default=None, null=True, blank=True)
    team = models.PositiveIntegerField(default=None, null=True, blank=True)
    civilization = models.CharField(max_length=50, default=None, null=True, blank=True)
    resign_time = models.PositiveIntegerField(default=0, blank=True)

    def __str__(self):
        if self.identity:
            return self.identity.pseudo
        else:
            return "unknown"

    def get_elo(self):
        if self.identity.person:
            return self.identity.person.elo
        else:
            print("warning: no identity for this player")
        return None


class GameMap(models.Model):
    """A game map object"""
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Game(models.Model):
    """
    A game opposing two teams. DO NOT modify teams after the game creation, otherwise the elo rating
    of players will be incorrectly recalculated.
    """
    date = models.DateTimeField(db_index=True)
    game_map = models.ForeignKey('GameMap', on_delete=models.PROTECT, null=True, blank=True)
    ranked = models.BooleanField(default=True)
    team1 = models.ManyToManyField('Player', related_name="team1")
    team2 = models.ManyToManyField('Player', related_name="team2")
    winner = models.CharField(max_length=20, default="team1", choices=[("team1", "Équipe 1"),
                                                                       ("team2", "Équipe 2")])
    replay = models.ForeignKey('GameReplay', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return str(self.date)

    def players(self):
        """Returns all players of the game"""
        return self.team1.all() | self.team2.all()

    def winners(self):
        """Returns winning players of the game"""
        if self.winner == "team2":
            return self.team2.all()
        else:
            return self.team1.all()

    def losers(self):
        """Returns all losing players of the game"""
        if self.winner == "team2":
            return self.team1.all()
        else:
            return self.team2.all()


class GameReplay(models.Model):
    """Replay of a game"""
    replay = models.FileField(upload_to='games/')

    minimap = models.ImageField(upload_to='minimaps/', default='', blank=True)
    chronology = models.ImageField(upload_to='researches/', default='', blank=True)

    game_version = models.CharField(max_length=20, default="", blank=True)
    game_type = models.CharField(max_length=50, default="Standard Game", blank=True)
    population_limit = models.PositiveSmallIntegerField(default=0, blank=True)
    speed = models.CharField(max_length=20, default="normal", blank=True)
    difficulty = models.CharField(max_length=20, default="normal", blank=True)

    def __str__(self):
        return self.replay.path


class EloLog(models.Model):
    """A table tracking elo of all players over time"""
    person = models.ForeignKey('Person', on_delete=models.PROTECT, db_index=True)
    date = models.DateTimeField(db_index=True)
    elo = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.person) + " " + self.date.strftime("%Y-%m-%d %H:%M:%S") + ' ' + str(self.elo)
