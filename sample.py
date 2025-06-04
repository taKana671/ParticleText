import array
import sys
import cv2
import random

import numpy as np
import scipy.interpolate as sci

from direct.interval.LerpInterval import LerpFunc
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import NodePath, CardMaker
from panda3d.core import GeomVertexData, GeomVertexFormat
from panda3d.core import GeomEnums, GeomVertexWriter, Geom, GeomNode, GeomPoints


class ParticleText(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        self.card_root = NodePath('card_root')
        # self.card_root.reparent_to(self.aspect2d)
        self.card_root.reparent_to(self.render)
        self.cnt = 0
        # self.read_image()
        self.splines = []
        self.dests = []
        self.create_card()


        self.is_move = False

        self.accept('m', self.start_move)
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
        self.is_move = not self.is_move

    def read_image(self):
        img = cv2.imread('text.png')
        h, w = img.shape[:2]

        for j in range(h):
            for i in range(w):
                if img[j, i, 0] == 0:
                    print(j, i)

    def get_destination(self):
        # x = 800 * (random.random() - 0.5)
        # y = 600 * (random.random() - 0.5)
        x = 800 * (random.random() - 0.5)
        y = 600 * (random.random() - 0.5)
        self.dests.append((x, y))

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

    def create_card(self):
        img = cv2.imread('text10.png')
        img = cv2.flip(img, 1)
        img = cv2.rotate(img, cv2.ROTATE_180)
        h, w = img.shape[:2]
        num_per_cel = 10
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
                        vdata_values.extend([x, 0, y])

                        # self.spline_interpolate(x, y)
                        self.get_destination()
                        cnt += 1

        print('cnt: ', cnt)
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

    def scatter_text(self, dt):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for n, i in enumerate(range(0, len(vdata_mem), 3)):
            # import pdb; pdb.set_trace()
            dest = self.dests[n]
            x = vdata_mem[i]
            y = vdata_mem[i + 2]

            next_x = None
            next_y = None


            if dest[0] <= 0:
                if x < dest[0]:
                    next_x = dest[0]  
            else:
                if x > dest[0]:
                    next_x = dest[0]

            if dest[1] <= 0:
                if y < dest[1]:
                    next_y = dest[1]
            else:
                if y > dest[1]:
                    next_y = dest[1]

            if next_x is None:
                dist_x = dest[0] - x
                next_x = x + dist_x * dt
            
            if next_y is None:
                dist_y = dest[1] - y
                next_y = y + dist_y * dt

            vdata_mem[i] = next_x
            vdata_mem[i + 2] = next_y


            # if dest[0] <= 0:
            #     if x <= dest[0]:
            #         vdata_mem[i] = dest[0]
            #         vdata_mem[i + 2] = dest[1]
            #         continue
            # else:
            #     if x > dest[0]:
            #         vdata_mem[i] = dest[0]
            #         vdata_mem[i + 2] = dest[1]
            #         continue

            # if dest[1] <= 0:
            #     if y <= dest[1]:
            #         vdata_mem[i] = dest[0]
            #         vdata_mem[i + 2] = dest[1]
            #         continue
            # else:
            #     if y > dest[1]:
            #         vdata_mem[i] = dest[0]
            #         vdata_mem[i + 2] = dest[1]
            #         continue

            # dist_x = dest[0] - x
            # dist_y = dest[1] - y

            # vdata_mem[i] = x + dist_x * dt
            # vdata_mem[i + 2] = y + dist_y * dt


    def scatter_text_spline(self, data):
        if int(data) == self.cnt:
            return

        self.cnt += 1
        print(self.cnt, data)
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for n, i in enumerate(range(0, len(vdata_mem), 3)):
            gen = self.splines[n]
            pt = next(gen)
            vdata_mem[i] = pt[0]
            vdata_mem[i + 2] = pt[1]

    def scatter(self, dt):
        geom_nd = self.np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for i in range(0, len(vdata_mem), 3):
            x = 800 * (random.random() - 0.5)
            y = 600 * (random.random() - 0.5)
            # x, _, z = vdata[i, i+3]
            vdata_mem[i] = x
            vdata_mem[i + 2] = y

    def create_card_3(self):
        img = cv2.imread('text7.png')
        img = cv2.flip(img, 1)
        img = cv2.rotate(img, cv2.ROTATE_180)
        h, w = img.shape[:2]
        num_per_cel = 50
        print('h: ', h, 'w: ', w)

        vdata = GeomVertexData('points', GeomVertexFormat.get_v3(), GeomEnums.UH_static)
        vdata.set_num_rows(h * w * num_per_cel)
        vertex = GeomVertexWriter(vdata, 'vertex')

        for j in range(h):
            for i in range(w):
                cell = img[j, i, :]
                if not (cell[0] == 0 and cell[1] == 0 and cell[2] == 0):
                    for _ in range(num_per_cel):
                        x = random.uniform(i, i + 1)
                        y = random.uniform(j, j + 1)
                        vertex.set_data3(x, 0, y)

        primitive = GeomPoints(GeomEnums.UH_static)
        primitive.add_next_vertices(h * w * num_per_cel)

        geom = Geom(vdata)
        geom.add_primitive(primitive)
        gnode = GeomNode('points')
        gnode.add_geom(geom)

        np = self.render.attach_new_node(gnode)
        np.set_render_mode_thickness(2.0)

    def create_card_2(self):
        img = cv2.imread('text5.png')
        img = cv2.flip(img, 1)
        img = cv2.rotate(img, cv2.ROTATE_180)
        h, w = img.shape[:2]

        num_pts = 1000
        vdata = GeomVertexData('points', GeomVertexFormat.get_v3(), GeomEnums.UH_static)
        vdata.set_num_rows(143000)
        vertex = GeomVertexWriter(vdata, 'vertex')

        start = end = None
        cnt = 0

        for j in range(h):
            for i in range(w):
                if img[j, i, 0] == 0:
                    if start is None:
                        start = i
                    else:
                        end = i

                if start is not None and end is not None:
                    for _ in range(num_pts):
                        x = random.uniform(start, end + 1)
                        y = random.uniform(j, j + 1)
                        vertex.set_data3(x, 0, y)
                        cnt += 1
                    start = end = None
        print(cnt)
        primitive = GeomPoints(GeomEnums.UH_static)
        primitive.add_next_vertices(cnt)

        geom = Geom(vdata)
        geom.add_primitive(primitive)
        gnode = GeomNode('points')
        gnode.add_geom(geom)

        np = self.render.attach_new_node(gnode)
        # np.set_render_mode_thickness(1.5)

    def create_card_1(self):
        img = cv2.imread('text2.png')

        img = cv2.flip(img, 1)
        img = cv2.rotate(img, cv2.ROTATE_180)

        h, w = img.shape[:2]
        # import pdb; pdb.set_trace()
        # for j in range(h):
            # for i in range(w):
        for j in np.linspace(0, h, h * 10, endpoint=False):
            for i in np.linspace(0, w, w * 10, endpoint=False):
                # print(j, i)
                pt = img[int(j), int(i), :]
                # if img[int(j), int(i), 0] == 0:
                if pt[0] == 0 and pt[1] == 0 and pt[2] == 0:
                    card = CardMaker('card')
                    card.set_frame(-0.05, 0.05, -0.05, 0.05)
                    model = self.card_root.attach_new_node(card.generate())
                    model.set_color(1, 0, 0, 1)
                    # self.model.set_p(-90)
                    model.set_pos(i-20, 0, j-20)


        # h, w = img.shape[:2]
        # # import pdb; pdb.set_trace()
        # for j in range(h):
        #     for i in range(w):
        #         # print(j, i)
        #         if img[j, i, 0] == 0:
        #             card = CardMaker('card')
        #             card.set_frame(-0.01, 0.01, -0.01, 0.01)
        #             model = self.card_root.attach_new_node(card.generate())
        #             model.set_color(1, 0, 0, 1)
        #             # self.model.set_p(-90)
        #             model.set_pos(i-10, 0, j-10)


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
            # self.is_move = False
            self.scatter_text(dt)
            # self.scatter(dt)
            # LerpFunc(self.scatter_text, duration=2, fromData=0, toData=20, blendType='easeInOut').start()


        # self.model.set_x(self.model.get_x() + 1 * dt)
        return task.cont


if __name__ == '__main__':
    app = ParticleText()
    app.run()
