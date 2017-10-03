# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone

from models import Game, Player, PlayerGameStats, GameMap, prob_winning, calculate_team_elo
from views import TeamBalancer
from utils import *
from . import factories


class GameTest(TestCase):
    def setUp(self):
        elos = [2000, 1500, 2100, 1900, 2500, 1500, 1400, 1200]
        self.players = [factories.PlayerFactory(elo=elo) for elo in elos]

        self.game_test_pw = factories.GameFactory.create(team1=(self.players[0],
                                                                self.players[1],
                                                                self.players[4],
                                                                self.players[7]),
                                                         team2=(self.players[2],
                                                                self.players[3],
                                                                self.players[5],
                                                                self.players[6]))
        self.game_test_pw2 = factories.GameFactory.create(team1=(self.players[0],
                                                                 self.players[1],
                                                                 self.players[6],
                                                                 self.players[7]),
                                                          team2=(self.players[2],
                                                                 self.players[3],
                                                                 self.players[4],
                                                                 self.players[5]))

    def test_str_gamemap(self):
        names = ("Arabia", "")

        for name in names:
            gmap = GameMap.objects.create(name=name)
            self.assertEqual(str(gmap), name)

    def test_str_player(self):
        player = factories.PlayerFactory(name="Foo")
        self.assertEqual(str(player), "Foo")

    def test_str_game(self):
        dt = timezone.now()
        self.assertEqual(str(factories.GameFactory.create(date=dt)), str(dt))

    def test_team_elo_1v1(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = calculate_team_elo([self.players[0]])
        elo_team2 = calculate_team_elo([self.players[1]])

        self.assertEqual(elo_team1, self.players[0].elo)
        self.assertEqual(elo_team2, self.players[1].elo)

    def test_team_elo_2v2(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = calculate_team_elo([self.players[0], self.players[1]])
        elo_team2 = calculate_team_elo([self.players[2], self.players[3]])

        self.assertEqual(elo_team1, 2050)
        self.assertEqual(elo_team2, 2300)

    def test_team_elo_3v3(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = calculate_team_elo([self.players[0], self.players[1], self.players[4]])
        elo_team2 = calculate_team_elo([self.players[2], self.players[3], self.players[5]])

        self.assertEqual(round(elo_team1, 0), 2475)
        self.assertEqual(round(elo_team2, 0), 2309)

    def test_team_elo_4v4(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = calculate_team_elo([self.players[0], self.players[1],
                                        self.players[4], self.players[7]])
        elo_team2 = calculate_team_elo([self.players[2], self.players[3],
                                        self.players[5], self.players[6]])

        self.assertEqual(round(elo_team1, 0), 2400)
        self.assertEqual(round(elo_team2, 0), 2325)

    def test_prob_winning(self):
        """Test probabilité de gagner (positif)"""
        team1 = self.game_test_pw.team1.all()
        team2 = self.game_test_pw.team2.all()

        self.assertEqual(round(prob_winning(calculate_team_elo(team1) - calculate_team_elo(team2)) * 100, 2), 66.61)
        self.assertEqual(round(prob_winning(calculate_team_elo(team2) - calculate_team_elo(team1)) * 100, 2), 33.39)

    def test_prob_winnng_under50(self):
        """Test probabilité de gagner (négatif)"""
        team1 = self.game_test_pw2.team1.all()
        team2 = self.game_test_pw2.team2.all()

        # Probability is the same for everyone in the team
        self.assertEqual(round(prob_winning(calculate_team_elo(team1) - calculate_team_elo(team2)) * 100, 2), 1.24)
        self.assertEqual(round(prob_winning(calculate_team_elo(team2) - calculate_team_elo(team1)) * 100, 2), 98.76)

    def test_k(self):
        player = self.players[0]
        self.assertEqual(player._k(), 25)

        player.ngames = 10
        self.assertEqual(round(player._k(), 0), 20)

        player.ngames = 100
        self.assertEqual(player._k(), 15)

        player.ngames = 1000
        self.assertEqual(round(player._k(), 0), 10)

        player.ngames = -1
        self.assertRaises(ValueError, player._k)

    def test_player_game_stats(self):
        """Teste l'instanciation de la classe PlayerGameStats"""
        game = factories.GameFactory.create(team1=[self.players[0]], team2=[self.players[2]])
        self.assertRaises(ValueError, PlayerGameStats, self.players[1], game)

        pgs = PlayerGameStats(self.players[0], game)
        self.assertEqual(pgs.won, True)
        self.assertEqual(pgs.team[0].name, self.players[0].name)
        self.assertEqual(pgs.ennemy_team[0].name, self.players[2].name)

    def test_get_elo_after(self):
        game = factories.GameFactory.create(team1=(self.players[0],),
                                            team2=(self.players[2],), winner="team1")
        p1_stats = PlayerGameStats(self.players[0], game)
        p2_stats = PlayerGameStats(self.players[2], game)

        self.assertEqual(round(p1_stats.get_elo_after(), 0), 2018)
        self.assertEqual(round(p2_stats.get_elo_after(), 0), 2082)

        game = factories.GameFactory.create(team1=(self.players[0],),
                                            team2=(self.players[2],), winner="team2")
        p1_stats = PlayerGameStats(self.players[0], game)
        p2_stats = PlayerGameStats(self.players[2], game)

        self.assertEqual(round(p1_stats.get_elo_after(), 0), 1993)
        self.assertEqual(round(p2_stats.get_elo_after(), 0), 2107)

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
        game1 = factories.GameFactory.create(team1=(player1,), team2=(player2,), winner="team1")
        player1_stats = PlayerGameStats(player1, game1)
        player2_stats = PlayerGameStats(player2, game1)

        player1.elo = player1_stats.get_elo_after()
        player2.elo = player2_stats.get_elo_after()

        player1.ngames += 1
        player2.ngames += 1

        # p2 gagne en équipe 2
        game2 = factories.GameFactory.create(team1=(player1,), team2=(player2,), winner="team2")
        player1_stats = PlayerGameStats(player1, game2)
        player2_stats = PlayerGameStats(player2, game2)

        player1.elo = player1_stats.get_elo_after()
        player2.elo = player2_stats.get_elo_after()

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
        game1 = factories.GameFactory.create(team1=(player2,), team2=(player1,), winner="team2")
        player1_stats = PlayerGameStats(player1, game1)
        player2_stats = PlayerGameStats(player2, game1)

        player1.elo = player1_stats.get_elo_after()
        player2.elo = player2_stats.get_elo_after()

        player1.ngames += 1
        player2.ngames += 1

        # p2 gagne en équipe 1
        game2 = factories.GameFactory.create(team1=(player2,), team2=(player1,), winner="team1")
        player1_stats = PlayerGameStats(player1, game2)
        player2_stats = PlayerGameStats(player2, game2)

        player1.elo = player1_stats.get_elo_after()
        player2.elo = player2_stats.get_elo_after()

        elo_p1_2 = player1.elo
        elo_p2_2 = player2.elo

        self.assertEqual(elo_p1_1, elo_p1_2)
        self.assertEqual(elo_p2_1, elo_p2_2)

    def test_balancing_teams(self):
        elos = [2001, 1500, 2000, 1499]
        players = [factories.PlayerFactory(elo=elo) for elo in elos]

        team_balancer = TeamBalancer([players[0], players[1], players[2], players[3]])
        teams = team_balancer.get_teams()

        self.assertEqual([players[0], players[3]], teams[0])
        self.assertEqual([players[1], players[2]], teams[1])

        bteams = team_balancer.get_balanced_teams()

        self.assertEqual(teams, bteams)


# Test views
from django.test import Client


class TestViews(TestCase):
    def test_pages(self):
        """Test that all pages are available"""
        pages = ('', '/index', '/games', '/addgame', '/players', '/teams')
        c = Client()

        for page in pages:
            response = c.get(page)
            self.assertEqual(response.status_code, 200)

    def test_team_balancing_page(self):
        """Test that team balancing return code after form completion is 200"""
        c = Client()
        player1 = factories.PlayerFactory(elo=2000)
        player2 = factories.PlayerFactory(elo=2000)

        response = c.post("/teams", {'players': [player1.pk, player2.pk]})
        response = c.post("/teams", {'players': [player1.pk]})

        self.assertEqual(response.status_code, 200)
