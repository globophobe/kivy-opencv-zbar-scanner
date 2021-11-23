import cv2
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.uix.image import Image

Builder.load_string(
    """
<KivyOutputImage>:
    allow_stretch: True
    keep_ratio: True
"""
)


class KivyNumpyImage(Image):
    def blit_frame(self, frame):
        frame = cv2.flip(frame, -1)
        data = frame.tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="bgr")
        texture.blit_buffer(data, colorfmt="bgr", bufferfmt="ubyte")
        self.texture = texture
