# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from models import Game, GameMap, Player

admin.site.register(Game)
admin.site.register(GameMap)
admin.site.register(Player)
