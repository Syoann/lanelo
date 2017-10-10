# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from models import TeamBalancer
from utils import calculate_team_elo, prob_winning
from . import factories


class PlayerTest(TestCase):
    def test_str_player(self):
        player = factories.PlayerFactory(name="Foo")
        self.assertEqual(str(player), "Foo")

    def test_k_0(self):
        player = factories.PlayerFactory()
        self.assertEqual(player._k(), 25)

    def test_k_10(self):
        player = factories.PlayerFactory(ngames=10)
        self.assertEqual(round(player._k(), 0), 20)

    def test_k_100(self):
        player = factories.PlayerFactory(ngames=100)
        self.assertEqual(player._k(), 15)

    def test_k_error(self):
        player = factories.PlayerFactory(ngames=-1)
        self.assertRaises(ValueError, player._k)


class GameMapTest(TestCase):
    def test_str_gamemap(self):
        names = ("Arabia", "")

        for name in names:
            gmap = factories.GameMapFactory.create(name=name)
            self.assertEqual(str(gmap), name)


class GameTest(TestCase):
    def setUp(self):
        elos = [2000, 1500, 2100, 1900, 2500, 1500, 1400, 1200]
        self.players = [factories.PlayerFactory(elo=elo) for elo in elos]

    def test_str_game(self):
        """Test Game __str__ method"""
        dt = timezone.now()
        self.assertEqual(str(factories.GameFactory.create(date=dt)), str(dt))

    def test_delta_elo(self):
        """Test Game get_delta_elo method"""
        game = factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[2]])

        self.assertEqual(game.get_delta_elo(), -100)
        self.assertEqual(game.get_delta_elo(self.players[0]), -100)
        self.assertEqual(game.get_delta_elo(self.players[2]), 100)

    def test_team_elo(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = calculate_team_elo([self.players[0]])
        elo_team2 = calculate_team_elo([self.players[1]])

        self.assertEqual(elo_team1, self.players[0].elo)
        self.assertEqual(elo_team2, self.players[1].elo)

        elo_team1 = calculate_team_elo([self.players[0], self.players[1]])
        elo_team2 = calculate_team_elo([self.players[2], self.players[3]])

        self.assertEqual(elo_team1, 2050)
        self.assertEqual(elo_team2, 2300)

        elo_team1 = calculate_team_elo([self.players[0], self.players[1], self.players[4]])
        elo_team2 = calculate_team_elo([self.players[2], self.players[3], self.players[5]])

        self.assertEqual(round(elo_team1, 0), 2475)
        self.assertEqual(round(elo_team2, 0), 2309)

        elo_team1 = calculate_team_elo([self.players[0], self.players[1],
                                        self.players[4], self.players[7]])
        elo_team2 = calculate_team_elo([self.players[2], self.players[3],
                                        self.players[5], self.players[6]])

        self.assertEqual(round(elo_team1, 0), 2400)
        self.assertEqual(round(elo_team2, 0), 2325)

    def test_prob_winning(self):
        """Test probabilité de gagner (positif)"""
        team1 = [self.players[0], self.players[1], self.players[4], self.players[7]]
        team2 = [self.players[2], self.players[3], self.players[5], self.players[6]]

        self.assertEqual(round(prob_winning(calculate_team_elo(team1) - calculate_team_elo(team2)) * 100, 2), 66.61)
        self.assertEqual(round(prob_winning(calculate_team_elo(team2) - calculate_team_elo(team1)) * 100, 2), 33.39)

    def test_prob_winnng_under50(self):
        """Test probabilité de gagner (négatif)"""
        team1 = [self.players[0], self.players[1], self.players[6], self.players[7]]
        team2 = [self.players[2], self.players[3], self.players[4], self.players[5]]

        # Probability is the same for everyone in the team
        self.assertEqual(round(prob_winning(calculate_team_elo(team1) - calculate_team_elo(team2)) * 100, 2), 1.24)
        self.assertEqual(round(prob_winning(calculate_team_elo(team2) - calculate_team_elo(team1)) * 100, 2), 98.76)


class IntegrationTests(TestCase):
    def setUp(self):
        elos = [2000, 1800, 2100]
        self.players = [factories.PlayerFactory(elo=elo, init_elo=elo) for elo in elos]

    def test_player_play(self):
        factories.GameFactory.create(team1=(self.players[0],),
                                     team2=(self.players[2],), winner="team1")

        self.players[0].refresh_from_db()
        self.players[2].refresh_from_db()

        self.assertEqual(self.players[0].elo, 2018)
        self.assertEqual(self.players[2].elo, 2082)

    def test_get_elo_after(self):
        factories.GameFactory.create(team1=(self.players[0],),
                                     team2=(self.players[2],), winner="team2")

        self.players[0].refresh_from_db()
        self.players[2].refresh_from_db()

        self.assertEqual(round(self.players[0].elo, 0), 1993)
        self.assertEqual(round(self.players[2].elo, 0), 2107)

    # Integration tests
    def test_multiple_games(self):
        """Test que gagner en étant équipe 1 ou 2 n'a pas d'importance"""
        player1 = self.players[0]
        player2 = self.players[1]

        player1.elo = 2100
        player2.elo = 2000

        player1.ngames = 0
        player2.ngames = 0

        # p1 gagne en équipe 1
        factories.GameFactory.create(team1=(player1,), team2=(player2,), winner="team1")

        # p2 gagne en équipe 2
        factories.GameFactory.create(team1=(player1,), team2=(player2,), winner="team2")

        elo_p1_1 = player1.elo
        elo_p2_1 = player2.elo

        # Reinit
        player1 = self.players[0]
        player2 = self.players[1]

        player1.elo = 2100
        player2.elo = 2000

        player1.ngames = 0
        player2.ngames = 0

        # p1 gagne en équipe 2
        factories.GameFactory.create(team1=(player2,), team2=(player1,), winner="team2")

        # p2 gagne en équipe 1
        factories.GameFactory.create(team1=(player2,), team2=(player1,), winner="team1")

        elo_p1_2 = player1.elo
        elo_p2_2 = player2.elo

        self.assertEqual(elo_p1_1, elo_p1_2)
        self.assertEqual(elo_p2_1, elo_p2_2)

    def test_balancing_teams(self):
        elos = [2001, 1500, 2000, 1499]
        players = [factories.PlayerFactory(elo=elo) for elo in elos]

        team_balancer = TeamBalancer(players)
        teams = team_balancer.get_teams()

        self.assertEqual(set([players[0], players[3]]), set(teams[0]))
        self.assertEqual(set([players[1], players[2]]), set(teams[1]))

    def test_balancing_teams_alt(self):
        elos = [2300, 1503, 1502, 1501, 1400]
        players = [factories.PlayerFactory(elo=elo) for elo in elos]

        team_balancer = TeamBalancer(players)
        bteams = team_balancer.get_balanced_teams()

        self.assertEqual(set(bteams[0]), set([players[0], players[-1]]))

    def test_delete_game(self):
        """Delete a game from the database and recalculate elo"""
        # Expected result
        player1_copy = factories.PlayerFactory.create(elo=self.players[0].elo, init_elo=self.players[0].init_elo)
        player2_copy = factories.PlayerFactory.create(elo=self.players[1].elo, init_elo=self.players[1].init_elo)

        factories.GameFactory.create(team1=[player1_copy], team2=[player2_copy], winner="team1")
        factories.GameFactory.create(team1=[player1_copy, player2_copy], team2=[self.players[2]], winner="team1")

        player1_copy.refresh_from_db()
        player2_copy.refresh_from_db()

        # Test: play 3 games and remove one
        games = [factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[1]], winner="team1"),
                 factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[1]], winner="team2"),
                 factories.GameFactory.create(team1=[self.players[0], self.players[1]], team2=[self.players[2]])]

        # Remove the second game
        games[1].delete()
        games.remove(games[1])

        self.players[0].refresh_from_db()
        self.players[1].refresh_from_db()

        self.assertEqual(self.players[0].elo, player1_copy.elo, 0)
        self.assertEqual(self.players[1].elo, player2_copy.elo, 0)


# Test views
class TestViews(TestCase):
    @classmethod
    def setUpClass(cls):
        elos = [2000, 2000, 1500, 1500, 1500, 1500, 1500]
        cls.players = [factories.PlayerFactory(elo=elo) for elo in elos]
        super(TestViews, cls).setUpClass()

    def test_pages(self):
        """Test that all pages are accessible"""
        pages = ('', '/index', '/games', '/addgame', '/players', '/teams')

        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200)

    def test_team_balancing_page(self):
        """Test that team balancing return code after form completion is 200"""
        player1 = self.players[0]
        player2 = self.players[1]

        response = self.client.post(reverse('gametracker:balance_teams'), {'players': [player1.pk, player2.pk]})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('gametracker:balance_teams'), {'players': [player1.pk]})
        self.assertEqual(response.status_code, 200)

    def test_team_full_balancing_page(self):
        """Test that team balancing return code after form completion is 200"""
        players = self.players[1:]
        players_pk = [player.pk for player in players]

        response = self.client.post(reverse('gametracker:balance_teams'),
                                    {'players': players_pk})
        self.assertEqual(response.status_code, 200)

    def test_add_game_page(self):
        """Test that the game insertion is working"""
        game_map = factories.GameMapFactory.create()

        player1 = self.players[0]
        player2 = self.players[1]

        response = self.client.post(reverse('gametracker:add_game'), {'game_map': game_map.pk, 'team1': [player1.pk],
                                    'team2': [player2.pk], 'winner': 'team1'})

        self.assertRedirects(response, reverse('gametracker:history'))
