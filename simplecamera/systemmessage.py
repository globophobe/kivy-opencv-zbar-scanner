from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

from .lib.resources import get_filename

Builder.load_file(get_filename("kv/systemmessage.kv"))


class SystemMessage(BoxLayout):
    pass
