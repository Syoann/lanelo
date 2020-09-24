import math
import itertools
import subprocess
import sys


class TeamBalancer:
    """Create two balanced teams from a list of players"""
    def __init__(self, players):
        self.players = players

    def _partition_players(self, size):
        """Split players in two teams: one of size 'size' and the other of size N - 'size'"""
        min_delta = None
        teams = []

        # Explore all combinations with 1st group of size 'size'
        for players in itertools.combinations(self.players, size):
            team1 = list(set(players))
            team2 = list(set(self.players) - set(players))

            diff = abs(calc_team_elo(team1) - calc_team_elo(team2))

            if min_delta is None or diff < min_delta:
                teams = [team1, team2]
                min_delta = diff

        return teams

    def get_teams(self):
        """Return the most balanced teams according to the algorithm"""
        s_teams = [self._partition_players(size) for size in range(1, len(self.players) // 2 + 1)]
        deltas = [abs(calc_team_elo(couple[0]) - calc_team_elo(couple[1])) for couple in s_teams]
        return s_teams[deltas.index(min(deltas))]

    def get_balanced_teams(self):
        """Return the most balanced teams with a similar number of players in both teams"""
        return self._partition_players(len(self.players) // 2)


def calc_team_elo(team):
    """Calculate elo rating for a team"""
    elos = []
    for player in team:
        if player.get_elo():
            elos.append(player.get_elo())
        # If a player has no elo, he is not taken into account in the team elo
        else:
            print("WARNING: no elo for player '" + player.identity.pseudo + "' !")

    return team_elo_formula(elos)


def team_elo_formula(elos):
    """Team elo formula"""
    # Corrective factor for multiplayer teams
    MP_FACTOR = 300

    if not elos:
        return None

    return sum(elos) / len(elos) + MP_FACTOR * math.log(len(elos), 2)


def prob_winning(delta_elo):
    """Returns the probability of winning given the elo difference"""
    return 1 / (1 + 10**(-delta_elo / 250))


def calculate_new_elo(elo, delta_elo, winner=True):
    """Returns the new elo given the former elo and the elo difference"""
    K = 20
    return round(elo + K * (int(winner) - prob_winning(delta_elo)))


def generate_identicon(name, output):
    cmd = "node /home/yoann/software/generate.js {} {}".format(name, output)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    if p.returncode != 0:
        sys.stderr.write(p.stderr.decode())
        raise Exception("Impossible de créer l'icone pour le joueur {}".format(name))
