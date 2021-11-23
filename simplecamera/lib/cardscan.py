from io import BytesIO
from threading import Thread

import requests
from PIL import Image

import cv2

HALF_HD = (640, 360)


class CardScanRequest(Thread):
    def __init__(self, widget, url, headers, qrcode, timestamp, frame):
        super(CardScanRequest, self).__init__()
        self.widget = widget
        self.url = url
        self.headers = headers
        self.qrcode = qrcode
        self.timestamp = timestamp
        self.frame = frame

    def get_frame_data(self):
        # Reduce size
        frame = cv2.resize(self.frame, HALF_HD, interpolation=cv2.INTER_CUBIC)
        # Convert to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to PIL
        image = Image.fromarray(rgb)
        inmemory_file = BytesIO()
        image.save(inmemory_file, format="JPEG")
        data = inmemory_file.getvalue()
        inmemory_file.close()
        return data

    def format_timestamp(self):
        return self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def run(self):
        data = {}
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                data={
                    "qrcode": self.qrcode,
                    "timestamp": self.format_timestamp(),
                    "face_recognition": self.widget.app.is_face_recognition_active,
                },
                files={"jpg": self.get_frame_data()},
            )
        except requests.ConnectionError:
            data["network_error"] = True
        else:
            data = response.json()
        finally:
            self.widget.cardscan_queue.put(data, self.widget.cardscan_response)
