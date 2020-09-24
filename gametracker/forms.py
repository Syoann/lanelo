from django import forms
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Field

from gametracker.models import (Game, GameMap, GameReplay,
                                Player, Identity, Person)

import logging

logger = logging.getLogger(__name__)

class CustomCheckbox(forms.ModelMultipleChoiceField):
    template = 'templates/custom_checkbox.html'


class GameForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = 'creategame'
        self.helper.add_input(Submit('submit', 'Ajouter', css_class="button is-success"))

    game_map = forms.ModelChoiceField(queryset=GameMap.objects.order_by('name'),
                                      required=False, label=_("Carte"))

    # Create players from Persons because Game only uses Player, not Person
    # So we create a player corresponding to each person and present them to selection
    team1 = []
    team2 = []
    for person in Person.objects.order_by('-elo'):
        identity, created = Identity.objects.get_or_create(person=person, pseudo=person.name)

        if created:
            identity.save()

        try:
            player, created = Player.objects.get_or_create(identity=identity, team=1)
            if created:
                player.save()
        except Player.MultipleObjectsReturned:
            player = Player.objects.filter(identity=identity, team=1).first()

        team1.append(player.pk)

        try:
            player2, created = Player.objects.get_or_create(identity=identity, team=2)
            if created:
                player.save()
        except Player.MultipleObjectsReturned:
            player2 = Player.objects.filter(identity=identity, team=2).first()

        team2.append(player2.pk)

    team1 = forms.ModelMultipleChoiceField(queryset=Player.objects.filter(pk__in=team1).order_by('-identity__person__elo'),
                                           label=_("Vainqueurs"))
    team2 = forms.ModelMultipleChoiceField(queryset=Player.objects.filter(pk__in=team2).order_by('-identity__person__elo'),
                                           label=_("Perdants"))

    class Meta:
        model = Game
        exclude = ["date", "winner", "ranked", "replay"]


class ReplayForm(forms.ModelForm):

    class Meta:
        model = GameReplay
        exclude = ["minimap", "speed", "difficulty"]


class TeamsForm(forms.Form):
    players = forms.ModelMultipleChoiceField(queryset=Person.objects.order_by('-elo'),
                                             label=_("Joueurs présents"),
                                             widget=forms.CheckboxSelectMultiple(attrs={'class': 'switch is-rounded is-success'}))

    def __init__(self, *args, **kwargs):
        super(TeamsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = 'teams'
        self.helper.label_class = 'form-label'
        self.helper.form_show_labels = False
        self.helper.add_input(Submit('submit', 'Valider', css_class="button is-success button-centered"))
