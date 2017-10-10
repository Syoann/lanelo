from django.db.models.signals import post_delete, m2m_changed
from django.dispatch import receiver

from models import Game, Player
from utils import calculate_team_elo


@receiver(post_delete, sender=Game)
def post_delete_elo(sender, instance, *args, **kwargs):
    update_elo()


@receiver(m2m_changed, sender=Game.team1.through)
def post_save_elo1(sender, instance, *args, **kwargs):
    if instance.team1.all() and instance.team2.all():
        instance.delta_elo = calculate_team_elo(instance.team1.all()) - calculate_team_elo(instance.team2.all())
        update_elo()


@receiver(m2m_changed, sender=Game.team2.through)
def post_save_elo2(sender, instance, *args, **kwargs):
    if instance.team1.all() and instance.team2.all():
        instance.delta_elo = calculate_team_elo(instance.team1.all()) - calculate_team_elo(instance.team2.all())
        update_elo()


def update_elo():
    """Recalculate elo for all players in the database"""
    players = Player.objects.all()

    for player in players:
        player.elo = player.init_elo
        player.ngames = 0

    for game in Game.objects.all():
        team1 = []
        team2 = []
        for player in players:
            if player in game.team1.all():
                team1.append(player)
            if player in game.team2.all():
                team2.append(player)

        game.delta_elo = calculate_team_elo(team1) - calculate_team_elo(team2)
        for player in players:
            if game.has_player(player):
                player.play(game)

    for player in players:
        player.elo = round(player.elo, 0)
        player.save()
