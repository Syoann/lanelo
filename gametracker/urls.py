from django.conf.urls import url
from . import views

app_name = "gametracker"
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^index$', views.index, name='index'),
    url(r'^addgame$', views.add_game, name="add_game"),
    url(r'^players$', views.PlayersView.as_view(), name='players'),
    url(r'^player/(?P<player_name>\w+)$', views.player_detail, name='player'),
    url(r'^games$', views.HistoryView.as_view(), name='history'),
    url(r'^game/(?P<pk>[0-9]+)$', views.game_detail, name='game'),
    url(r'^teams$', views.balance_teams, name='balance_teams'),
]
