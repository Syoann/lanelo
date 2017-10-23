# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.utils import timezone
from django.urls import reverse

from .models import Game, Player, TeamBalancer
from .forms import GameForm, ReplayForm, TeamsForm
from utils import calculate_team_elo, prob_winning


def index(request):
    players = Player.objects.order_by('-elo')
    return render(request, "gametracker/index.html", {'player_list': players})


class PlayersView(generic.ListView):
    model = Player

    def get_queryset(self):
        return Player.objects.order_by('-elo')


class HistoryView(generic.ListView):
    model = Game
    template_name = "gametracker/history.html"

    def get_queryset(self):
        return Game.objects.order_by('-date')


def player_detail(request, player_name):
    player = get_object_or_404(Player, name__iexact=player_name)

    (n_victories, n_defeats) = (0, 0)
    for game in Game.objects.all():
        if game.has_player(player):
            if player.has_won(game):
                n_victories += 1
            else:
                n_defeats += 1

    try:
        victory_ratio = n_victories * 100.0 / (n_victories + n_defeats)
    except ZeroDivisionError:
        victory_ratio = 0

    return render(request, 'gametracker/player_detail.html', {'player': player, 'victories': n_victories,
                                                              'defeats': n_defeats, 'ratio': victory_ratio})


def game_detail(request, pk):
    """Detailed view of a game"""
    game = get_object_or_404(Game, pk=pk)
    return render(request, 'gametracker/game_detail.html', {'game': game, 'winners': game.winners(),
                                                            'losers': game.losers()})


def add_game(request):
    """Add a new game in the database"""
    if request.method == "POST":
        game_form = GameForm(request.POST)
        replay_form = ReplayForm(request.POST, request.FILES)

        if game_form.is_valid():
            game = game_form.save(commit=False)
            game.date = timezone.now()
            game.save()
            game_form.save_m2m()

            return redirect(reverse('gametracker:history'))

        if replay_form.is_valid():
            return redirect(reverse('gametracker:history'))
    else:
        game_form = GameForm()
        replay_form = ReplayForm()
    return render(request, 'gametracker/add_game.html', {'form': game_form, 'replay_form': replay_form})


def balance_teams(request):
    if request.method == "POST":
        form = TeamsForm(request.POST)

        if form.is_valid() and len(form.cleaned_data["players"]) > 1:
            team_balancer = TeamBalancer(form.cleaned_data["players"])

            teams = team_balancer.get_teams()
            context = {'form': form}
            context.update({'team1': teams[0], 'team2': teams[1],
                            'elo_team1': calculate_team_elo(teams[0]),
                            'elo_team2': calculate_team_elo(teams[1])})

            teams_eq = team_balancer.get_balanced_teams()
            if teams_eq[0] not in teams:
                context.update({'team1eq': teams_eq[0], 'team2eq': teams_eq[1],
                                'elo_team1eq': calculate_team_elo(teams_eq[0]),
                                'elo_team2eq': calculate_team_elo(teams_eq[1])})
            else:
                context.update({'team1eq': None, 'team2eq': None})

            # Add winning probability for teams
            delta_elo = calculate_team_elo(teams[0]) - calculate_team_elo(teams[1])
            pw = prob_winning(delta_elo) * 100
            context.update({"pw_team1": pw,
                            "pw_team2": 100 - pw})

            return render(request, "gametracker/balance_teams.html", context)
        else:
            return render(request, "gametracker/balance_teams.html", {'form': form})
    else:
        form = TeamsForm()
        return render(request, "gametracker/balance_teams.html", {'form': form, 'team1': None, 'team2': None})
