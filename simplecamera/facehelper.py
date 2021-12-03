from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from .constants import WASHED_BLUE_95
from .lib.resources import get_filename

Builder.load_file(get_filename("kv/facehelper.kv"))


class FaceHelper(BoxLayout):
    app = ObjectProperty()
    head_radius = NumericProperty(dp(240))
    font_color = ObjectProperty(WASHED_BLUE_95)
