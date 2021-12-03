from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout

from .constants import HD
from .lib.resources import get_filename

Builder.load_file(get_filename("kv/mainwindow.kv"))


class MainWindow(FloatLayout):
    card = ObjectProperty()

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        # Get keyboard
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        # Window size
        self.check_window_size(Window.size)

    def _keyboard_closed(self):
        """May be triggered by text inputs, so pass."""
        # self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        # self._keyboard = None
        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if modifiers and keycode:
            for modifier in modifiers:
                if "ctrl" in modifier.lower():
                    key = keycode[1]
                    if key == "s":
                        self.toggle_is_settings_menu_visible()
                    if key == "h":
                        self.toggle_is_scanning_area_highlighted()

    def toggle_is_face_recognition_active(self, *args):
        self.app.is_face_recognition_active = not self.app.is_face_recognition_active

    def toggle_is_scanning_area_highlighted(self, *args):
        self.app.is_scanning_area_highlighted = (
            not self.app.is_scanning_area_highlighted
        )

    def on_size(self, instance, size):
        self.check_window_size(size)
        self.set_card_pos(size)

    def check_window_size(self, size):
        """Although camera is half HD, minimum window size is HD."""
        width, height = size
        if width >= HD[0] and height >= HD[1]:
            self.app.is_minimum_size = True
        else:
            self.app.is_minimum_size = False

    def set_card_pos(self, size):
        window_width, window_height = size
        camera_width, camera_height = self.ids["camera"].size
        card_width, card_height = self.ids["card"].size
        # Head
        head_radius = self.ids["body"].head_radius
        # With arbitrary adjustments
        x = self.center_x + int(head_radius / 2) + int(card_width / 2) + dp(12.5)
        y = self.center_y - int(card_height / 2) - dp(50)
        self.ids["card"].pos = (x, y)
        self.ids["card_helper"].pos = (x, y)
