# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.lang import Builder

from .lib.resources import get_filename
from .constants import WHITE_95, WHITE_15, LIGHT_GRAY_95

Builder.load_file(get_filename("kv/card.kv"))


class Card(BoxLayout):
    app = ObjectProperty()
    header_block = StringProperty()
    text_block = StringProperty()
    footer_block = StringProperty()
    font_opacity = NumericProperty(0)
    border_color = ObjectProperty(LIGHT_GRAY_95)
    background_color = ObjectProperty(WHITE_15)
    face_preview_opacity = NumericProperty(0)

    def start_scanning(self, *args):
        # Clear card text
        self.header_block = ""
        self.text_block = ""
        self.footer_block = ""
        self.app.is_scanning = True
        # After reinitialize scanning
        self.camera.is_request_active = False

    def show_card(self, background_color=WHITE_95):
        self.font_opacity = 1
        self.background_color = background_color

    def animate_background_color(self, color):
        # Creates an infinite loop if bound to the property
        animation = Animation(background_color=color, t="out_expo", duration=0.1)
        animation.start(self)

    def fade_out_card(self, transition="in_expo", duration=0.5):
        # Fade out face preview
        animation = Animation(face_preview_opacity=0, t=transition, duration=duration)
        # Fade out card
        animation &= Animation(
            background_color=WHITE_15, t=transition, duration=duration
        )
        # Fade out card text
        animation &= Animation(font_opacity=0, t=transition, duration=duration)
        animation.start(self)
        # Set callback
        animation.bind(on_complete=self.start_scanning)

    def blit_face(self, face):
        # Show face preview
        face_preview = self.ids["face_preview"]
        face_preview.blit_frame(face)
        animation = Animation(face_preview_opacity=1, t="out_expo", duration=0.25)
        animation.start(self)
