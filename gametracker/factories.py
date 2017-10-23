#! /usr/bin/env python
# -*- coding: utf-8 -*-

import factory
from django.utils import timezone

from . import models


class PlayerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Player

    firstname = factory.Faker('first_name')
    lastname = factory.Faker('last_name')
    name = factory.LazyAttribute(lambda a: '{0}{1}'.format(a.firstname[:1], a.lastname).lower())
    ngames = 0
    elo = 1500
    init_elo = factory.LazyAttribute(lambda p: p.elo)


class GameMapFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.GameMap

    name = 'Arabia'


class GameFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Game

    date = factory.LazyFunction(timezone.now)
    game_map = models.GameMap("")
    winner = "team1"
    game_file = None

    @factory.post_generation
    def team1(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for player in extracted:
                self.team1.add(player)

    @factory.post_generation
    def team2(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for player in extracted:
                self.team2.add(player)
