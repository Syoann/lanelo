# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import generic
from django.utils import timezone

from .models import Game, GameMap, Player, TeamBalancer, EloCalculator
from .forms import GameForm, TeamsForm

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
    
        if form.is_valid():
            team_balancer = TeamBalancer(form.cleaned_data["players"])

            balance_result = team_balancer.balance()

            context = {'form': form}
            context.update(balance_result)

            # Add winning probability for teams
            elo_calc = EloCalculator(balance_result["team1"], balance_result["team2"])
            pw = elo_calc.pW()
            context.update({"pw_team1": pw["team1"] * 100, "pw_team2": pw["team2"] * 100})

            return render(request, "gametracker/balance_teams.html", context)
    else:
        form = TeamsForm()
        return render(request, "gametracker/balance_teams.html", {'form': form})
       
    def form_valid(self, form):
        return True

def add_game(request):
    if request.method == "POST":
        form = GameForm(request.POST)

        if form.is_valid():
            game = form.save(commit=False)
            game.date = timezone.now()
            game.save()
            form.save_m2m()
 
            elo_calc = EloCalculator(game.team1.all(), game.team2.all(), game.winner)

            # Update players
            for player in game.team1.all() + game.team2.all():
                player.ngames += 1
                player.elo = elo_calc.new_elo(player)
                player.save()

            return redirect('/gametracker/games')
    else:
        form = GameForm()
    return render(request, "gametracker/add_game.html", {'form': form})

