import array
import sys
import cv2
import random
import math
import os

import numpy as np
import scipy.interpolate as sci
from direct.interval.IntervalGlobal import Parallel, Sequence, Wait
from direct.interval.LerpInterval import LerpFunc
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import NodePath, CardMaker, Vec3, Point3
from panda3d.core import GeomVertexData, GeomVertexFormat
from panda3d.core import GeomEnums, GeomVertexWriter, Geom, GeomNode, GeomPoints


# sys.path.append(os.path.join(os.path.dirname(__file__), '../pytweener'))

from noise import PerlinNoise
from noise import SimplexNoise
from pytweener.tween import Tween
from create_text import TextImage, generate_text_img, get_text_range


class ParticleText(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        props = self.win.get_properties()

        print(props.get_size())
        self.perlin = PerlinNoise()
        # self.perlin = SimplexNoise()

        self.card_root = NodePath('card_root')
        # self.card_root.reparent_to(self.aspect2d)
        self.card_root.reparent_to(self.render)
        self.cnt = 0
        self.speed = 0.1
        self.amp = 0

        self.amp_x = 0
        self.amp_y = 0

        # self.read_image()
        self.splines = []
        self.dests = []
        self.starts = []
        self.indexes = []
        self.tweens = []
        self.draw_text()
        self.para = Parallel()

        self.total_dt = 0
        self.is_move = False
        self.is_reverse = False
        self.is_fade = False

        self.accept('t', self.turn_back)
        self.accept('m', self.start_move)
        self.accept('p', self.pause)
        self.accept('r', self.resume)
        self.accept('f', self.finish)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

        self.camera.set_pos(0, -400, 0)
        self.camera.look_at(0, 0, 0)
        self.camLens.set_fov(90)
        # **************when parent is aspect2D***********************
        # self.camera.set_pos(0, 0, 0)
        # self.camera.look_at(0, 0, 0)
        # *************************************************************

    def turn_back(self):
        for tween in self.tweens:
            tween.turn_back()

    def finish(self):
        for tween in self.tweens:
            tween.finish()

    def pause(self):
        for tween in self.tweens:
            tween.pause()

    def resume(self):
        for tween in self.tweens:
            tween.resume()

    def start_move(self):
        self.start_time = globalClock.get_frame_time()
        self.is_move = not self.is_move

        for tween in self.tweens:
            # tween.start()
            tween.loop()

    def scatter_text4(self, dt):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for n, i in enumerate(range(0, len(vdata_mem), 3)):
            tween = self.tweens[n]

            if tween.is_playing:
                tween.update()
                vdata_mem[i] = tween.next_pos.x
                vdata_mem[i + 2] = tween.next_pos.z

    def get_dest(self, x, y, t, start_x, start_y):
        nx = x / 637
        ny = y / 57

        px = self.perlin.pnoise2(nx + t, ny + t) - 0.5
        py = self.perlin.pnoise2(nx * 2 + t, ny + t) - 0.5

        # import pdb; pdb.set_trace()
        # spread = (1 - nx) * 100 + 100
        # ex = 800 * px + random.random() * spread
        # ey = 600 * py + random.random() * spread * 0.5

        ex = 1200 * px
        ey = 400 * py

        self.dests.append((x, y))
        # tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 2, repeat=3, loop=False, yoyo=False, easing_type='in_out_quint')
        tween = Tween(Point3(start_x, 0, start_y), Point3(ex, 0, ey), 2, yoyo=True, easing_type='in_out_expo')

        self.tweens.append(tween)

        #     LerpFunc(self.scatter_text2, duration=1, fromData=0, toData=300, blendType='easeInOut'),
        #     self.np.colorScaleInterval(1, (1, 1, 1, 0), blendType='easeInOut')
        # ).start()

        # spread = (1 - nx) * 100 - 100
        # self.dests.append((px * 800 + spread * random.random(), py * 600 + spread * random.random()))


        # self.dests.append((px * 800, py * 600))


    def draw_text(self):
        cnt = 0
        t = random.uniform(0, 1000)
        vdata_values = array.array('f', [])
        text_img = TextImage('Panda3D Hello World')

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2

            vdata_values.extend([x, 0, y])
            self.get_dest(px, py, t, x, y)
            cnt += 1

        vdata = GeomVertexData('texts', GeomVertexFormat.get_v3(), Geom.UH_static)
        vdata.unclean_set_num_rows(cnt)
        vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
        vdata_mem[:] = vdata_values

        prim = GeomPoints(GeomEnums.UH_static)
        prim.add_next_vertices(cnt)

        geom = Geom(vdata)
        geom.add_primitive(prim)
        geom_node = GeomNode('points')
        geom_node.add_geom(geom)

        self.np = self.render.attach_new_node(geom_node)
        self.np.set_render_mode_thickness(1.)



    # def draw_text(self):
    #     img = generate_text_img('Panda3D Hello World')
    #     # img = cv2.imread('img_pil2.png')
    #     img = np.fliplr(img)
    #     img = np.rot90(img, 2)
    #     # img = cv2.flip(img, 1)
    #     # img = cv2.rotate(img, cv2.ROTATE_180)
    #     h, w = img.shape[:2]
    #     print('img_size', h, w)

    #     text_range = get_text_range(img)
    #     print('text_range', text_range)

    #     t = random.uniform(0, 1000)
    #     cnt = 0
    #     vdata_values = array.array('f', [])

    #     for j in range(h):
    #         for i in range(w):
    #             cell = img[j, i, :]
    #             if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
    #                 # print(j, i)
    #                 x = i - w / 2
    #                 y = j - h / 2

    #                 vdata_values.extend([x, 0, y])
    #                 self.get_dest(i, j, t, x, y)

    #                 cnt += 1

    #     vdata = GeomVertexData('texts', GeomVertexFormat.get_v3(), Geom.UH_static)
    #     vdata.unclean_set_num_rows(cnt)
    #     vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
    #     vdata_mem[:] = vdata_values

    #     prim = GeomPoints(GeomEnums.UH_static)
    #     prim.add_next_vertices(cnt)

    #     geom = Geom(vdata)
    #     geom.add_primitive(prim)
    #     geom_node = GeomNode('points')
    #     geom_node.add_geom(geom)

    #     self.np = self.render.attach_new_node(geom_node)
    #     self.np.set_render_mode_thickness(1.)

        # >>> arr
        # array([[[0, 0, 0],
        #         [1, 1, 1],
        #         [2, 2, 2]],

        #     [[3, 3, 3],
        #         [4, 4, 4],
        #         [5, 5, 5]]])
        # >>> arr2
        # array([[[2, 2, 2],
        #         [1, 1, 1],
        #         [0, 0, 0]],

        #     [[5, 5, 5],
        #         [4, 4, 4],
        #         [3, 3, 3]]], dtype=int32)
        # >>> arr3
        # array([[[3, 3, 3],
        #         [4, 4, 4],
        #         [5, 5, 5]],

        #     [[0, 0, 0],
        #         [1, 1, 1],
        #         [2, 2, 2]]], dtype=int32)
        # >>> arr.shape
        # (2, 3, 3)
        # >>> arr2.shape
        # (2, 3, 3)
        # >>> arr3.shape
        # (2, 3, 3)
        # >>> arr3[0]
        # array([[3, 3, 3],
        #     [4, 4, 4],
        #     [5, 5, 5]], dtype=int32)
        # >>> arr3[0][1]
        # array([4, 4, 4], dtype=int32)
        # >>> arr3[0][1][:]
        # array([4, 4, 4], dtype=int32)



        # **************when parent is aspect2D***********************
        # card = CardMaker('card')
        # card.set_frame(-0.01, 0.01, -0.01, 0.01)
        # self.model = self.card_root.attach_new_node(card.generate())
        # self.model.set_color(1, 0, 0, 1)
        # # model.set_p(90)
        # self.model.set_pos(0, 0, 0)
        # *************************************************************

    def update(self, task):
        dt = globalClock.get_dt()

        if self.is_move:
            self.scatter_text4(dt)
            # self.is_move = False

        if self.is_reverse:
            self.scatter_text_reverse(dt)

        # self.model.set_x(self.model.get_x() + 1 * dt)
        return task.cont


if __name__ == '__main__':
    app = ParticleText()
    app.run()
