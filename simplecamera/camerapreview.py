# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime
from io import BytesIO
from urllib.parse import urlencode

import cv2
import numpy as np
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import ObjectProperty, StringProperty
from PIL import Image

from .camera import KivyOpenCVCamera
from .constants import GOLD_95, LIGHT_BLUE_95, LIGHTEST_BLUE_95, RED_95
from .lib.cardscan import CardScanRequest
from .lib.kqueue import KivyQueue
from .lib.resources import get_filename
from .mixins import NetworkRetryMixin, UTCMixin

Builder.load_file(get_filename("kv/camerapreview.kv"))


class CameraPreview(UTCMixin, NetworkRetryMixin, KivyOpenCVCamera):
    app = ObjectProperty()
    request_init = ObjectProperty(allownone=True)

    uuid = StringProperty(allownone=True)
    cardscan_uuid = StringProperty(allownone=True)
    qrcode = StringProperty(allownone=True)
    utc = ObjectProperty(allownone=True)
    localtime = ObjectProperty(allownone=True)

    sound = StringProperty(allownone=True)

    def __init__(self, *args, **kwargs):
        super(CameraPreview, self).__init__(*args, **kwargs)
        # Get sounds
        self.sounds = {
            "success": SoundLoader.load(get_filename("assets/success.wav")),
            "done": SoundLoader.load(get_filename("assets/done.wav")),
            "fail": SoundLoader.load(get_filename("assets/fail.wav")),
            "error": SoundLoader.load(get_filename("assets/error.wav")),
        }
        # Numpy properties, which do not behave well with kivy's
        # property checking
        self.frame = None
        self.face_preview = None
        # Initialize queue
        self.cardscan_queue = KivyQueue(self.cardscan_response, maxsize=1)

    def got_data(self, frame, qrcode, face_preview):
        # Stop scanning
        self.app.is_scanning = False
        self.face_helper_deactivate()
        # Datetime
        self.utc = self.get_utc()
        # Init url request
        self.qrcode = qrcode
        # Highlight body
        if self.app.is_face_detection_active:
            self.body.color = GOLD_95
        # Save references
        self.frame = frame.copy()
        self.face_preview = face_preview.copy()

    def on_qrcode(self, *args):
        """Retry until CPU 75% or less, or 500ms have passed."""
        if not self.app.is_scanning and not self.request_init:
            elapsed_time = self.get_elapsed_time(self.utc)
            milliseconds = elapsed_time * 1000
            # Is CPU 75% or less, or have 500ms passed
            if self.app.cpu <= 75.0 or milliseconds >= 500:
                # For retry
                self.request_init = self.get_utc()
                self.user_request()
            else:
                Clock.schedule_once(self.on_qrcode, 0.1)

    def user_request(self, *args):
        headers = self.app.get_headers(content_type="application/x-www-form-urlencoded")
        UrlRequest(
            self.app.url + "jinjuku-card/user/",
            on_success=self.qrcode_result,
            on_failure=self.user_request_error,
            on_error=self.user_request_error,
            req_body=urlencode({"qrcode": self.qrcode}),
            req_headers=headers,
            timeout=3,
        )

    def user_request_error(self, *args):
        self.retry_on_error(
            self.user_request, self.request_init, error=self.network_error
        )

    def qrcode_result(self, request, result):
        # Was there a cardscan, within 5 minutes?
        has_uuid = "cardscan_uuid" in result
        has_timestamp = "cardscan_timestamp" in result
        try:
            if has_uuid and has_timestamp:
                self.get_face_preview(result)
            else:
                self.new_cardscan(result)
        except Exception:
            self.decode_error()

    def get_face_preview(self, data):
        self.cardscan_uuid = data["cardscan_uuid"]
        self.localtime = datetime.datetime.strptime(
            data["cardscan_timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        # Set card
        self.set_card_text(data)
        # Face preview
        self.request_init = self.get_utc()
        self.face_preview_request()

    def face_preview_request(self, *args):
        # Get headers
        headers = self.app.get_headers(content_type="application/x-www-form-urlencoded")
        UrlRequest(
            self.app.url + "card/face-preview/",
            on_success=self.face_preview_result,
            on_failure=self.face_preview_error,
            on_error=self.face_preview_error,
            req_body=urlencode({"uuid": self.cardscan_uuid}),
            req_headers=headers,
            timeout=3,
        )

    def face_preview_error(self, *args):
        self.retry_on_error(
            self.face_preview_request, self.request_init, error=self.network_error
        )

    def face_preview_result(self, request, result):
        try:
            # Open as PIL image
            inmemory_file = BytesIO(result)
            with Image.open(inmemory_file) as image:
                # Convert to array
                face_preview = np.array(image)
                # Convert to BGR
                bgr = cv2.cvtColor(face_preview, cv2.COLOR_RGB2BGR)
        except Exception:
            self.decode_error()
        else:
            self.face_preview = bgr
            # Show card
            self.card.show_card(background_color=LIGHTEST_BLUE_95)
            # Show face
            self.card.blit_face(self.face_preview)
            # Play sound
            self.sound = "done"

    def new_cardscan(self, data):
        # Set timestamp before uuid
        self.localtime = datetime.datetime.now()
        # Set uuid
        self.uuid = data["uuid"]
        # Show card
        self.set_card_text(data)
        # Show card
        self.card.show_card()
        # Show face
        self.card.blit_face(self.face_preview)

    def set_card_text(self, data, attention=False):
        # Card header
        self.card.header_block = "JINJUKU"
        # Card text block
        # B/C windows, no unicode with strftime
        hour = self.localtime.strftime("%H")
        minute = self.localtime.strftime("%M")
        second = self.localtime.strftime("%S")
        time = "{}時{}分{}秒".format(hour, minute, second)
        self.card.text_block = "[size=14]{}[/size]\n{}\n{}".format(
            time, data["line_1"], data["line_2"]
        )
        # Card footer block
        if attention:
            if "attention_line" in data:
                points = data["attention_line"]
                # TODO: Fix this on the server
                if points not in (None, ""):
                    self.card.footer_block = "{}点".format(points)

    def network_error(self, *args):
        self.app.total_connection_errors += 1
        self.card.show_card()
        self.card.header_block = "[color=#E7040F]エラー[/color]"
        self.card.text_block = "インターネット\nの接続\nがありません。"
        self.sound = "error"

    def decode_error(self):
        self.card.show_card()
        self.card.header_block = "[color=#E7040F]エラー[/color]"
        self.card.text_block = "カードは\nもう一度\nしてください。"
        self.sound = "error"

    def on_uuid(self, instance, uuid):
        if uuid is not None:
            self.request_init = self.get_utc()
            self.cardscan_request()

    def cardscan_request(self):
        url = self.app.url + "jinjuku-card/save/"
        headers = self.app.get_headers()
        cardscan = CardScanRequest(
            self, url, headers, self.qrcode, self.utc, self.frame
        )
        cardscan.start()

    def cardscan_response(self):
        # Work with legacy API
        data = self.cardscan_queue.get()[0]
        if data:
            if "network_error" in data:
                self.retry_on_error(
                    self.cardscan_request, self.request_init, error=self.network_error
                )
            else:
                # Play sound
                if "sound" in data:
                    sound = data["sound"]
                    # TODO: Rename on server
                    sound = "fail" if sound == "lock" else sound
                    self.set_card_text(data, attention=True)
                    self.sound = sound
        else:
            self.clear_request()

    def on_sound(self, instance, sound):
        if sound in self.sounds:
            snd = self.sounds[sound]
            snd.bind(on_play=self.on_play)
            snd.bind(on_stop=self.on_stop)
            snd.play()

    def on_play(self, *args):
        self.clear_request_params()
        self.animate_card_background_color()

    def clear_request_params(self):
        self.uuid = None
        self.cardscan_uuid = None
        self.qrcode = None
        self.utc = None
        self.localtime = None
        self.frame = None
        self.face_preview = None
        # Clear last
        self.request_init = None

    def animate_card_background_color(self):
        """Mustn't bind to property, or property will update n times."""
        if self.sound in ("success", "fail"):
            if self.sound == "success":
                color = LIGHT_BLUE_95
            elif self.sound == "fail":
                color = RED_95
            self.card.animate_background_color(color)
        # Clear sound
        self.sound = None

    def on_stop(self, *args):
        self.card.fade_out_card()
