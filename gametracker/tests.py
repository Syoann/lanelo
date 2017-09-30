# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone

from models import Game, Player, Team
from views import EloCalculator, TeamBalancer

class GameTest(TestCase):
    def setUp(self):
        self.p1 = Player.objects.create(name="Foo", firstname="", lastname="", ngames=0, elo=2000)
        self.p2 = Player.objects.create(name="Bar", firstname="", lastname="", ngames=0, elo=1500)
        self.p3 = Player.objects.create(name="Oof", firstname="", lastname="", ngames=0, elo=2100)
        self.p4 = Player.objects.create(name="Rab", firstname="", lastname="", ngames=0, elo=1900)
        self.p5 = Player.objects.create(name="toto", firstname="", lastname="", ngames=0, elo=2500)
        self.p6 = Player.objects.create(name="tata", firstname="", lastname="", ngames=0, elo=1500)
        self.p7 = Player.objects.create(name="titi", firstname="", lastname="", ngames=0, elo=1400)
        self.p8 = Player.objects.create(name="tutu", firstname="", lastname="", ngames=0, elo=1200)


    def test_team_elo_1v1(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""
        elo_team1 = Team([self.p1]).get_elo()
        elo_team2 = Team([self.p2]).get_elo()
        
        self.assertEqual(elo_team1, 2000)
        self.assertEqual(elo_team2, 1500)


    def test_team_elo_2v2(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""

        elo_team1 = Team([self.p1, self.p2]).get_elo()
        elo_team2 = Team([self.p3, self.p4]).get_elo()

        self.assertEqual(elo_team1, 2050)
        self.assertEqual(elo_team2, 2300)

    def test_team_elo_3v3(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""

        elo_team1 = Team([self.p1, self.p2, self.p5]).get_elo()
        elo_team2 = Team([self.p3, self.p4, self.p6]).get_elo()

        self.assertEqual(round(elo_team1, 0), 2475)
        self.assertEqual(round(elo_team2, 0), 2309)

    def test_team_elo_4v4(self):
        """Test du calcul de l'elo de l'équipe. Cas basiques"""

        elo_team1 = Team([self.p1, self.p2, self.p5, self.p8]).get_elo()
        elo_team2 = Team([self.p3, self.p4, self.p6, self.p7]).get_elo()

        self.assertEqual(round(elo_team1, 0), 2400)
        self.assertEqual(round(elo_team2, 0), 2325)

    def test_pW(self):
        """Test probabilité de gagner (positif)"""
        elo_calc = EloCalculator(Team([self.p1, self.p2, self.p5, self.p8]),
                                 Team([self.p3, self.p4, self.p6, self.p7]))

        self.assertEqual(round(elo_calc.pW()["team1"]*100, 2), 66.61)
        self.assertEqual(round(elo_calc.pW()["team2"]*100, 2), 100-66.61)


    def test_pW_under50(self):
        """Test probabilité de gagner (négatif)"""
        elo_calc = EloCalculator(Team([self.p1, self.p2, self.p7, self.p8]),
                                 Team([self.p3, self.p4, self.p5, self.p6]))

        self.assertEqual(round(elo_calc.pW()["team1"]*100, 2), 1.24)
        self.assertEqual(round(elo_calc.pW()["team2"]*100, 2), 100-1.24)

    def test_K(self):
        elo_calc = EloCalculator(Team([self.p1]), Team([self.p2]))
        self.assertEqual(elo_calc.K(0), 25)
        self.assertEqual(round(elo_calc.K(10), 0), 20)
        self.assertEqual(elo_calc.K(100), 15)
        self.assertEqual(round(elo_calc.K(1000), 0), 10)

    def test_K_none(self):
        elo_calc = EloCalculator(Team([self.p1]), Team([self.p2]))
        self.assertRaises(ValueError, elo_calc.K, -1)

    def test_new_elo(self):
        elo_calc = EloCalculator(Team([self.p1]), Team([self.p3]), winner="team1")
        
        self.assertEqual(round(elo_calc.new_elo(self.p1), 0), 2018)
        self.assertEqual(round(elo_calc.new_elo(self.p3), 0), 2082)

        elo_calc = EloCalculator(Team([self.p1]), Team([self.p3]), winner="team2")

        self.assertEqual(round(elo_calc.new_elo(self.p1), 0), 1993)
        self.assertEqual(round(elo_calc.new_elo(self.p3), 0), 2107)

    def test_multiple_games(self):
        """Test que gagner en étant équipe 1 ou 2 n'a pas d'importance"""

        # p1 gagne en équipe 1
        p1_1st_game = Player.objects.create(name="Foo", firstname="", lastname="", ngames=0, elo=2100)
        p2_1st_game = Player.objects.create(name="Bar", firstname="", lastname="", ngames=0, elo=2000)

        elo_calc = EloCalculator(Team([p1_1st_game]), Team([p2_1st_game]), winner="team1")

        # p2 gagne en équipe 2
        p1_2nd_game_v1 = Player.objects.create(name="Foo", firstname="", lastname="", ngames=1, elo=elo_calc.new_elo(p1_1st_game))
        p2_2nd_game_v1 = Player.objects.create(name="Bar", firstname="", lastname="", ngames=1, elo=elo_calc.new_elo(p2_1st_game))

        elo_calc_v1 = EloCalculator(Team([p1_2nd_game_v1]), Team([p2_2nd_game_v1]), winner="team2")

        # p1 gagne en équipe 2
        p1_1st_game = Player.objects.create(name="Foo", firstname="", lastname="", ngames=0, elo=2100)
        p2_1st_game = Player.objects.create(name="Bar", firstname="", lastname="", ngames=0, elo=2000)    
        elo_calc = EloCalculator(Team([p2_1st_game]), Team([p1_1st_game]), winner="team2")

        # p2 gagne en équipe 1
        p1_2nd_game_v2 = Player.objects.create(name="Foo", firstname="", lastname="", ngames=1, elo=elo_calc.new_elo(p1_1st_game))
        p2_2nd_game_v2 = Player.objects.create(name="Bar", firstname="", lastname="", ngames=1, elo=elo_calc.new_elo(p2_1st_game))

        elo_calc_v2 = EloCalculator(Team([p2_2nd_game_v2]), Team([p1_2nd_game_v2]), winner="team1")

        self.assertEqual(elo_calc_v1.new_elo(p1_2nd_game_v1), elo_calc_v2.new_elo(p1_2nd_game_v2))
        self.assertEqual(elo_calc_v1.new_elo(p2_2nd_game_v1), elo_calc_v2.new_elo(p2_2nd_game_v2))

    def test_balancing_teams(self):
        self.p1.elo = 2001
        self.p2.elo = 1500
        self.p3.elo = 2000
        self.p4.elo = 1499

        team_balancer = TeamBalancer([self.p1, self.p4, self.p3, self.p2])
        teams = team_balancer.balance()

        self.assertEqual((self.p1, self.p4), teams["team1"].players)
        self.assertEqual((self.p2, self.p3), teams["team2"].players)

        
