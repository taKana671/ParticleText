from typing import NamedTuple

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class ImageSize(NamedTuple):

    w: float
    h: float


class TextImage:

    def __init__(self, text, font_file="DejaVuSans.ttf", font_size=60):
        self.text = text
        self.font = ImageFont.truetype(font_file, font_size)
        self.size = self.get_image_size()

    def get_image_size(self):
        img = Image.new("RGB", (0, 0), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        _, _, w, h = draw.textbbox((0, 0), text=self.text, font=self.font)
        return ImageSize(w, h)

    def create_text_image(self):
        img = Image.new("RGB", self.size, (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), self.text, (255, 255, 255), font=self.font)

        img = np.array(img)
        img = np.fliplr(img)
        img = np.rot90(img, 2)
        return img

    def pixel_coordinates(self):
        img = self.create_text_image()

        for j in range(self.size.h):
            for i in range(self.size.w):
                cell = img[j, i, :]
                if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
                    yield i, j