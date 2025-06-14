from typing import NamedTuple

import cv2
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
        # img = cv2.flip(img, 1)
        # img = cv2.rotate(img, cv2.ROTATE_180)
        return img

    def pixel_coordinates(self):
        img = self.create_text_image()

        for j in range(self.size.h):
            for i in range(self.size.w):
                cell = img[j, i, :]
                if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
                    yield i, j

# (0, 10, 637, 57)

def generate_text_img_1(text):
    img = Image.new("RGB", (1024, 1024), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSans.ttf", 60)
    # import pdb; pdb.set_trace()
    # txt_w, txt_h = draw.textsize(text, font=font)
    draw.text((0, 0), text, (255, 255, 255), font=font)
    img.save('img_pil.png')
    return np.array(img)


def generate_text_img(text):
    font = ImageFont.truetype("DejaVuSans.ttf", 60)

    img = Image.new("RGB", (0, 0), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    _, _, w, h = draw.textbbox((0, 0), text=text, font=font)

    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, (255, 255, 255), font=font)
    img.save('img_pil2.png')
    return np.array(img)


def get_text_range(arr):
    h, w = np.where(np.all(arr > 0, axis=2))
    # h, w = np.where(np.all(arr == 255, axis=2))
    print('h_max', h.max(), 'h_min', h.min(), 'w_max', w.max(), 'w_min', w.min())
    return h.max() - h.min(), w.max() - w.min()


def test():
    img = cv2.imread('img_pil.png', cv2.IMREAD_UNCHANGED)
    h, w = img.shape[:2]

    for j in range(h):
        for i in range(w):
            line = img[j, i]
            if line[3] == 1:
            # if line[0] == 0 and line[1] == 0 and line[2] == 0:
                print(j, i)


if __name__ == '__main__':
    # test()
    generate_text_img('Panda3D Hello World')