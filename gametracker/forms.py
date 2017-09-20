# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Game, GameMap, Player

class GameForm(forms.ModelForm):
    game_map = forms.ModelChoiceField(queryset=GameMap.objects.order_by('name'), required=False, label="Carte")
    team1 = forms.ModelMultipleChoiceField(queryset=Player.objects.order_by('-elo'), label="Équipe 1")
    team2 = forms.ModelMultipleChoiceField(queryset=Player.objects.order_by('-elo'), label="Équipe 2")

    class Meta:
        model = Game
        exclude = ["date"] 
        labels = {"winner": "Gagnant"}


class TeamsForm(forms.Form):
   players = forms.ModelMultipleChoiceField(queryset=Player.objects.order_by('-elo'), label="Joueurs présents")
