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

from animations import RandomParticles, PerlinParticles, DelayPerlinParticles, DelaySimplexParticles
from animations import SimplexParticles


class Particles(Enum):

    RANDOM = auto()
    PERLIN = auto()
    SIMPLEX = auto()
    DELAY_SIMPLEX = auto()
    ANIMATION = auto()
    DELAY_PERLIN = auto()
    DEBUG = auto()


class Status(Enum):

    SETUP = auto()
    SHOW_TEXT = auto()
    START_TWEEN = auto()
    HIDE_TEXT = auto()
    TO_PARTICLES = auto()
    TURN_BACK = auto()
    TO_TEXT = auto()
    SHOW_PARTICLES = auto()


class TextColorScaleInterval(LerpColorScaleInterval):

    def __init__(self, np, duration=1, fade=True, blend_type='easeInOut'):
        color_scale = (1, 1, 1, 0) if fade else (1, 1, 1, 1)
        start_color = (1, 1, 1, 1) if fade else (1, 1, 1, 0)
        super().__init__(np, duration, color_scale, start_color, blendType=blend_type)


class ParticleText(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        self.delay_starting = False
        self.is_move = False
        self.is_reverse = False

        self.mode = None

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
        self.animation.finish()
        # for tween in self.tweens:
        #     tween.finish()

    def pause(self):
        self.animation.pause()
        # for tween in self.tweens:
        #     tween.pause()

    def resume(self):
        self.animation.resume()
        # for tween in self.tweens:
            # tween.resume()

    def delay_start(self, dt):
        # self.total_dt += dt

        for tween in self.tweens:
            if not tween.delay_started:
                tween.delay_start(self.total_dt)


        # if not self.is_fade and self.total_dt > 2:
        #     self.points_np.colorScaleInterval(2, (1, 1, 1, 0), blendType='easeInOut').start()
        #     self.is_fade = True

    def start_move(self):
        # self.mode = Particles.RANDOM
        # self.mode = Particles.PERLIN
        # self.mode = Particles.DELAY_PERLIN
        # self.mode = Particles.DELAY_SIMPLEX
        self.mode = Particles.SIMPLEX

    def to_simplex_particles(self, text):
        cnt = 0
        text_img = TextImage(text)
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

            tween = Tween(Point3(x, 0, y), Point3(ex, 0, ey), 3, delay=nx, yoyo=True, easing_type='in_out_expo')
            self.tweens.append(tween)
            cnt += 1

        self.create_points(vdata_values, cnt)

    def update(self, task):
        dt = globalClock.get_dt()

        match self.mode:

            case Particles.RANDOM:
                self.animation = RandomParticles('Panda3D Hello World')
                self.mode = Particles.ANIMATION

            case Particles.PERLIN:
                self.animation = PerlinParticles('Bullet Hello World')
                self.mode = Particles.ANIMATION

            case Particles.DELAY_PERLIN:
                self.animation = DelayPerlinParticles('Start 3D programming')
                self.mode = Particles.ANIMATION

            case Particles.DELAY_SIMPLEX:
                self.animation = DelaySimplexParticles('Create Noise Texture')
                self.mode = Particles.ANIMATION

            case Particles.SIMPLEX:
                self.animation = SimplexParticles('Try Creative Coding')
                self.animation.create_tweens()
                self.animation.loop()
                self.mode = Particles.DEBUG

            case Particles.ANIMATION:
                if self.animation.update(dt):
                    self.mode = None

            case Particles.DEBUG:
                self.animation.update(dt)

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
