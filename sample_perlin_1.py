import array
import sys
import cv2
import random
import math

import numpy as np
import scipy.interpolate as sci

from direct.interval.LerpInterval import LerpFunc
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import NodePath, CardMaker, Vec3, Point3
from panda3d.core import GeomVertexData, GeomVertexFormat
from panda3d.core import GeomEnums, GeomVertexWriter, Geom, GeomNode, GeomPoints


from noise_texture.pynoise.perlin import PerlinNoise


class ParticleText(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        props = self.win.get_properties()
        print(props.get_size())

        self.card_root = NodePath('card_root')
        # self.card_root.reparent_to(self.aspect2d)
        self.card_root.reparent_to(self.render)
        self.cnt = 0
        self.speed = 0
        # self.read_image()
        self.splines = []
        self.dests = []
        self.starts = []
        self.create_card()

        self.total_dt = 0
        self.is_move = False
        self.is_reverse = False
        self.perlin = PerlinNoise()

        self.accept('m', self.start_move)
        self.accept('r', self.start_reverse)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

        self.camera.set_pos(0, -300, 0)
        self.camera.look_at(0, 0, 0)
        self.camLens.set_fov(90)
        # **************when parent is aspect2D***********************
        # self.camera.set_pos(0, 0, 0)
        # self.camera.look_at(0, 0, 0)
        # *************************************************************

    def start_move(self):
        self.start_time = globalClock.get_frame_time()
        self.is_move = not self.is_move

    def start_reverse(self):
        # self.dests = []
        # self.starts = []
        # self.get_random_text_pos()
        self.is_reverse = not self.is_reverse

    def read_image(self):
        img = cv2.imread('text.png')
        h, w = img.shape[:2]

        for j in range(h):
            for i in range(w):
                if img[j, i, 0] == 0:
                    print(j, i)

    def spline_interpolate(self, px, py):
        # x = 800 * (random.random() - 0.5)
        # y = 600 * (random.random() - 0.5)
        fxs = (800 * (random.random() - 0.5) for _ in range(10))
        fys = (600 * (random.random() - 0.5) for _ in range(10))
        xs = np.cumsum([px, *fxs])
        ys = np.cumsum([py, *fys])

        spl, _ = sci.make_splprep([xs, ys], s=0)
        # import pdb; pdb.set_trace()
        gen = ((x, y) for x, y in zip(*spl(np.linspace(0, 1, 100))))
        self.splines.append(gen)

    def get_random_text_pos(self):
        img = cv2.imread('text10.png')
        img = cv2.flip(img, 1)
        img = cv2.rotate(img, cv2.ROTATE_180)
        h, w = img.shape[:2]
        num_per_cel = 5
        print('h: ', h, 'w: ', w)

        cnt = 0

        for j in range(h):
            for i in range(w):
                cell = img[j, i, :]
                if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
                    for _ in range(num_per_cel):
                        x = random.uniform(i, i + 1)
                        y = random.uniform(j, j + 1)

                        # self.spline_interpolate(x, y)
                        self.dests.append((x - 200, y))
                        cnt += 1

    def create_card(self):
        img = cv2.imread('text10.png')
        img = cv2.flip(img, 1)
        img = cv2.rotate(img, cv2.ROTATE_180)
        h, w = img.shape[:2]
        num_per_cel = 5
        print('h: ', h, 'w: ', w)

        cnt = 0
        vdata_values = array.array('f', [])
        # vertex = GeomVertexWriter(vdata, 'vertex')

        for j in range(h):
            for i in range(w):
                cell = img[j, i, :]
                if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
                    for _ in range(num_per_cel):
                        x = random.uniform(i, i + 1)
                        y = random.uniform(j, j + 1)
                        vdata_values.extend([x - 200, 0, y])
                        self.starts.append((x - 200, y))
                        cnt += 1

        print('cnt: ', cnt)
        # import pdb; pdb.set_trace()
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
        # self.np.set_render_mode_thickness(2.0)

        # **************when parent is aspect2D***********************
        # card = CardMaker('card')
        # card.set_frame(-0.01, 0.01, -0.01, 0.01)
        # self.model = self.card_root.attach_new_node(card.generate())
        # self.model.set_color(1, 0, 0, 1)
        # # model.set_p(90)
        # self.model.set_pos(0, 0, 0)
        # *************************************************************

    def get_speed(self):
        # if self.speed >= 200:
        #     acceleration = 5

        if self.speed > 1:
            acceleration = 0

        elif self.speed >= 1:
            acceleration = 0.1

        elif self.speed >= 0.1:
            acceleration = 0.01

        else:
            acceleration = 0.005

        # print(self.speed, acceleration)

        self.speed += acceleration

        # if self.speed >= 1:
        #     acceleration = 0

        # if self.speed >= 0.5:
        #     acceleration = 0.1

        # else:
        #     acceleration = 0.01

        # self.speed += acceleration




    def scatter_text(self, dt):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')
        self.total_dt += dt

        for n, i in enumerate(range(0, len(vdata_mem), 3)):

            start_x, start_y = self.starts[n]

            nx = (start_x % 1200) / 1200
            ny = math.floor(start_y / 1200) / 600

            px = self.perlin.pnoise2(self.total_dt + nx, self.total_dt + ny)
            py = self.perlin.pnoise2(self.total_dt + nx * 2, self.total_dt + ny)

            vdata_mem[i] = px * 1200
            vdata_mem[i + 2] = py * 600

    def update(self, task):
        dt = globalClock.get_dt()

        if self.is_move:
            # self.is_move = False
            self.scatter_text(dt)
            # self.scatter(dt)
            # LerpFunc(self.scatter_text, duration=2, fromData=0, toData=20, blendType='easeInOut').start()


        if self.is_reverse:
            self.scatter_text_reverse(dt)



        # self.model.set_x(self.model.get_x() + 1 * dt)
        return task.cont


if __name__ == '__main__':
    app = ParticleText()
    app.run()
