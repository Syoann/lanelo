from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "gametracker"
urlpatterns = [
    url(r'^$', views.index, name='index0'),
    url(r'^index$', views.index, name='index'),
    url(r'^addgame$', views.add_game, name="add_game"),
    url(r'^creategame$', views.manually_add_game, name="manually_add_game"),
    url(r'^players$', views.person_list, name='players'),
    url(r'^player/(?P<person_name>.+$)', views.person_detail, name='player'),
    url(r'^games$', views.HistoryView.as_view(), name='history'),
    url(r'^game/(?P<pk>[0-9]+)$', views.game_detail, name='game'),
    url(r'^teams$', views.balance_teams, name='balance_teams'),
    url(r'^build-orders$', views.build_orders, name='build_orders'),
    url(r'^update$', views.update, name='update'),
    url(r'^error-dup-game$', views.duplicated_game, name='duplicated_game'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
