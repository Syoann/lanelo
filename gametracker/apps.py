# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class GametrackerConfig(AppConfig):
    name = 'gametracker'

    def ready(self):
        import gametracker.signals
