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


# sys.path.append(os.path.join(os.path.dirname(__file__), '...'))

from noise import PerlinNoise
from noise import SimplexNoise
from tween.tween import Tween


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
        self.create_card()
        self.para = Parallel()

        self.total_dt = 0
        self.is_move = False
        self.is_reverse = False
        self.is_fade = False

        self.accept('m', self.start_move)
        self.accept('r', self.start_reverse)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

        self.camera.set_pos(200, -500, 0)
        self.camera.look_at(200, 0, 0)
        self.camLens.set_fov(90)
        # **************when parent is aspect2D***********************
        # self.camera.set_pos(0, 0, 0)
        # self.camera.look_at(0, 0, 0)
        # *************************************************************

    def start_move(self):
        self.start_time = globalClock.get_frame_time()
        self.is_move = not self.is_move

        for tween in self.tweens:
            tween.start()

        # self.np.colorScaleInterval(1, (1, 1, 1, 0), blendType='easeInOut').start()
        # self.np.set_transparency(True)
        # Parallel(
        #     LerpFunc(self.scatter_text2, duration=1, fromData=0, toData=300, blendType='easeInOut'),
        #     self.np.colorScaleInterval(1, (1, 1, 1, 0), blendType='easeInOut')
        # ).start()

        # Sequence(
        #     Parallel(
        #         LerpFunc(self.scatter_text4, duration=1, fromData=0, toData=400, blendType='easeInOut'),
        #         self.np.colorScaleInterval(1, (1, 1, 1, 0), blendType='easeInOut')
        #     ),
        #     Wait(1),
        #     Parallel(
        #         LerpFunc(self.scatter_text4, duration=1, fromData=400, toData=0, blendType='easeOut'),
        #         self.np.colorScaleInterval(1, (1, 1, 1, 1), blendType='easeInOut')
        #     ),
        # ).start()

    def scatter_text4(self, dt):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for n, i in enumerate(range(0, len(vdata_mem), 3)):
            # dest = self.dests[n]
            x = vdata_mem[i]
            y = vdata_mem[i + 2]

            tween = self.tweens[n]
            next_pt = tween.update()
            # dist_x = dest[0] - x
            # next_x = x + dist_x * dt * self.speed

            # dist_y = dest[1] - y
            # next_y = y + dist_y * dt * self.speed

            vdata_mem[i] = next_pt.x -203
            vdata_mem[i + 2] = next_pt.z - 20

        self.get_speed()

    def get_speed(self):
        # if self.speed >= 200:
        #     acceleration = 5

        if self.speed > 30:
            acceleration = 0

        elif self.speed >= 20:
            acceleration = 0.5

        elif self.speed >= 1:
            acceleration = 0.2

        else:
            acceleration = 0.1

        # print(self.speed, acceleration)

        self.speed += acceleration
    
    def scatter_text3(self, data):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        self.amp_y = data
        for n, i in enumerate(range(0, len(vdata_mem), 3)):

            start_x, start_y = self.starts[n]

            idx_x, idx_y = self.indexes[n]

            nx = idx_x / 406
            ny = idx_y / 40

            px = self.perlin.snoise2(nx * 20, ny * 20) - 0.5
            py = self.perlin.snoise2(nx * 40, ny * 20) - 0.5

            # spread = (1 - nx) * 100 + 100 

            vdata_mem[i] = start_x + px * 2 * self.amp_y - nx
            vdata_mem[i + 2] = start_y + py * 2 * self.amp_y * 0.5

    def get_dest(self, x, y, t=0):
        nx = x / 406
        ny = y / 40

        # px = self.perlin.snoise2(nx, ny * 1.5) - 0.5
        # py = self.perlin.snoise2(nx * 3, ny) - 0.5
        
        # px = self.perlin.snoise2(nx + t, ny + t) - 0.5
        # py = self.perlin.snoise2((nx + t) * 2 + t, ny + t) - 0.5
        

        px = self.perlin.pnoise2(nx + t, ny + t) - 0.5
        # py = self.perlin.pnoise2(nx * 2 + t, ny + t) - 0.5
        py = self.perlin.pnoise2((nx + t) * 4, ny + t) - 0.5

        spread = (1 - nx) * 100 + 100

        ex = 800 * px + random.random() * spread
        ey = 600 * py + random.random() * spread

        # ex = 800 * px
        # ey = 600 * py

        self.dests.append((x, y))
        tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 2, 'in_out_quint')
        self.tweens.append(tween)

        #     LerpFunc(self.scatter_text2, duration=1, fromData=0, toData=300, blendType='easeInOut'),
        #     self.np.colorScaleInterval(1, (1, 1, 1, 0), blendType='easeInOut')
        # ).start()

        # spread = (1 - nx) * 100 - 100
        # self.dests.append((px * 800 + spread * random.random(), py * 600 + spread * random.random()))


        # self.dests.append((px * 800, py * 600))

    def scatter_text2(self, data):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        self.amp_y += data
        for n, i in enumerate(range(0, len(vdata_mem), 3)):

            start_x, start_y = self.starts[n]

            idx_x, idx_y = self.indexes[n]

            # idx_x, idx_y = self.starts[n]

            nx = idx_x / 406
            ny = idx_y / 40

            px = self.perlin.snoise2(nx, ny) - 0.5
            py = self.perlin.snoise2(nx * 2, ny) - 0.5

            vdata_mem[i] = start_x + px * 2 * self.amp_y
            vdata_mem[i + 2] = start_y + py * 2 * self.amp_y * 0.5

    def test_func(self, data):
        print(data)

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
        img = cv2.imread('text11.png')
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

        t = random.uniform(0, 1000)

        cnt = 0
        vdata_values = array.array('f', [])
        # vertex = GeomVertexWriter(vdata, 'vertex')

        for j in range(h):
            for i in range(w):
                cell = img[j, i, :]
                if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
                    # for _ in range(num_per_cel):
                        # x = random.uniform(i, i + 1)
                        # y = random.uniform(j, j + 1)
                    x = i  - w / 2
                    y = j - h / 2
                    vdata_values.extend([x, 0, y])
    
                    self.starts.append((x, y))
                    self.indexes.append((i, j))
                    self.get_dest(i, j, t)
                    # vdata_values.extend([x - 200, 0, y])
                    # self.starts.append((x - 200, y))
                    # self.indexes.append((i-200, j))
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
        self.np.set_render_mode_thickness(1.)

        # **************when parent is aspect2D***********************
        # card = CardMaker('card')
        # card.set_frame(-0.01, 0.01, -0.01, 0.01)
        # self.model = self.card_root.attach_new_node(card.generate())
        # self.model.set_color(1, 0, 0, 1)
        # # model.set_p(90)
        # self.model.set_pos(0, 0, 0)
        # *************************************************************

    def scatter_text(self, dt):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')


        for n, i in enumerate(range(0, len(vdata_mem), 3)):

            start_x, start_y = self.starts[n]

            idx_x, idx_y = self.indexes[n]

            # idx_x, idx_y = self.starts[n]

            nx = idx_x / 406
            ny = idx_y / 40

            # nx = idx_x / 800
            # ny = idx_y / 600

            # nx = (start_x % 406) / 406
            # ny = math.floor(start_y / 406) / 40

            # px = self.perlin.pnoise2(nx + self.total_dt, ny + self.total_dt)
            # py = self.perlin.pnoise2(nx * 100 + self.total_dt, nx + self.total_dt)
            
            # px = self.perlin.snoise2(nx + self.total_dt, ny + self.total_dt)
            # py = self.perlin.snoise2(nx + self.total_dt, nx + self.total_dt)

            # px = self.perlin.snoise2((nx + self.total_dt) * 2, (ny + self.total_dt) * 2)
            # py = self.perlin.snoise2((nx + self.total_dt) * 2, (nx + self.total_dt) * 2)

            # self.speed = 0.1
            px = self.perlin.snoise2(nx + self.total_dt * self.speed * 2, ny + self.total_dt * self.speed * 2) - 0.5
            py = self.perlin.snoise2(nx + self.total_dt * self.speed, nx + self.total_dt * self.speed) - 0.5

          
           
            # print(px, py)

            # print(px, py)
            # vdata_mem[i] = start_x + px * 800 - 300
            # vdata_mem[i + 2] = start_y * py * 10

            # vdata_mem[i] = start_x + px * 600 - 300
            # vdata_mem[i + 2] = start_y + py * 59 - 100

            # vdata_mem[i] = start_x + px * 2 * 300
            # vdata_mem[i + 2] = start_y + py * 2 * 150

            vdata_mem[i] = start_x + px * 2 * self.amp_y
            vdata_mem[i + 2] = start_y + py * 2 * self.amp_y

            # vdata_mem[i] = px
            # vdata_mem[i + 2] = py

        # if self.amp_x < 600:
        
        # if self.amp_x < 400:
        #     self.amp_x += 20
        # if self.amp_y < 400:
        #     self.amp_y += 20

        if self.amp_x <= 20:
            self.amp_x += 1
            self.amp_y += 1
        # else:
        #     self.amp_x += 10
        #     self.amp_y += 10
        self.amp_y += 5
        self.total_dt += dt

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
