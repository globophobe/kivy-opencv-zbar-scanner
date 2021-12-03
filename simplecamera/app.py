from datetime import datetime

import cv2
from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivymd.theming import ThemeManager

from .constants import HD
from .mainwindow import MainWindow


class SimpleCamera(App):
    capture_request = ObjectProperty(allownone=True)
    capture_init = ObjectProperty(allownone=True)
    cpu = NumericProperty(0)

    scanner_name = StringProperty()

    https = BooleanProperty(True)
    domain = StringProperty()
    token = StringProperty()
    # Initially None
    settings = ObjectProperty()
    is_settings_valid = BooleanProperty()

    url = StringProperty()
    total_connection_errors = NumericProperty(0)

    can_init_capture = BooleanProperty(False)
    capture = ObjectProperty(allownone=True)

    is_hd = BooleanProperty(True)
    is_minimum_size = BooleanProperty(False)
    is_scanning = BooleanProperty(False)

    is_settings_menu_visible = BooleanProperty(False)
    is_secondary_camera = BooleanProperty(False)
    is_left_scanning_active = BooleanProperty()
    is_face_detection_active = BooleanProperty()
    is_face_helper_active = BooleanProperty(False)
    is_face_recognition_active = BooleanProperty()
    is_scanning_area_highlighted = BooleanProperty(False)

    is_debug_character_visible = BooleanProperty()
    debug_character_icon = StringProperty()
    debug_character_message = StringProperty()

    is_system_message_visible = BooleanProperty(False)
    system_message_header = StringProperty("起動")
    system_message_text = StringProperty("お待ちください。")

    theme_cls = ThemeManager()

    def __init__(self, https=True, settings={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.https = https
        # Settings
        self.settings = settings
        # Update cpu twice a second.
        Clock.schedule_interval(self.get_cpu, 0.5)

    def on_domain(self, instance, domain):
        self.url = self.get_url(domain)

    def get_url(self, domain):
        if self.https:
            url = "https://{}/".format(domain)
        else:
            url = "http://{}/".format(domain)
        return url

    def get_headers(self, token=None, content_type=None):
        if not token:
            token = self.token
        headers = {
            "Authorization": "Token {}".format(token),
            "X-Requested-With": "XMLHttpRequest",
        }
        if content_type:
            headers["Content-type"] = content_type
        return headers

    def on_is_settings_valid(self, instance, is_settings_valid):
        if is_settings_valid:
            self.can_init_capture = True
            self.system_message_header = "起動"
            self.system_message_text = "お待ちください。"
        else:
            self.invalid_settings()

    def invalid_settings(self):
        self.release_capture()
        self.can_init_capture = False
        self.system_message_header = "設定"
        self.system_message_text = "インターネットの接続がありません。\nまたは、ドメイン名とパスワードの\n設定が間違いっています。"

    def get_cpu(self, *args):
        self.cpu = None

    def on_cpu(self, instance, cpu):
        # Is token valid?
        if self.can_init_capture:
            # Is there a capture device?
            if not self.capture and self.capture_request is None and self.is_hd:
                self.capture_request = datetime.now()
        # Is capture requested?
        if self.capture_request:
            # is window minimum size and cpu 50% or less?
            if self.is_minimum_size and cpu <= 50.0:
                # Get capture
                self.get_capture()
            else:
                elapsed_time = datetime.now() - self.capture_request
                # Is elapsed time greater than 5 seconds?
                if elapsed_time.total_seconds() >= 5:
                    # Get capture
                    self.get_capture()

    def on_is_hd(self, instance, is_hd):
        if not is_hd:
            self.system_message_header = "カメラ"
            self.system_message_text = "必要な解像度は1280x720です。"
            self.release_capture()

    def on_is_minimum_size(self, instance, is_minimum_size):
        if is_minimum_size:
            self.system_message_header = "起動"
            self.system_message_text = "お待ちください。"
        else:
            self.system_message_header = "画面"
            self.system_message_text = "最小画面サイズは1280x720です。"
            self.release_capture()

    def on_is_secondary_camera(self, *args):
        self.system_message_header = "カメラ"
        self.system_message_text = "カメラを変更しています。"
        self.release_capture()

    def get_capture(self, *args):
        width, height = HD
        fps = 30
        device = 1 if self.is_secondary_camera else 0
        capture = cv2.VideoCapture(device)
        capture.set(3, width)  # CV_CAP_PROP_FRAME_WIDTH
        capture.set(4, height)  # CV_CAP_PROP_FRAME_HEIGHT
        capture.set(5, fps)  # CV_CAP_PROP_FPS
        self.capture = capture
        # Success
        self.capture_request = None
        self.capture_init = datetime.now()
        self.is_scanning = True
        self.system_message_header = ""
        self.system_message_text = ""

    def release_capture(self):
        # Capture was initialized
        if self.capture is not None:
            self.capture.release()
            self.capture = None
            self.capture_init = None
            self.is_scanning = False

    def build(self):
        # Subclasses
        Factory.register("KivyOpenCVCamera", module="simplecamera.camera")
        Factory.register("KivyNumpyImage", module="simplecamera.numpyimage")
        # App classes
        Factory.register("AppSettings", module="simplecamera.appsettings")
        Factory.register("DebugCharacter", module="simplecamera.debugcharacter")
        Factory.register("SimpleClock", module="simplecamera.simpleclock")
        Factory.register("CameraPreview", module="simplecamera.camerapreview")
        Factory.register("Body", module="simplecamera.body")
        Factory.register("FaceHelper", module="simplecamera.facehelper")
        Factory.register("Card", module="simplecamera.card")
        Factory.register("CardHelper", module="simplecamera.cardhelper")
        Factory.register("SystemMessage", module="simplecamera.systemmessage")
        # Build
        return MainWindow()

    def on_stop(self):
        self.release_capture()
