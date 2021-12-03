# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import numpy as np
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout

from .lib.resources import get_filename

Builder.load_file(get_filename("kv/debugcharacter.kv"))


class DebugCharacter(AnchorLayout):
    app = ObjectProperty()
    header = StringProperty("Info")
    message = StringProperty()

    def __init__(self, *args, **kwargs):
        super(DebugCharacter, self).__init__(*args, **kwargs)
        # Numpy
        self.fps_samples = np.array([])
        # Update fps twice a second.
        Clock.schedule_interval(self.get_fps, 1)

    def on_is_active(self, instance, value):
        if value is not None:
            if value:
                opacity = 1
            else:
                opacity = 0
            # Start animation
            animation = Animation(opacity=opacity, t="out_expo", duration=0.25)
            animation.start(self)

    def get_fps(self, *args):
        # Get FPS
        fps = round(Clock.get_fps())
        # Calculate average
        self.calculate_fps_avg(fps)
        # Update condition
        self.set_message(fps)

    def calculate_fps_avg(self, fps):
        # One minute
        max_samples = 60
        total_samples = self.fps_samples.shape[0]
        if total_samples == max_samples:
            mean = np.mean(self.fps_samples)
            fps_avg = round(mean)
            # Not a property, so always trigger
            if fps_avg <= 5:
                self.app.is_debug_character_visible = True
            self.fps_avg = int(fps_avg)
            self.fps_samples = np.delete(self.fps_samples, [0])
        self.fps_samples = np.append(self.fps_samples, [fps])

    def set_message(self, fps):
        cpu = round(self.app.cpu)
        cpu_string = "{}％".format(str(cpu))
        fps_string = str(fps)
        failure_string = self.get_failure_message()
        dark_red = "[color=E7040F]{}[/color]"
        if cpu >= 90:
            cpu_string = dark_red.format(cpu_string)
        if fps <= 10:
            fps_string = dark_red.format(fps_string)
        msg = "CPU {}\nFPS  {}\n{}"
        self.message = msg.format(cpu_string, fps_string, failure_string)

    def get_failure_message(self):
        failures = self.app.total_connection_errors
        failure_string = "failure {}".format(str(failures))
        if failures > 0:
            if failures >= 5:
                self.app.is_debug_character_visible = True
                failure_string = "[color=E7040F]{}[/color]".format(failure_string)
        return failure_string
