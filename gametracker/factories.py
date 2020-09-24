import factory
from django.utils import timezone

from gametracker import models


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Person

    firstname = factory.Faker('first_name')
    lastname = factory.Faker('last_name')
    name = factory.LazyAttribute(lambda a: '{0}{1}'.format(a.firstname[:1], a.lastname).lower())
    ngames = 0
    init_elo = 1500
    elo = factory.LazyAttribute(lambda p: p.init_elo)


class IdentityFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Identity

    person = None
    pseudo = factory.Faker('first_name')


class PlayerFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Player

    identity = factory.SubFactory(IdentityFactory)
    number = 1
    team = 2
    civilization = 'Franks'
    resign_time = 0


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
