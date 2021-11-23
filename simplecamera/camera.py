import logging
from datetime import datetime
import numpy as np

from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
from kivy.uix.image import Image
from pyzbar.pyzbar import ZBarSymbol, decode

import cv2

from .constants import FULL_HD, HD
from .lib.resources import get_filename

logger = logging.getLogger(__name__)

Builder.load_file(get_filename("kv/camera.kv"))

# Rekognition minimum size * 2(4)
# https://aws.amazon.com/rekognition/faqs/
HD_FACE_SIZE = (120, 120)
FULL_HD_FACE_SIZE = (240, 240)


class KivyOpenCVCamera(Image):
    app = ObjectProperty()
    opencl_request = ObjectProperty()
    is_opencl_initialized = BooleanProperty(False)
    resolution = ObjectProperty()
    card_area = ObjectProperty()
    card_pad_x = NumericProperty()
    card_pad_y = NumericProperty()
    face_area = ObjectProperty()
    face_position = ObjectProperty()

    def __init__(self, **kwargs):
        super(KivyOpenCVCamera, self).__init__(**kwargs)
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        self.clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        # OpenCV Haar cascades
        haar_cascade = "assets/haarcascade_frontalface_default.xml"
        haar_cascade = get_filename(haar_cascade)
        self.face_cascade = cv2.CascadeClassifier(haar_cascade)
        # Update camera preview, 30 fps
        Clock.schedule_interval(self.update, 1 / 30.0)

    def face_helper_activate(self):
        self.app.is_face_helper_active = True
        Clock.schedule_once(self.face_helper_deactivate, 3)

    def face_helper_deactivate(self, *args):
        self.app.is_face_helper_active = False

    def update(self, dt):
        if self.app.capture is not None:
            ret, frame = self.app.capture.read()
            if ret:
                # Update frame resolution
                self.set_frame_resolution(frame)
                # Initialize OpenCL runtime
                if not self.is_opencl_initialized:
                    self.initialize_opencl(frame)
                # Scan for QR codes
                if self.app.is_scanning:
                    self.scan(frame)
                # Show frame
                self.blit_frame(frame)
            else:
                self.blit_black_frame()

    def set_frame_resolution(self, frame):
        height, width, _ = frame.shape
        self.resolution = width, height
        if self.resolution == HD:
            # Total area is 306000
            self.card_area = (425, 720)
            self.card_pad_x = 0
            self.card_pad_y = 0
            # Total area is 273600
            self.face_area = (570, 570)
            self.face_position = (355, 75)
        else:
            self.app.is_hd = False

    def initialize_opencl(self, frame):
        # Is opencl initialized?
        if not self.is_opencl_initialized:
            if not self.opencl_request:
                self.opencl_request = datetime.now()
            # is cpu 50% or less?
            if self.app.cpu <= 50.0:
                self.opencl_face(frame)
            else:
                elapsed_time = datetime.now() - self.opencl_request
                # Is elapsed time greater than 5 seconds?
                if elapsed_time.total_seconds() >= 5:
                    self.opencl_face(frame)

    def opencl_face(self, frame):
        """Scan a 25x25 sample to initialize the OpenCL runtime."""
        segment = self.get_segment(frame, (25, 25))
        gray = cv2.cvtColor(segment, cv2.COLOR_BGR2GRAY)
        self.face_cascade.detectMultiScale(gray)
        self.is_opencl_initialized = True

    def scan(self, frame):
        # Search on the right
        position = (self.card_pad_x, self.card_pad_y)
        segment = self.get_segment(frame, self.card_area, position)
        qrcode = self.get_qrcode(segment)
        # Highlight right
        if self.app.is_scanning_area_highlighted:
            color = (235, 252, 255)  # Washed yellow
            self.highlight_segment(segment, color)
        # Search on the left
        if self.app.is_left_scanning_active and not qrcode:
            pos = (
                self.resolution[0] - self.card_area[0] - self.card_pad_x,
                self.card_pad_y,
            )
            seg = self.get_segment(frame, self.card_area, pos)
            qrcode = self.get_qrcode(seg)
            # Highlight left
            if self.app.is_scanning_area_highlighted:
                color = (223, 223, 255)  # Washed red
                self.highlight_segment(seg, color)
        if qrcode:
            # Face preview, square...
            face_preview = self.get_segment(
                frame, (self.resolution[1], self.resolution[1])
            )
            if self.app.is_face_detection_active:
                # Activate face helper
                if not self.app.is_face_helper_active:
                    self.face_helper_activate()
                # Search for face
                face_segment = self.get_segment(
                    frame, self.face_area, self.face_position
                )
                # Highlight face
                if self.app.is_scanning_area_highlighted:
                    color = (254, 255, 246)  # Washed blue
                    self.highlight_segment(face_segment, color)
                face_pos = self.get_face(face_segment)
                if face_pos is not None:
                    face = self.get_face_segment(frame, self.face_position, face_pos)
                    if face is not None:
                        if not self.app.is_scanning_area_highlighted:
                            self.got_data(frame, qrcode, face_preview)
            else:
                if not self.app.is_scanning_area_highlighted:
                    self.got_data(frame, qrcode, face_preview)

    def get_qrcode(self, segment):
        # Convert to grayscale, as binarization requires
        gray = cv2.cvtColor(segment, cv2.COLOR_BGR2GRAY)
        # Don't Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Don't use Otsu method, or gaussian...
        # cv2.adaptiveThreshold is hard on CPU, but...
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2
        )
        qrcodes = self.get_all_qrcodes(threshold)
        valid_qrcode = self.get_valid_qrcode(qrcodes)
        # QR code
        if valid_qrcode:
            polygon = [(point.x, point.y) for point in valid_qrcode.polygon]
            light_yellow = (169, 241, 251)
            self.highlight_polygon(segment, polygon, light_yellow, alpha=0.90)
            return valid_qrcode.data.decode("utf8")

    def highlight_segment(self, segment, color, alpha=0.35):
        x, y = (0, 0)
        h, w, _ = segment.shape
        polygon = [(x, y), (x, y + h), (x + w, y + h), (x + w, y)]
        self.highlight_polygon(segment, polygon, color, alpha=alpha)

    def highlight_polygon(self, segment, polygon, color, alpha=0.5):
        overlay = segment.copy()
        points = np.array(polygon, dtype=np.int32)
        overlay = cv2.fillConvexPoly(
            overlay, points=points, color=color, lineType=cv2.LINE_AA
        )
        cv2.addWeighted(overlay, alpha, segment, 1 - alpha, 0, segment)

    def get_all_qrcodes(self, threshold):
        height, width = threshold.shape[:2]
        qrcodes = decode(
            (threshold.tobytes(), width, height), symbols=[ZBarSymbol.QRCODE]
        )
        return qrcodes

    def get_valid_qrcode(self, qrcodes):
        """Returns largest QR code"""
        choices = []
        for qrcode in qrcodes:
            if self.is_valid_qrcode(qrcode):
                x, y, w, h = qrcode.rect
                size = w * h
                choices.append({"qrcode": qrcode, "size": size})
        choices = sorted(choices, key=lambda k: k["size"], reverse=True)
        for choice in choices:
            qrcode = choice["qrcode"]
            return qrcode

    def is_valid_qrcode(self, qrcode):
        qr = qrcode.data.decode("utf8")
        try:
            card_number, password = qr.split(" ")
            assert len(card_number) == 8
            int(card_number)
        except Exception:
            logging.info("Invalid: {}".format(qrcode.data))
        else:
            return True

    def get_face(self, segment):
        faces = self.get_all_faces(segment)
        return self.get_valid_face(faces)

    def get_face_segment(self, frame, position, face):
        x, y, w, h = face
        # Completely arbitrary
        if self.app.is_face_recognition_active:
            area = (w, h + 150)
            pos = (x + position[0], y + position[1] - 75)
            segment = self.get_segment(frame, area, pos)
        else:
            area = (w, h)
            pos = (x + position[0], y + position[1])
            segment = self.get_segment(frame, area, pos)
        if self.app.is_scanning_area_highlighted:
            light_pink = (215, 163, 255)
            self.highlight_segment(segment, light_pink, alpha=0.5)
        return segment

    def get_all_faces(self, segment):
        # Convert to grayscale
        gray = cv2.cvtColor(segment, cv2.COLOR_BGR2GRAY)
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        cl1 = self.clahe.apply(gray)
        # Detect faces
        scale_factor = 1.05  # Slow scale factor
        min_neighbors = 4  # Average neighbors
        if self.resolution == FULL_HD:
            min_size = FULL_HD_FACE_SIZE
        else:
            min_size = HD_FACE_SIZE
        return self.face_cascade.detectMultiScale(
            cl1, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size
        )

    def get_valid_face(self, faces):
        """Get largest face, which exceeds minimum size."""
        choices = []
        for face in faces:
            x, y, w, h = face
            size = w * h
            if self.resolution == FULL_HD:
                face_size = FULL_HD_FACE_SIZE
            else:
                face_size = HD_FACE_SIZE
            min_size = face_size[0] * face_size[1]
            if size >= min_size:
                choices.append({"face": face, "size": size})
        if len(choices):
            choices = sorted(choices, key=lambda k: k["size"], reverse=True)
            for choice in choices:
                return choice["face"]

    def get_segment(self, frame, area, position=(None, None)):
        height, width, _ = frame.shape
        w, h = area
        x, y = position
        if x is None:
            x = int((width - w) / 2)
        if y is None:
            y = int((height - h) / 2)
        assert (width - (w + x)) >= 0
        assert (height - (h + y)) >= 0
        assert (w + x) <= width
        assert (y + h) <= height
        position = x, y
        return self.crop_segment(frame, position, area)

    def crop_segment(self, frame, position, area):
        x, y = position
        w, h = area
        cropped = frame[y : (y + h), x : (x + w)]
        return cropped

    def blit_black_frame(self):
        frame = np.zeros((HD[1], HD[0], 3), np.uint8)
        self.blit_frame(frame)

    def blit_frame(self, frame):
        frame = cv2.flip(frame, -1)
        data = frame.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(data, colorfmt="bgr", bufferfmt="ubyte")
        self.texture = texture
