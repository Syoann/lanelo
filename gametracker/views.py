from __future__ import unicode_literals

from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.utils import timezone
from django.urls import reverse

from gametracker.models import Game, Person, Identity, EloLog
from gametracker.forms import GameForm, ReplayForm, TeamsForm
from gametracker.utils import calc_team_elo, prob_winning, TeamBalancer
from gametracker.signals import update_elo


def index(request):
    persons = Person.objects.order_by('-elo')
    return render(request, "gametracker/index.html", {'person_list': persons})


def person_list(request):
    persons = Person.objects.order_by('-elo')
    total_n_games = Game.objects.filter(ranked=True).count()

    return render(request, 'gametracker/person_list.html', {'person_list': persons, "n_games": total_n_games})


class HistoryView(generic.ListView):
    model = Game
    template_name = "gametracker/history.html"

    def get_queryset(self):
        return Game.objects.order_by('-date').prefetch_related('team1', 'team2')


def person_detail(request, person_name):
    person = get_object_or_404(Person, name__iexact=person_name)

    (n_victories, n_defeats) = (0, 0)
    identities = Identity.objects.filter(person=person)

    victories = [game for game in Game.objects.all() if game.winners().filter(identity__in=identities).exists()]
    defeats = [game for game in Game.objects.all() if game.losers().filter(identity__in=identities).exists()]

    n_victories = len(victories)
    n_defeats = len(defeats)

    games = victories + defeats
    games.sort(key=lambda x: x.date)


    try:
        victory_ratio = n_victories * 100.0 / (n_victories + n_defeats)
    except ZeroDivisionError:
        victory_ratio = 0

    elo_history = EloLog.objects.filter(person__pk=person.pk).order_by('date')
    elos = [elolog.elo for elolog in elo_history]

    return render(request, 'gametracker/person_detail.html', {'person': person, 'victories': n_victories,
                                                              'defeats': n_defeats, 'ratio': victory_ratio,
                                                              'elos': elos, 'games': games})


def game_detail(request, pk):
    """Detailed view of a game"""
    game = get_object_or_404(Game, pk=pk)

    try:
        new_elolog = EloLog.objects.filter(date=game.date)[0]
        old_elolog = EloLog.objects.filter(date__lt=game.date, person=new_elolog.person).latest('date')
        var_elo = abs(old_elolog.elo - new_elolog.elo)
    except:
        var_elo = None
    return render(request, 'gametracker/game_detail.html', {'game': game,
                                                            'game_replay': game.replay,
                                                            'winners': game.winners(),
                                                            'losers': game.losers(),
                                                            'var_elo': var_elo})


def add_game(request):
    replay_form = ReplayForm(request.POST, request.FILES)

    if replay_form.is_valid():
        replay = replay_form.save(commit=False)
        replay.save()

        try:
            game_id = Game.objects.get(replay=replay).id
            return redirect(reverse('gametracker:game', kwargs={'pk': game_id}))
        except:
            return redirect(reverse('gametracker:duplicated_game'))

    return render(request, 'gametracker/add_game.html', {'form': ReplayForm()})


def duplicated_game(request):
    return render(request, 'gametracker/duplicated_game.html')


def manually_add_game(request):
    """Add a new game in the database"""
    if request.method == "POST":
        game_form = GameForm(request.POST)

        if game_form.is_valid():
            game = game_form.save(commit=False)
            game.date = timezone.now()
            game.save()

            game_form.save_m2m()
            update_elo(game.date)
            return redirect(reverse('gametracker:history'))

    return render(request, 'gametracker/manually_add_game.html', {'form': GameForm})


def build_orders(request):
    return render(request, 'gametracker/build_orders.html')


def update(request):
    update_elo()
    persons = Person.objects.order_by('-elo')
    return render(request, "gametracker/index.html", {'person_list': persons})


def balance_teams(request):
    if request.method == "POST":
        form = TeamsForm(request.POST)

        if form.is_valid() and len(form.cleaned_data["players"]) > 1:
            team_balancer = TeamBalancer(form.cleaned_data["players"])

            teams = team_balancer.get_teams()
            context = {'form': form}
            context.update({'team1': teams[0], 'team2': teams[1],
                            'elo_team1': calc_team_elo(teams[0]),
                            'elo_team2': calc_team_elo(teams[1])})

            teams_eq = team_balancer.get_balanced_teams()

            if teams_eq[0] not in teams:

                delta_elo = calc_team_elo(teams_eq[0]) - calc_team_elo(teams_eq[1])
                pw = prob_winning(delta_elo) * 100

                context.update({'team1eq': teams_eq[0], 'team2eq': teams_eq[1],
                                'pw_team1eq': pw,
                                'pw_team2eq': 100-pw})
            else:
                context.update({'team1eq': None, 'team2eq': None})

            # Add winning probability for teams
            delta_elo = calc_team_elo(teams[0]) - calc_team_elo(teams[1])
            pw = prob_winning(delta_elo) * 100

            if pw > 60 or pw < 40:
                color_cls = "is-danger"
            elif pw > 55 or pw < 45:
                color_cls = "is-warning"
            else:
                color_cls = "is-success"

            context.update({"pw_team1": pw,
                            "pw_team2": 100 - pw,
                            "color_cls": color_cls})

            return render(request, "gametracker/balance_teams.html", context)
        else:
            return render(request, "gametracker/balance_teams.html", {'form': form})
    else:
        form = TeamsForm()
        return render(request, "gametracker/balance_teams.html", {'form': form, 'team1': None, 'team2': None})
