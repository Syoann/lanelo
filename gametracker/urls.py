from django.conf.urls import url
from . import views

app_name = "gametracker"
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^index$', views.index, name='index'),
    url(r'^addgame$', views.add_game, name="add_game"),
    url(r'^players$', views.PlayersView.as_view(), name='players'),
    url(r'^games$', views.HistoryView.as_view(), name='history'),
    url(r'^teams$', views.balance_teams, name='balance_teams'),
]
