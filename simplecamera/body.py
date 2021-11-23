from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty

from .constants import BLUE_95, GOLD_95
from .lib.resources import get_filename

Builder.load_file(get_filename("kv/body.kv"))


class Body(BoxLayout):
    head_radius = NumericProperty(dp(240))
    color = ObjectProperty(BLUE_95)

    def on_color(self, instance, value):
        if value == GOLD_95:
            # Immediately, set callback
            Clock.schedule_once(self.reset_color, 0.15)

    def reset_color(self, *args):
        self.color = BLUE_95
