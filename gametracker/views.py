# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import redirect, render
from django.views import generic
from django.utils import timezone
from django.urls import reverse

from .models import Game, Player, TeamBalancer
from .forms import GameForm, TeamsForm
from utils import calculate_team_elo, prob_winning


# Create your views here.
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
        return render(request, "gametracker/balance_teams.html", {'form': form})


def add_game(request):
    """Add a new game in the database"""
    if request.method == "POST":
        form = GameForm(request.POST)

        if form.is_valid():
            game = form.save(commit=False)
            game.date = timezone.now()
            game.save()
            form.save_m2m()

            return redirect(reverse('gametracker:history'))
    else:
        form = GameForm()
    return render(request, 'gametracker/add_game.html', {'form': form})
