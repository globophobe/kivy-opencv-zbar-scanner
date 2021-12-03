# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from datetime import datetime

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.anchorlayout import AnchorLayout

from .lib.resources import get_filename

Builder.load_file(get_filename("kv/simpleclock.kv"))


class SimpleClock(AnchorLayout):
    current_time = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super(SimpleClock, self).__init__(*args, **kwargs)
        # Update time every second
        Clock.schedule_interval(self.update_current_time, 1)

    def update_current_time(self, dt):
        self.current_time = datetime.now()  # Local time, not UTC
        self.ids["current_time"].text = "{}:{}:{}".format(
            str(self.current_time.hour).zfill(2),
            str(self.current_time.minute).zfill(2),
            str(self.current_time.second).zfill(2),
        )
