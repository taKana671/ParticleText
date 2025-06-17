import array
import sys
import random
from enum import Enum, auto

from direct.interval.LerpInterval import LerpColorInterval, LerpColorScaleInterval
from direct.interval.IntervalGlobal import Parallel, Sequence, Wait
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Point3, LColor
from panda3d.core import GeomVertexData, GeomVertexFormat
from panda3d.core import GeomEnums, Geom, GeomNode, GeomPoints

from noise import PerlinNoise
from noise import SimplexNoise
from pytweener.tween import Tween
from text_image_creator import TextImage


class Status(Enum):

    SHOW_TEXT = auto()
    START_TWEEN = auto()
    HIDE_TEXT = auto()
    TO_PARTICLES = auto()
    TURN_BACK = auto()
    TO_TEXT = auto()
    WAIT = auto()
    TURN = auto()
    START_RETURN = auto()



class TextColorScaleInterval(LerpColorScaleInterval):

    def __init__(self, np, duration=1, fade=True, blend_type='easeInOut'):
        color_scale = (1, 1, 1, 0) if fade else (1, 1, 1, 1)
        start_color = (1, 1, 1, 1) if fade else (1, 1, 1, 0)
        super().__init__(np, duration, color_scale, start_color, blendType=blend_type)


class TextAnimation:

    def __init__(self, text):
        self.text = text

        props = base.win.get_properties()
        self.screen_size = props.get_size()

        self.tweens = []
        self.status = None
        self.total_dt = 0
        self.elapsed = 0

    def start(self):
        for tween in self.tweens:
            tween.start()

    def turn_back(self):
        for tween in self.tweens:
            tween.turn_back()

    def turn(self):
        for tween in self.tweens:
            tween.turn()

    def delay_start(self, dt):
        cnt = 0
        self.total_dt += dt

        for tween in self.tweens:
            # if not tween.delay_started:
            if not tween.is_playing:
                cnt += 1
                tween.delay_start(self.total_dt)

        if cnt == 0:
            self.total_dt = 0
            return True

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

        self.pts_np = base.render.attach_new_node(geom_node)
        self.pts_np.set_transparency(True)
        # self.points_np.set_render_mode_thickness(1.)

    def to_particles(self):
        geom_nd = self.pts_np.node()
        geom = geom_nd.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')
        cnt = 0

        for n, i in enumerate(range(0, len(vdata_mem), 3)):
            tween = self.tweens[n]

            if tween.is_playing:
                tween.update()
                vdata_mem[i] = tween.next_pos.x
                vdata_mem[i + 2] = tween.next_pos.z
                cnt += 1

        if cnt == 0:
            return True

    def do_fade(self, dt, elapsed):
        self.total_dt += dt

        if self.total_dt >= elapsed:
            self.is_faded = not self.is_faded
            self.total_dt = 0
            return True


class RandomParticles(TextAnimation):

    def create_tweens(self):
        cnt = 0
        vdata_values = array.array('f', [])
        text_img = TextImage(self.text)

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

    def update(self, dt):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade=False)
                self.color_scale.start()
                self.status = Status.START_TWEEN

            case Status.START_TWEEN:
                if not self.color_scale.is_playing():
                    self.start()
                    self.status = Status.TO_PARTICLES

            case Status.TO_PARTICLES:
                if self.to_particles():
                    self.color_scale = TextColorScaleInterval(self.pts_np, fade=True)
                    self.color_scale.start()
                    self.status = Status.HIDE_TEXT

            case Status.HIDE_TEXT:
                if not self.color_scale.is_playing():
                    self.pts_np.remove_node()
                    self.status = None
                    return True

            case _:
                self.status = Status.SHOW_TEXT


class PerlinParticles(TextAnimation):

    def __init__(self, text):
        super().__init__(text)
        self.total_dt = 0
        self.is_faded = False

    def create_tweens(self):
        cnt = 0
        text_img = TextImage(self.text)
        vdata_values = array.array('f', [])

        perlin = PerlinNoise()
        t = random.randint(0, 1000)

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            nx = px / text_img.size.w
            ny = py / text_img.size.h

            sx = perlin.pnoise2(nx + t, ny + t) - 0.5
            sy = perlin.pnoise2((nx + t) * 2, ny + t) - 0.5
            ex = self.screen_size.x * 2 * sx
            ey = self.screen_size.y * 2 * sy

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 3, yoyo=False, easing_type='in_out_expo')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def update(self, dt):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade=False)
                self.color_scale.start()
                self.status = Status.START_TWEEN

            case Status.START_TWEEN:
                if not self.color_scale.is_playing():
                    self.start()
                    self.status = Status.TO_PARTICLES

            case Status.TO_PARTICLES:
                if not self.is_faded:
                    if self.do_fade(dt, 2.0):
                        self.color_scale = TextColorScaleInterval(self.pts_np, blend_type='easeOut')
                        self.color_scale.start()

                if self.to_particles():
                    self.status = Status.TURN_BACK

            case Status.TURN_BACK:
                if not self.color_scale.is_playing():
                    self.turn_back()
                    self.status = Status.TO_TEXT

            case Status.TO_TEXT:
                if self.is_faded:
                    if self.do_fade(dt, 0.5):
                        self.color_scale = TextColorScaleInterval(
                            self.pts_np, duration=0.5, fade=False, blend_type='easeIn')
                        self.color_scale.start()

                if self.to_particles():
                    self.color_scale = TextColorScaleInterval(self.pts_np)
                    self.color_scale.start()
                    self.status = Status.HIDE_TEXT

            case Status.HIDE_TEXT:
                if not self.color_scale.is_playing():
                    self.pts_np.remove_node()
                    self.status = None
                    return True

            case _:
                self.status = Status.SHOW_TEXT


class DelayPerlinParticles(TextAnimation):

    def __init__(self, text):
        super().__init__(text)
        self.total_dt = 0
        self.is_faded = False
        # self.is_all_started = False

    def create_tweens(self):
        cnt = 0
        text_img = TextImage(self.text)
        vdata_values = array.array('f', [])

        perlin = PerlinNoise()
        t = random.randint(0, 1000)

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            nx = px / text_img.size.w
            ny = py / text_img.size.h

            sx = perlin.pnoise2(nx + t, ny + t) - 0.5
            sy = perlin.pnoise2((nx + t) * 2, ny + t) - 0.5
            ex = self.screen_size.x * 2 * sx
            ey = self.screen_size.y * 2 * sy

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 3, delay=nx, yoyo=False, easing_type='in_out_expo')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def update(self, dt):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade=False)
                self.color_scale.start()
                self.status = Status.START_TWEEN

            case Status.START_TWEEN:
                if not self.color_scale.is_playing():
                    if self.delay_start(dt):
                        self.status = Status.TO_PARTICLES

                    self.to_particles()

            case Status.TO_PARTICLES:
                if not self.is_faded:
                    if self.do_fade(dt, 0):
                        self.color_scale = TextColorScaleInterval(
                            self.pts_np, duration=4, blend_type='easeInOut')
                        self.color_scale.start()

                if self.to_particles():
                    self.status = Status.TURN

            case Status.TURN:
                if not self.color_scale.is_playing():
                    self.turn()
                    self.status = Status.START_RETURN

            case Status.START_RETURN:
                if self.is_faded:
                    if self.do_fade(dt, 0):
                        self.color_scale = TextColorScaleInterval(
                            self.pts_np, fade=False, duration=1.5, blend_type='easeIn')
                        self.color_scale.start()

                if self.delay_start(dt):
                    self.status = Status.TO_TEXT

                self.to_particles()

            case Status.TO_TEXT:
                if self.to_particles():
                    self.color_scale = TextColorScaleInterval(self.pts_np)
                    self.color_scale.start()
                    self.status = Status.HIDE_TEXT

            case Status.HIDE_TEXT:
                if not self.color_scale.is_playing():
                    self.pts_np.remove_node()
                    self.status = None
                    return True

            case _:
                self.status = Status.SHOW_TEXT


class DelaySimplexParticles(TextAnimation):

    def __init__(self, text):
        super().__init__(text)
        self.total_dt = 0
        self.is_faded = False

    def create_tweens(self):
        cnt = 0
        text_img = TextImage(self.text)
        vdata_values = array.array('f', [])

        simplex = SimplexNoise()
        t = random.randint(0, 1000)

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            nx = px / text_img.size.w
            ny = py / text_img.size.h
            pnx = simplex.snoise2(nx + t, (ny + t) * 3) - 0.5
            pny = simplex.snoise2((nx + t) * 1.5, ny + t) - 0.5

            spread = (1 - nx) * 200 - 100
            ex = self.screen_size.x * pnx + random.random() * spread
            ey = self.screen_size.y / 2 * pny + random.random() * spread

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 3, delay=nx, yoyo=False, easing_type='in_out_expo')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def update(self, dt):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade=False)
                self.color_scale.start()
                self.status = Status.START_TWEEN

            case Status.START_TWEEN:
                if not self.color_scale.is_playing():
                    if self.delay_start(dt):
                        self.status = Status.TO_PARTICLES

                    self.to_particles()

            case Status.TO_PARTICLES:
                if not self.is_faded:
                    if self.do_fade(dt, 0):
                        self.color_scale = TextColorScaleInterval(
                            self.pts_np, duration=4, blend_type='easeInOut')
                        self.color_scale.start()

                if self.to_particles():
                    self.status = Status.TURN

            case Status.TURN:
                if not self.color_scale.is_playing():
                    self.turn()
                    self.status = Status.START_RETURN

            case Status.START_RETURN:
                if self.is_faded:
                    if self.do_fade(dt, 0):
                        self.color_scale = TextColorScaleInterval(
                            self.pts_np, fade=False, duration=1.5, blend_type='easeIn')
                        self.color_scale.start()

                if self.delay_start(dt):
                    self.status = Status.TO_TEXT

                self.to_particles()

            case Status.TO_TEXT:
                if self.to_particles():
                    self.color_scale = TextColorScaleInterval(self.pts_np)
                    self.color_scale.start()
                    self.status = Status.HIDE_TEXT

            case Status.HIDE_TEXT:
                if not self.color_scale.is_playing():
                    self.pts_np.remove_node()
                    self.status = None
                    return True

            case _:
                self.status = Status.SHOW_TEXT


class SimplexParticles(TextAnimation):

    def __init__(self, text):
        super().__init__(text)

    def create_tweens(self):
        cnt = 0
        text_img = TextImage(self.text)
        vdata_values = array.array('f', [])

        simplex = SimplexNoise()
        t = random.uniform(0, 1000)

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

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 3, yoyo=True, easing_type='in_out_bounce')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def update(self, dt):
        self.to_particles()

    def finish(self):
        for tween in self.tweens:
            tween.finish()

    def pause(self):
        for tween in self.tweens:
            tween.pause()

    def resume(self):
        for tween in self.tweens:
            tween.resume()

    def loop(self):
        for tween in self.tweens:
            tween.loop()
