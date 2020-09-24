from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from gametracker.utils import TeamBalancer, calc_team_elo, prob_winning, calculate_new_elo
from gametracker import factories
from gametracker.signals import update_elo



class PersonTest(TestCase):
    def test_str_person(self):
        person = factories.PersonFactory(name="Foo")
        self.assertEqual(str(person), "Foo")

    def test_elo(self):
        person = factories.PersonFactory(name="Toto", init_elo=2000)
        self.assertEqual(person.get_elo(), 2000)


class PlayerTest(TestCase):
    def test_str_player(self):
        player = factories.PlayerFactory(identity=factories.IdentityFactory(pseudo="Foo1234"))
        self.assertEqual(str(player), "Foo1234")


class GameMapTest(TestCase):
    def test_str_gamemap(self):
        gmap = factories.GameMapFactory.create(name="Arabia")
        self.assertEqual(str(gmap), "Arabia")

    def test_str_gamemap_empty(self):
        gmap = factories.GameMapFactory.create(name="")
        self.assertEqual(str(gmap), "")


class GameTest(TestCase):
    def setUp(self):
        elos = [2000, 1500, 2100, 1900]
        self.persons = [factories.PersonFactory(init_elo=elo) for elo in elos]
        self.identities = [factories.IdentityFactory(person=p) for p in self.persons]
        self.players = [factories.PlayerFactory(identity=identity) for identity in self.identities]

    def test_str_game(self):
        """Test Game __str__ method"""
        dt = timezone.now()
        self.assertEqual(str(factories.GameFactory.create(date=dt)), str(dt))

    def test_winners(self):
        """Tests that the Game class correctly returns the winning players"""
        game = factories.GameFactory.create(team1=[self.players[0], self.players[1]],
                                            team2=[self.players[2], self.players[3]])

        self.assertEqual(set(game.winners()), set([self.players[0], self.players[1]]))

        game = factories.GameFactory.create(team1=[self.players[0], self.players[1]],
                                            team2=[self.players[2], self.players[3]], winner="team2")

        self.assertEqual(set(game.winners()), set([self.players[2], self.players[3]]))

    def test_losers(self):
        """Tests that the Game class correctly returns the losing players"""
        game = factories.GameFactory.create(team1=[self.players[0], self.players[1]],
                                            team2=[self.players[2], self.players[3]])

        self.assertEqual(set(game.losers()), set([self.players[2], self.players[3]]))

        game = factories.GameFactory.create(team1=[self.players[0], self.players[1]],
                                            team2=[self.players[2], self.players[3]], winner="team2")

        self.assertEqual(set(game.losers()), set([self.players[0], self.players[1]]))



class UtilsTest(TestCase):
    def setUp(self):
        elos = [2000, 1500, 2100, 1900, 2500, 1500, 1400, 1200]
        self.persons = [factories.PersonFactory(init_elo=elo) for elo in elos]
        self.identities = [factories.IdentityFactory(person=p) for p in self.persons]
        self.players = [factories.PlayerFactory(identity=identity) for identity in self.identities]

    def test_team_elo(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = calc_team_elo([self.players[0]])
        elo_team2 = calc_team_elo([self.players[1]])

        self.assertEqual(elo_team1, self.players[0].get_elo())
        self.assertEqual(elo_team2, self.players[1].get_elo())

        elo_team1 = calc_team_elo([self.players[0], self.players[1]])
        elo_team2 = calc_team_elo([self.players[2], self.players[3]])

        self.assertEqual(elo_team1, 2050)
        self.assertEqual(elo_team2, 2300)

        elo_team1 = calc_team_elo([self.players[0], self.players[1], self.players[4]])
        elo_team2 = calc_team_elo([self.players[2], self.players[3], self.players[5]])

        self.assertEqual(round(elo_team1, 0), 2475)
        self.assertEqual(round(elo_team2, 0), 2309)

        elo_team1 = calc_team_elo([self.players[0], self.players[1],
                                        self.players[4], self.players[7]])
        elo_team2 = calc_team_elo([self.players[2], self.players[3],
                                        self.players[5], self.players[6]])

        self.assertEqual(round(elo_team1, 0), 2400)
        self.assertEqual(round(elo_team2, 0), 2325)

    def test_prob_winning(self):
        """Test probabilité de gagner (>50%)"""
        team1 = [self.players[0], self.players[1], self.players[4], self.players[7]]
        team2 = [self.players[2], self.players[3], self.players[5], self.players[6]]

        self.assertEqual(round(prob_winning(calc_team_elo(team1) - calc_team_elo(team2)) * 100, 2), 66.61)
        self.assertEqual(round(prob_winning(calc_team_elo(team2) - calc_team_elo(team1)) * 100, 2), 33.39)

    def test_prob_winnng_under50(self):
        """Test probabilité de gagner (<50%)"""
        team1 = [self.players[0], self.players[1], self.players[6], self.players[7]]
        team2 = [self.players[2], self.players[3], self.players[4], self.players[5]]

        # Probability is the same for everyone in the team
        self.assertEqual(round(prob_winning(calc_team_elo(team1) - calc_team_elo(team2)) * 100, 2), 1.24)
        self.assertEqual(round(prob_winning(calc_team_elo(team2) - calc_team_elo(team1)) * 100, 2), 98.76)

    def test_calculate_new_elo(self):
        self.assertEqual(calculate_new_elo(2000, -100, True), round(2000 + 20 * (1 - prob_winning(-100))))
        self.assertEqual(calculate_new_elo(2000, -100, False), round(2000 + 20 * (0 - prob_winning(-100))))


class IntegrationTests(TestCase):
    def setUp(self):
        elos = [2000, 1800, 2100]
        self.persons = [factories.PersonFactory(init_elo=elo) for elo in elos]
        self.identities = [factories.IdentityFactory(person=p) for p in self.persons]
        self.players = [factories.PlayerFactory(identity=identity) for identity in self.identities]

    def test_get_elo_after(self):
        factories.GameFactory.create(team1=(self.players[0],),
                                     team2=(self.players[2],), winner="team2")

        update_elo()
        self.persons[0].refresh_from_db()
        self.persons[2].refresh_from_db()

        self.assertEqual(self.persons[0].elo, calculate_new_elo(2000, -100, False))
        self.assertEqual(self.persons[2].elo, calculate_new_elo(2100, 100, True))

    def test_get_elo_after_2games(self):
        factories.GameFactory.create(team1=(self.players[0],),
                                     team2=(self.players[2],), winner="team2")

        factories.GameFactory.create(team1=(self.players[0],),
                                     team2=(self.players[2],), winner="team2")

        update_elo()
        self.persons[0].refresh_from_db()
        self.persons[2].refresh_from_db()

        self.assertEqual(self.persons[0].elo, calculate_new_elo(calculate_new_elo(2000, -100, False), -100, False))
        self.assertEqual(self.persons[2].elo, calculate_new_elo(calculate_new_elo(2100, 100, True), 100, True))

    def test_multiple_games(self):
        """Teste que gagner en étant équipe 1 ou 2 n'a pas d'importance"""
        elos = [1900, 2100]
        persons = [factories.PersonFactory(init_elo=elo) for elo in elos]
        identities = [factories.IdentityFactory(person=p) for p in persons]
        players = [factories.PlayerFactory(identity=identity) for identity in identities]

        # p1 gagne en équipe 1
        factories.GameFactory.create(team1=[players[0]], team2=[players[1]], winner="team1")

        # p2 gagne en équipe 2
        factories.GameFactory.create(team1=[players[0]], team2=[players[1]], winner="team2")

        update_elo()
        persons[0].refresh_from_db()
        persons[1].refresh_from_db()

        elo_p1_1 = players[0].get_elo()
        elo_p2_1 = players[1].get_elo()

        # Reset
        persons = [factories.PersonFactory(init_elo=elo) for elo in elos]
        identities = [factories.IdentityFactory(person=p) for p in persons]
        players = [factories.PlayerFactory(identity=identity) for identity in identities]

        # p1 gagne en équipe 2
        factories.GameFactory.create(team1=[players[1]], team2=[players[0]], winner="team2")

        # p2 gagne en équipe 1
        factories.GameFactory.create(team1=[players[1]], team2=[players[0]], winner="team1")

        update_elo()
        persons[0].refresh_from_db()
        persons[1].refresh_from_db()

        elo_p1_2 = players[0].get_elo()
        elo_p2_2 = players[1].get_elo()

        self.assertNotEqual(elo_p1_1, elos[0])
        self.assertNotEqual(elo_p2_1, elos[1])
        self.assertEqual(elo_p1_1, elo_p1_2)
        self.assertEqual(elo_p2_1, elo_p2_2)

    def test_delete_game(self):
        """Delete a game from the database and recalculate elo"""
        # Expected result
        person1_copy = factories.PersonFactory.create(init_elo=self.players[0].get_elo())
        person2_copy = factories.PersonFactory.create(init_elo=self.players[1].get_elo())

        identity1_copy = factories.IdentityFactory(person=person1_copy)
        identity2_copy = factories.IdentityFactory(person=person2_copy)

        player1_copy = factories.PlayerFactory(identity=identity1_copy)
        player2_copy = factories.PlayerFactory(identity=identity2_copy)

        # Only game1 and game3 for controls
        factories.GameFactory.create(team1=[player1_copy], team2=[player2_copy], winner="team1")
        factories.GameFactory.create(team1=[player1_copy, player2_copy], team2=[self.players[2]], winner="team1")

        update_elo()
        player1_copy.refresh_from_db()
        player2_copy.refresh_from_db()

        # Test: play 3 games and remove one
        games = [factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[1]], winner="team1"),
                 factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[1]], winner="team2"),
                 factories.GameFactory.create(team1=[self.players[0], self.players[1]], team2=[self.players[2]])]

        # Remove the second game
        games[1].delete()
        games.remove(games[1])

        update_elo()
        self.players[0].refresh_from_db()
        self.players[1].refresh_from_db()

        self.assertEqual(self.players[0].get_elo(), player1_copy.get_elo(), 0)
        self.assertEqual(self.players[1].get_elo(), player2_copy.get_elo(), 0)


class TeamBalancerTest(TestCase):
    def test_balancing_teams(self):
        elos = [2001, 1500, 2000, 1499]
        players = [factories.PersonFactory(init_elo=elo) for elo in elos]

        team_balancer = TeamBalancer(players)
        teams = team_balancer.get_teams()

        self.assertEqual(set([players[0], players[3]]), set(teams[0]))
        self.assertEqual(set([players[1], players[2]]), set(teams[1]))

    def test_balancing_teams_alt(self):
        elos = [2300, 1503, 1502, 1501, 1400]
        players = [factories.PersonFactory(init_elo=elo) for elo in elos]

        team_balancer = TeamBalancer(players)
        bteams = team_balancer.get_balanced_teams()

        self.assertEqual(set(bteams[0]), set([players[0], players[-1]]))


# Test views
#class TestViews(TestCase):
#    @classmethod
#    def setUpClass(cls):
#        elos = [2000, 2000, 1500, 1500, 1500, 1500, 1500]
#        cls.persons = [factories.PersonFactory(elo=elo) for elo in elos]
#        cls.identities = [factories.IdentityFactory(person=p) for p in cls.persons]
#        cls.players = [factories.PlayerFactory(identity=identity) for identity in cls.identities]
#        super(TestViews, cls).setUpClass()
#
#    def test_pages(self):
#        """Test that all pages are accessible"""
#        pages = ('', '/index', '/games', '/addgame', '/players', '/teams',
#                 '/player/' + self.persons[0].name, '/player/' + self.persons[1].name.upper())
#
#        for page in pages:
#            response = self.client.get(page)
#            self.assertEqual(response.status_code, 200)
#
#    def test_team_balancing_page(self):
#        """Test that team balancing return code after form completion is 200"""
#        player1 = self.players[0]
#        player2 = self.players[1]
#
#        response = self.client.post(reverse('gametracker:balance_teams'), {'players': [player1.pk, player2.pk]})
#        self.assertEqual(response.status_code, 200)
#
#        response = self.client.post(reverse('gametracker:balance_teams'), {'players': [player1.pk]})
#        self.assertEqual(response.status_code, 200)
#
#    def test_team_full_balancing_page(self):
#        """Test that team balancing return code after form completion is 200"""
#        players = self.players[1:]
#        players_pk = [player.pk for player in players]
#
#        response = self.client.post(reverse('gametracker:balance_teams'),
#                                    {'players': players_pk})
#        self.assertEqual(response.status_code, 200)
#
#    def test_player_detail(self):
#        """Test the detailed view of a player"""
#        factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[1]], winner="team1")
#
#        self.persons[0].refresh_from_db()
#        self.persons[1].refresh_from_db()
#
#        response = self.client.get("/player/" + self.players[0].identity.person.name)
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(response.context['victories'], 1)
#        self.assertEqual(response.context['defeats'], 0)
#        self.assertEqual(response.context['ratio'], 100)
#
#        response = self.client.get("/player/" + self.players[1].identity.person.name)
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(response.context['victories'], 0)
#        self.assertEqual(response.context['defeats'], 1)
#        self.assertEqual(response.context['ratio'], 0)
#
#    def test_game_detail(self):
#        game = factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[1]], winner="team1")
#        response = self.client.get("/game/" + str(game.pk))
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(list(response.context['winners']), [self.players[0]])
#        self.assertEqual(list(response.context['losers']), [self.players[1]])
#
#    def test_game_detail_2players(self):
#        team1 = [self.players[0], self.players[2]]
#        team2 = [self.players[1], self.players[3]]
#
#        game = factories.GameFactory.create(team1=team1, team2=team2, winner="team1")
#        response = self.client.get("/game/" + str(game.pk))
#        self.assertEqual(response.status_code, 200)
#        self.assertEqual(list(response.context['winners']), team1)
#        self.assertEqual(list(response.context['losers']), team2)
