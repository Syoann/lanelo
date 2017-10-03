#! /usr/bin/env python
# -*- conding: utf-8 -*-

import math

def calculate_team_elo(team):
    """Calculate elo rating for a team"""
    # Corrective factor for multiplayer teams
    MP_FACTOR = 300
    elos = [player.elo for player in team]
    return float(sum(elos)) / len(team) + MP_FACTOR * math.log(len(team), 2)

def prob_winning(delta_elo):
    """Returns the probability of winning given the elo difference"""
    return 1 / (1 + 10**(-delta_elo / 250))

