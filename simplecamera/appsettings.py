# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import os

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout

from appdirs import user_data_dir
from jsondiff import diff

from .lib.resources import get_filename
from .mixins import NetworkRetryMixin, UTCMixin

Builder.load_file(get_filename("kv/appsettings.kv"))


class AppSettings(UTCMixin, NetworkRetryMixin, AnchorLayout):
    app = ObjectProperty()
    domain_request_init = ObjectProperty(allownone=True)
    token_request_init = ObjectProperty(allownone=True)
    has_pending_domain_request = BooleanProperty(False)
    has_pending_token_request = BooleanProperty(False)
    is_domain_valid = BooleanProperty(False)
    is_token_valid = BooleanProperty(False)
    # b/c windows character encoding not valid in kv
    menu_label = StringProperty("設定、ctrl-sで開く")
    secondary_camera_label = StringProperty(
        "第二カメラ\n[color=#777777][size=10]第二のカメラを使用[/size][/color]"
    )
    scanner_name_label = StringProperty(
        "スキャナ名\n[color=#777777][size=10]この名前で写真にタグを付ける[/size][/color]"
    )
    domain_label = StringProperty(
        "ドメイン名\n[color=#777777][size=10]example.com[/size][/color]"
    )
    token_label = StringProperty("パスワード\n[color=#777777][size=10]トークン[/size][/color]")
    debug_character_label = StringProperty(
        "デバッグ情報\n[color=#777777][size=10]１分の間にFPSが５以下、"
        + "または接続障害5回以上だったの場合、自動的にオン[/size][/color]"
    )
    left_scanning_label = StringProperty(
        "スキャン左右\n[color=#777777][size=10]パフォーマンスのためオフはお勧め[/size][/color]"
    )
    face_detection_label = StringProperty(
        "顔検出\n[color=#777777][size=10]支払いが必要ない[/size][/color]"
    )
    face_recognition_label = StringProperty(
        "顔認識\n[color=#777777][size=10]支払いが必要[/size][/color]"
    )
    settings = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super(AppSettings, self).__init__(*args, **kwargs)

    def on_app(self, instance, app):
        # Delay loading, for AppSettings.app
        self.load_settings()

    def get_settings_path(self):
        app_name = "JinjukuCamera"
        app_author = "Jinjuku"
        app_dir = user_data_dir(app_name, app_author)
        # Create author_dir
        author_dir, _ = os.path.split(app_dir)
        if not os.path.exists(author_dir):
            os.mkdir(author_dir)
        # Create app_dir
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        settings_path = os.path.join(app_dir, "settings.json")
        # Create file
        if not os.path.exists(settings_path):
            with open(settings_path, "w"):
                pass
        return settings_path

    def init_settings(self):
        return {
            "scanner_name": "スキャナ",
            "domain": "jinryo.jinjuku.com",
            "token": "",
            "is_secondary_camera": False,
            "is_debug_character_visible": True,
            "is_left_scanning_active": True,
            "is_face_detection_active": True,
            "is_face_recognition_active": False,
        }

    def load_settings(self):
        path = self.get_settings_path()
        if os.path.exists(path):
            with open(path, "r") as settings_file:
                data = settings_file.read()
                try:
                    self.settings = json.loads(data)
                except json.decoder.JSONDecodeError:
                    self.settings = self.init_settings()
        else:
            self.settings = self.init_settings()
        self.apply_settings()

    def apply_settings(self):
        self.app.scanner_name = self.get_setting("scanner_name")
        self.app.domain = self.get_setting("domain")
        self.app.token = self.get_setting("token")
        self.app.is_secondary_camera = self.get_setting("is_secondary_camera")
        self.app.is_debug_character_visible = self.get_setting(
            "is_debug_character_visible"
        )
        self.app.is_left_scanning_active = self.get_setting("is_left_scanning_active")
        self.app.is_face_detection_active = self.get_setting("is_face_detection_active")
        self.app.is_face_recognition_active = self.get_setting(
            "is_face_recognition_active"
        )

    def get_setting(self, key):
        if key in self.app.settings:
            value = self.app.settings[key]
        else:
            if key in self.settings:
                value = self.settings[key]
            else:
                settings = self.init_settings()
                if key in settings:
                    value = settings[key]
        return value

    def on_scanner_name(self, scanner_name):
        if self.is_scanner_name_valid(scanner_name):
            self.app.scanner_name = scanner_name
            self.save_settings()

    def is_scanner_name_valid(self, scanner_name):
        if scanner_name is not None:
            scanner_name_field = self.ids["scanner_name"]
            if len(scanner_name) < 3:
                scanner_name_field.error = True
            else:
                scanner_name_field.error = False
                return True

    def validate_domain(self, *args):
        """Debounce requests in 250ms. If failure or error, retry up to 4 times within
        1 sec. Pending requests are delayed until that time."""
        if self.ids["domain"].text is not None:
            if not self.domain_request_init:
                self.domain_request_init = self.get_utc()
                self.domain_request()
            else:
                self.has_pending_domain_request = True

    def on_has_pending_domain_request(self, instance, is_pending):
        if is_pending:
            Clock.schedule_once(self.validate_domain, 0.25)

    def domain_request(self, *args):
        domain = self.ids["domain"].text
        url = self.app.get_url(domain)
        UrlRequest(
            url + "jinjuku-card/scanner-ping/",
            on_success=self.domain_success,
            on_failure=self.domain_retry,
            on_error=self.domain_retry,
            timeout=3,
        )

    def domain_retry(self, *args):
        self.retry_on_error(
            self.domain_request, self.domain_request_init, error=self.domain_error
        )

    def domain_error(self, *args):
        # Clear params
        self.clear_domain_params()
        # Set error
        self.ids["domain"].error = True
        # Validate settings
        self.is_domain_valid = False
        self.validate_settings()
        # Show settings menu
        self.app.is_settings_menu_visible = True

    def domain_success(self, *args):
        # Clear params
        self.clear_domain_params()
        # Set domain
        domain_field = self.ids["domain"]
        self.app.domain = domain_field.text
        # Clear error
        domain_field.error = False
        # Validate settings
        self.is_domain_valid = True
        self.validate_settings()
        # Save settings
        self.save_settings()
        # Check token
        self.validate_token()

    def clear_domain_params(self, exclude_init=False):
        self.domain_request_init = None
        self.has_pending_domain_request = False

    def validate_token(self, *args):
        if self.ids["token"].text is not None:
            if not self.token_request_init:
                self.token_request_init = self.get_utc()
                self.token_request()
            else:
                self.has_pending_token_request = True

    def on_has_pending_token_request(self, instance, is_pending):
        if is_pending:
            Clock.schedule_once(self.validate_token, 0.25)

    def token_request(self, *args):
        token = self.ids["token"].text
        headers = self.app.get_headers(token=token)
        UrlRequest(
            self.app.url + "jinjuku-card/scanner-auth/",
            on_success=self.token_success,
            on_failure=self.token_retry,
            # Network error
            on_error=self.token_retry,
            req_headers=headers,
            timeout=3,
        )

    def token_retry(self, *args):
        self.retry_on_error(
            self.token_request, self.token_request_init, error=self.token_error
        )

    def token_error(self, *args):
        # Clear params
        self.clear_token_params()
        # Set error
        self.ids["token"].error = True
        # Validate settings
        self.is_token_valid = False
        self.validate_settings()
        # Show settings menu
        self.app.is_settings_menu_visible = True

    def token_success(self, *args):
        # Clear params
        self.clear_token_params()
        # Set token
        token_field = self.ids["token"]
        self.app.token = token_field.text
        # Clear error
        token_field.error = False
        # Validate settings
        self.is_token_valid = True
        self.validate_settings()
        # Save settings
        self.save_settings()

    def clear_token_params(self):
        self.token_request_init = None
        self.has_pending_token_request = False

    def validate_settings(self):
        if self.is_domain_valid and self.is_token_valid:
            self.app.is_settings_valid = True
        else:
            self.app.is_settings_valid = False

    def toggle_is_secondary_camera(self, is_secondary):
        # True, False, None
        if is_secondary is not None:
            self.app.is_secondary_camera = is_secondary
            self.save_settings()

    def toggle_is_debug_character_visible(self, is_visible):
        # True, False, None
        if is_visible is not None:
            self.app.is_debug_character_visible = is_visible
            self.save_settings()

    def toggle_is_left_scanning_active(self, is_active):
        # True, False, None
        if is_active is not None:
            self.app.is_left_scanning_active = is_active
            self.save_settings()

    def toggle_is_face_detection_active(self, is_active):
        # True, False, None
        if is_active is not None:
            self.app.is_face_detection_active = is_active
            self.save_settings()

    def toggle_is_face_recognition_active(self, is_active):
        # True, False, None
        if is_active is not None:
            # Dependent settings
            self.app.is_face_recognition_active = is_active
            if is_active:
                if not self.app.is_face_detection_active:
                    self.app.is_face_detection_active = True
            self.save_settings()

    def can_save_settings(self):
        return (
            self.app.scanner_name
            and self.app.domain is not None
            and self.app.token is not None
            and self.app.is_secondary_camera is not None
            and self.app.is_debug_character_visible is not None
            and self.app.is_left_scanning_active is not None
            and self.app.is_face_detection_active is not None
            and self.app.is_face_recognition_active is not None
        )

    def get_current_settings(self):
        return {
            "scanner_name": self.app.scanner_name,
            "domain": self.app.domain,
            "token": self.app.token,
            "is_secondary_camera": (self.app.is_secondary_camera),
            "is_debug_character_visible": (self.app.is_debug_character_visible),
            "is_left_scanning_active": (self.app.is_left_scanning_active),
            "is_face_detection_active": (self.app.is_face_detection_active),
            "is_face_recognition_active": (self.app.is_face_recognition_active),
        }

    def save_settings(self):
        path = self.get_settings_path()
        if self.can_save_settings:
            current_settings = self.get_current_settings()
            with open(path, "r+") as settings_file:
                data = settings_file.read()
                try:
                    saved_settings = json.loads(data)
                except json.decoder.JSONDecodeError:
                    saved_settings = self.init_settings()
                finally:
                    if diff(current_settings, saved_settings):
                        d = json.dumps(current_settings)
                        # Clear file
                        settings_file.seek(0)
                        settings_file.truncate()
                        # Write settings
                        settings_file.write(d)
