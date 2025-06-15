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

from noise import PerlinNoise, ValueNoise, VoronoiNoise, PeriodicNoise
from noise import SimplexNoise
from pytweener.tween import Tween
from text_image_creator import TextImage, generate_text_img, get_text_range


class ParticleText(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        props = self.win.get_properties()
        self.screen_size = props.get_size()

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
        # self.draw_text()
        # self.to_random_particles('Panda3D Hello World')
        # self.to_simplex_particles('Panda3D Hello World')
        self.to_perlin_particles('Panda3D Hello World')

        self.delay_starting = False
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

    def delay_start(self, dt):
        self.start_end = False

        for tween in self.tweens:
            if not tween.is_playing and self.total_dt >= tween.delay:
                tween.start()
                self.start_end = True

        self.total_dt += dt

    def start_move(self):
        self.delay_starting = True
        # self.start_time = globalClock.get_frame_time()
        # self.is_move = not self.is_move

        # for tween in self.tweens:
        #     tween.start()
            # tween.loop()

    def scatter_text4(self, dt):
        geom_nd = self.points_np.node()
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

    def create_points(self, vdata_values, vertices_cnt):
        vdata = GeomVertexData('texts', GeomVertexFormat.get_v3(), Geom.UH_static)
        vdata.unclean_set_num_rows(vertices_cnt)
        vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
        vdata_mem[:] = vdata_values

        prim = GeomPoints(GeomEnums.UH_static)
        prim.add_next_vertices(vertices_cnt)

        geom = Geom(vdata)
        geom.add_primitive(prim)
        geom_node = GeomNode('points')
        geom_node.add_geom(geom)

        self.points_np = self.render.attach_new_node(geom_node)
        # self.points_np.set_render_mode_thickness(1.)

    # def to_draw_text(self):
    #     cnt = 0
    #     t = random.uniform(0, 1000)
    #     vdata_values = array.array('f', [])
    #     text_img = TextImage('Panda3D Hello World')

    #     for px, py in text_img.pixel_coordinates():
    #         x = px - text_img.size.w / 2
    #         y = py - text_img.size.h / 2

    #         vdata_values.extend([x, 0, y])
    #         self.get_dest(px, py, t, x, y)
    #         cnt += 1

    #     self.create_points(vdata_values, cnt)

    def to_random_particles(self, text):
        cnt = 0
        vdata_values = array.array('f', [])
        text_img = TextImage(text)

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            ex = (random.random() - 0.5) * self.screen_size.x
            ey = (random.random() - 0.5) * self.screen_size.y

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 2, yoyo=True, easing_type='in_out_expo')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def to_simplex_particles(self, text):
        cnt = 0
        text_img = TextImage(text)
        vdata_values = array.array('f', [])

        simplex = SimplexNoise()
        t = simplex.mock_time()
        # t = random.uniform(0, 1000)

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            nx = px / text_img.size.w
            ny = py / text_img.size.h
            sx = simplex.snoise2(nx + t, ny + t) - 0.5
            sy = simplex.snoise2((nx + t) * 2, ny + t) - 0.5
            ex = self.screen_size.x * sx
            ey = self.screen_size.y * sy

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 2, yoyo=True, easing_type='in_out_expo')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def to_perlin_particles(self, text):
        cnt = 0
        text_img = TextImage(text)
        vdata_values = array.array('f', [])

        perlin = PerlinNoise()
        # perlin = ValueNoise()
        t = perlin.mock_time() * 100

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            nx = px / text_img.size.w * 2
            ny = py / text_img.size.h * 0.5
            pnx = perlin.pnoise2(nx + t, (ny + t) * 3) - 0.5
            pny = perlin.pnoise2((nx + t) * 1.5, ny + t) - 0.5
            spread = (1 - nx) * 200 + 100
            ex = self.screen_size.x * pnx + random.random() * spread
            ey = self.screen_size.y * pny + random.random() * spread

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 4, yoyo=True, easing_type='in_out_expo')
            tween.delay = nx * 0.5
            self.tweens.append(tween)
            self.starts.append(py)
            cnt += 1

        self.create_points(vdata_values, cnt)
        self.starts_set = list(set(self.starts))

    def update(self, task):
        dt = globalClock.get_dt()
        # print(dt)

        if self.is_move:
            self.scatter_text4(dt)
            # self.scatter_text5(dt)
            # self.is_move = False

        if self.delay_starting:
            self.delay_start(dt)
            self.scatter_text4(dt)

        if self.is_reverse:
            self.scatter_text_reverse(dt)

        # self.model.set_x(self.model.get_x() + 1 * dt)
        return task.cont


if __name__ == '__main__':
    app = ParticleText()
    app.run()


# **************when parent is aspect2D***********************
# card = CardMaker('card')
# card.set_frame(-0.01, 0.01, -0.01, 0.01)
# self.model = self.card_root.attach_new_node(card.generate())
# self.model.set_color(1, 0, 0, 1)
# # model.set_p(90)
# self.model.set_pos(0, 0, 0)
# *************************************************************
