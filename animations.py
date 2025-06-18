import array
import random
from enum import Enum, auto

from direct.interval.LerpInterval import LerpColorScaleInterval
from panda3d.core import Point3
from panda3d.core import GeomVertexData, GeomVertexFormat
from panda3d.core import GeomEnums, Geom, GeomNode, GeomPoints

from noise import PerlinNoise, Fractal2D, SimplexNoise
from pytweener.tween import Tween
from text_image_creator import TextImage


class Status(Enum):

    SHOW_TEXT = auto()
    HIDE_TEXT = auto()
    START = auto()
    GO_BACK = auto()
    TO_PARTICLES = auto()
    TO_TEXT = auto()
    TURN = auto()


class TextColorScaleInterval(LerpColorScaleInterval):

    def __init__(self, np, duration=1, fade_out=True, blend_type='easeInOut'):
        color_scale = (1, 1, 1, 0) if fade_out else (1, 1, 1, 1)
        start_color = (1, 1, 1, 1) if fade_out else (1, 1, 1, 0)
        super().__init__(np, duration, color_scale, start_color, blendType=blend_type)


class TextAnimation:

    def __init__(self, text, easing_func='in_out_expo'):
        self.text = text
        self.easing_func = easing_func

        props = base.win.get_properties()
        self.screen_size = props.get_size()
        self.tweens = []
        self.status = None

    def start(self):
        for tween in self.tweens:
            tween.start()

    def turn_back(self):
        for tween in self.tweens:
            tween.turn_back()

    def turn(self):
        for tween in self.tweens:
            tween.turn()

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
        self.pts_np.set_render_mode_thickness(1.2)

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


class Boomerang(TextAnimation):

    def update(self, _):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade_out=False)
                self.color_scale.start()
                self.status = Status.START

            case Status.START:
                if not self.color_scale.is_playing():
                    self.start()
                    self.status = Status.TO_PARTICLES

            case Status.TO_PARTICLES:
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


class RandomParticles(Boomerang):

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

            tween = Tween(
                Point3(x, 0, y), Point3(ex, 0, ey), 2, yoyo=True, easing_type=self.easing_func)
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)


class SimplexParticles(Boomerang):

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

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 3, yoyo=True, easing_type=self.easing_func)
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)


class Fade(TextAnimation):

    def __init__(self, text, easing_func='in_out_expo'):
        super().__init__(text, easing_func)
        self.is_faded = False
        self.total_dt = 0
        self.elapsed = 0

    def start_fade(self, dt, elapsed):
        self.total_dt += dt

        if self.total_dt >= elapsed:
            self.is_faded = not self.is_faded
            self.total_dt = 0
            return True

    def fade_out(self, dt, elapsed, duration=1):
        if not self.is_faded:
            if self.start_fade(dt, elapsed):
                self.color_scale = TextColorScaleInterval(
                    self.pts_np, duration, True, 'easeOut')
                self.color_scale.start()

    def fade_in(self, dt, elapsed, duration=1):
        if self.is_faded:
            if self.start_fade(dt, elapsed):
                self.color_scale = TextColorScaleInterval(
                    self.pts_np, duration, False, 'easeIn')
                self.color_scale.start()

    def update(self, dt):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade_out=False)
                self.color_scale.start()
                self.status = Status.START

            case Status.START:
                if not self.color_scale.is_playing():
                    self.start()
                    self.status = Status.TO_PARTICLES

            case Status.TO_PARTICLES:
                self.fade_out(dt, 2.0)

                if self.to_particles():
                    self.status = Status.GO_BACK

            case Status.GO_BACK:
                if not self.color_scale.is_playing():
                    self.turn_back()
                    self.status = Status.TO_TEXT

            case Status.TO_TEXT:
                self.fade_in(dt, 0.5, 0.5)

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


class PerlinParticles(Fade):

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

            sx = perlin.pnoise2(nx + t, (ny + t) * 2) - 0.5
            sy = perlin.pnoise2((nx + t) * 2, ny + t) - 0.5
            ex = self.screen_size.x * 2 * sx
            ey = self.screen_size.y * 2 * sy

            tween = Tween(
                Point3(x, 0, y), Point3(ex, 0, ey), 3, yoyo=False, easing_type=self.easing_func)
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)


class DelayedStart(Fade):

    def __init__(self, text, easing_func='in_out_expo', do_fade=False):
        super().__init__(text, easing_func)
        self.do_fade = do_fade

    def delay_start(self, dt):
        cnt = 0
        self.total_dt += dt

        for tween in self.tweens:
            if not tween.is_playing:
                cnt += 1
                tween.delay_start(self.total_dt)

        if cnt == 0:
            self.total_dt = 0
            return True

    def update(self, dt):
        match self.status:

            case Status.SHOW_TEXT:
                self.create_tweens()
                self.color_scale = TextColorScaleInterval(self.pts_np, fade_out=False)
                self.color_scale.start()
                self.status = Status.START

            case Status.START:
                if not self.color_scale.is_playing():
                    if self.delay_start(dt):
                        self.status = Status.TO_PARTICLES

                    self.to_particles()

            case Status.TO_PARTICLES:
                if self.do_fade:
                    self.fade_out(dt, 0, 3)

                if self.to_particles():
                    self.status = Status.TURN

            case Status.TURN:
                if not self.color_scale.is_playing():
                    self.turn()
                    self.status = Status.GO_BACK

            case Status.GO_BACK:
                if self.do_fade:
                    self.fade_in(dt, 0, 1.5)

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


class SpreadSimplexParticles(DelayedStart):

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
            sx = simplex.snoise2(nx + t, (ny + t) * 3.0) - 0.5
            sy = simplex.snoise2((nx + t) * 0.5, ny + t) - 0.5

            spread = (1 - nx) * 100 - 150
            ex = self.screen_size.x * sx + random.random() * spread
            ey = self.screen_size.y * sy + random.random() * spread

            tween = Tween(
                Point3(x, 0, y), Point3(ex, 0, ey), 2, delay=nx, yoyo=False, easing_type=self.easing_func)
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)


class DelayedPerlinParticles(DelayedStart):

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

            pnx = perlin.pnoise2(nx + t, ny + t) - 0.5
            pny = perlin.pnoise2((nx + t) * 2, ny + t) - 0.5
            ex = self.screen_size.x * 2 * pnx
            ey = self.screen_size.y * 2 * pny

            tween = Tween(
                Point3(x, 0, y), Point3(ex, 0, ey), 3, delay=nx, yoyo=False, easing_type=self.easing_func)
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)


class SpreadFractalParticles(DelayedStart):

    def create_tweens(self):
        cnt = 0
        text_img = TextImage(self.text)
        vdata_values = array.array('f', [])

        perlin = PerlinNoise()
        fract = Fractal2D(perlin.pnoise2)
        t = random.randint(0, 1000)

        for px, py in text_img.pixel_coordinates():
            x = px - text_img.size.w / 2
            y = py - text_img.size.h / 2
            vdata_values.extend([x, 0, y])

            nx = px / text_img.size.w
            ny = py / text_img.size.h

            fx = fract.fractal(nx + t, (ny + t) * 2) - 0.5
            fy = fract.fractal((nx + t) * 2, ny + t) - 0.5

            spread = (1 - nx) * 400 - 400
            ex = self.screen_size.x * fx + random.random() * spread
            ey = self.screen_size.y * fy + random.random() * spread

            tween = Tween(
                Point3(x, 0, y), Point3(ex, 0, ey), 3, delay=nx, yoyo=False, easing_type=self.easing_func)
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)
