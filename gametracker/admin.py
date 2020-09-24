from __future__ import unicode_literals
from django.contrib import admin
from gametracker.models import (Game, GameReplay, GameMap, Person,
                                Identity, EloLog)


class PersonAdmin(admin.ModelAdmin):
    exclude = ('elo', 'ngames')


admin.site.site_header = ('Administration de Lan Elo Tracker')
admin.site.index_title = ('Lan Elo Tracker')

admin.site.register(Game)
admin.site.register(GameReplay)
admin.site.register(GameMap)
admin.site.register(Person, PersonAdmin)
admin.site.register(Identity)
admin.site.register(EloLog)
