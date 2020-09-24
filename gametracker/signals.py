import re
import os
import json
import logging
import subprocess

from datetime import datetime
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from gametracker.models import Game, GameReplay, GameMap, Person, Player, Identity, EloLog
from gametracker.utils import calc_team_elo, calculate_new_elo, generate_identicon


logger = logging.getLogger(__name__)


@receiver(post_save, sender=GameReplay)
def analyze_replay(sender, instance, *args, **kwargs):
    # Parse data
    basename = os.path.splitext(os.path.basename(instance.replay.name))[0]
    minimap_path = '/minimaps/' + basename + '.png'
    chronology_path = '/researches/' + basename + '.png'
    cmd = ' '.join(["/home/yoann/software/pyrecanalyst/examples/analyze.py",
                    "-i '" + instance.replay.path + "' -l fr",
                    "-m " + settings.MEDIA_ROOT + minimap_path,
                    "-r " + settings.MEDIA_ROOT + chronology_path])

    logger.debug(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    logger.debug(err)

    # Parse date in filename
    # AOE2HD style
    if instance.replay.path.endswith(".aoe2record"):
        reg = re.search("([0-9]{4})\.([0-9]{2})\.([0-9]{2}).([0-9]{2})([0-9]{2})([0-9]{2})", instance.replay.path)
    # AoFE style
    elif instance.replay.path.endswith(".mgz"):
        reg = re.search("([0-9]{4})(0[1-9]|1[1-2])([0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})", instance.replay.path)

    if reg:
        strdate = (reg.group(1) + "-" + reg.group(2) + "-" + reg.group(3) + " " +
                   reg.group(4) + ":" + reg.group(5) + ":" + reg.group(6))
        date = datetime.strptime(strdate, "%Y-%m-%d %H:%M:%S")
    else:
        date = timezone.now()

    # Read parsing output
    game_data = json.loads(out.decode('utf-8', errors='ignore').replace('\n', ''))

    # Add information to replay
    game_replay_queryset = GameReplay.objects.filter(pk=instance.pk)
    game_replay_queryset.update(game_version=game_data["version"])
    game_replay_queryset.update(game_type=game_data["type"])
    game_replay_queryset.update(speed=game_data["speed"])
    game_replay_queryset.update(difficulty=game_data["difficulty"])
    game_replay_queryset.update(population_limit=game_data["population_limit"])
    game_replay_queryset.update(minimap=minimap_path)
    game_replay_queryset.update(chronology=chronology_path)

    # Create teams
    teams = {}
    n_resign = {}
    number = 1
    for player_name in game_data["players"]:
        player_stats = game_data["players"][player_name]

        # Create a new player
        p = Player()
        p.civilization = player_stats["civilization"]
        p.number = number
        p.resign_time = player_stats["resign_time"]
        p.team = player_stats["team"]

        if p.team < 0:
            p.team = None

        teams.setdefault(p.team, []).append(p)

        # Count the number of resigns in each team
        n_resign[p.team] = n_resign.get(p.team, 0) + int(p.resign_time > 0)

        # Find player's identity
        identity, created = Identity.objects.get_or_create(pseudo=player_name)
        p.identity = identity

        p.save()
        number += 1

    # The winning team is the team with the lowest number of resigns
    winning_team = min(n_resign, key=n_resign.get)

    # Add map
    game_map, created = GameMap.objects.get_or_create(name=game_data["map"])

    if created:
        game_map.save()

    # Create a game with all the players
    try:
        game = Game.objects.get(date=date, game_map=game_map)
        print("WARNING: La partie existe déjà dans la base de données...")
    except Game.DoesNotExist:
        game = Game()
        game.date = date
        game.game_map = game_map
        game.ranked = False
        game.replay = game_replay_queryset.first()
        game.save()

        if len(teams.keys()) == 2:
            game.ranked = True
            if winning_team == sorted(teams.keys())[0]:
                game.winner = "team1"
            elif winning_team == sorted(teams.keys())[1]:
                game.winner = "team2"

            game.team1.add(*teams[sorted(teams.keys())[0]])
            game.team2.add(*teams[sorted(teams.keys())[1]])

        game.save()
        update_elo(game.date)


@receiver(post_delete, sender=GameReplay)
def auto_delete_mediafiles(sender, instance, *args, **kwargs):
    try:
        instance.replay.delete(save=False)
    except:
        logger.debug("Can't remove replay")
        logger.debug(instance.replay)

    try:
        instance.minimap.delete(save=False)
    except:
        logger.debug("Can't remove minimap")
        logger.debug(instance.minimap)

    try:
        instance.chronology.delete(save=False)
    except:
        logger.debug("Can't remove chronology")
        logger.debug(instance.chronology)


@receiver(pre_save, sender=Person)
def init_person(sender, instance, *args, **kwargs):
    """Initialize elo from initial elo"""
    if not instance.elo:
        instance.elo = instance.init_elo

    if not instance.avatar: # or not os.path.isfile(instance.avatar.path):
        name = instance.name
        out_name = '/avatars/' + name + '.png'
        generate_identicon(name, settings.MEDIA_ROOT + out_name)
        instance.avatar = out_name


@receiver(post_save, sender=Person)
def add_identity(sender, instance, created, *args, **kwargs):
    """Create a new identity corresponding to the person's name"""
    if created:
        try:
            identity = Identity.objects.select_related('person').get(pseudo=instance.name)

            if not identity.person:
                identity.person = instance
                identity.save()
        except Identity.DoesNotExist:
            identity = Identity(person=instance, pseudo=instance.name)
            identity.save()


@receiver(post_delete, sender=Game)
def post_delete_game(sender, instance, *args, **kwargs):
    if instance.replay:
        instance.replay.delete()
    update_elo(instance.date)


def update_elo(date=datetime.min):
    # Delete ELoLogs newer than the provided date
    elos_to_be_deleted = EloLog.objects.filter(date__gte=date)
    elos_to_be_deleted.delete()

    # Only get the queryset once, to avoid unnecessary calls to .save()
    persons = { p.name:p for p in Person.objects.all() }

    # Keep track of elo after each game
    elos = []

    # Init elo and number of games
    for person_name, person in persons.items():
        try:
            person_elos = EloLog.objects.filter(person=person)
            person.elo = person_elos.latest('date').elo
            person.ngames = person_elos.count() - 1  # First EloLog is init_elo
        except:
            person.elo = person.init_elo
            person.ngames = 0
            elos.append(EloLog(person=person, date=datetime.min, elo=person.init_elo))

    for game in Game.objects.filter(date__gte=date).order_by('date').prefetch_related('team1', 'team2').iterator():
        # We can't call the queryset directly, otherwise the elo is updated to the latest one
        # So here we select 'persons' that are in game.team1 and game.team2
        team1 = [ persons[name["identity__person__name"]] for name in game.team1.all().values("identity__person__name") if name["identity__person__name"] in persons ]
        team2 = [ persons[name["identity__person__name"]] for name in game.team2.all().values("identity__person__name") if name["identity__person__name"] in persons ]

        team1_elo = calc_team_elo(team1)
        team2_elo = calc_team_elo(team2)

        # Only update the elo if elo of both team1 and team2 have been calculated
        if game.ranked and team1_elo and team2_elo:
            delta_elo = team1_elo - team2_elo

            # Calculate each player's new elo
            for person in team1 + team2:
                if person in team1:
                    person.elo = calculate_new_elo(person.elo, delta_elo, game.winner == "team1")
                else:
                    person.elo = calculate_new_elo(person.elo, -delta_elo, game.winner == "team2")
                elos.append(EloLog(person=person, date=game.date, elo=person.elo))
                person.ngames += 1

    # Commit changes
    EloLog.objects.bulk_create(elos)

    for person_name, person in persons.items():
        person.save()
