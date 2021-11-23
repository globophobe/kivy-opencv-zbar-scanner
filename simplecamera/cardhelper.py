from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.lang import Builder

from .lib.resources import get_filename

Builder.load_file(get_filename("kv/cardhelper.kv"))


class CardHelper(BoxLayout):
    app = ObjectProperty()
