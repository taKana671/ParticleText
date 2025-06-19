import sys
from enum import Enum, auto

from direct.gui.DirectGui import DirectEntry
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock

from animations import (
    RandomParticles,
    SimplexParticles,
    SpreadFractalParticles,
    DelayedPerlinParticles,
    SpreadSimplexParticles
)


class Particles(Enum):

    RANDOM = auto()
    FRACTAL_PERLIN = auto()
    SIMPLEX = auto()
    DELAY_PERLIN = auto()
    SPREAD_SIMPLEX = auto()


class Status(Enum):

    ANIMATION = auto()
    SELECT = auto()


class ParticleText(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        self.camera.set_pos(0, -400, 0)
        self.camera.look_at(0, 0, 0)
        self.camLens.set_fov(90)

        self.modes = list(Particles)
        self.idx = 0
        self.status = None
        self.text = ''
        self.entry = None

        self.accept('p', self.pause)
        self.accept('r', self.resume)
        self.accept('c', self.change_text)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

    def pause(self):
        self.animation.pause()

    def resume(self):
        self.animation.resume()

    def change_text(self):
        if self.entry is None:
            self.entry = DirectEntry(
                parent=self.a2dBottomLeft,
                pos=(0.05, 0.05, 0.05),
                scale=0.07,
                width=20,
                frameColor=(1, 1, 1, 1),
                focus=True,
                command=self.get_new_text
            )
        else:
            self.entry.reparent_to(self.a2dBottomLeft)
            self.entry.set('')
            self.entry.setFocus()

    def get_new_text(self, text):
        self.text = text
        self.entry.detach_node()

    def update(self, task):
        dt = globalClock.get_dt()

        match self.status:

            case Status.SELECT:
                match self.modes[self.idx]:

                    case Particles.RANDOM:
                        t = self.text if self.text else 'Panda3D Hello World'
                        self.animation = RandomParticles(t)

                    case Particles.FRACTAL_PERLIN:
                        t = self.text if self.text else 'Bullet Hello World'
                        self.animation = SpreadFractalParticles(t, easing_func='in_out_back')

                    case Particles.SIMPLEX:
                        t = self.text if self.text else 'Try Creative Coding'
                        self.animation = SimplexParticles(t)

                    case Particles.DELAY_PERLIN:
                        t = self.text if self.text else 'Enjoy 3D programming'
                        self.animation = DelayedPerlinParticles(t, do_fade=True, easing_func='out_back')

                    case Particles.SPREAD_SIMPLEX:
                        t = self.text if self.text else 'I Love panda3D'
                        self.animation = SpreadSimplexParticles(t, easing_func='in_back')

                self.status = Status.ANIMATION
                self.idx = next_idx if (next_idx := self.idx + 1) < len(self.modes) else 0

            case Status.ANIMATION:
                if self.animation.update(dt):
                    self.status = Status.SELECT

            case _:
                self.status = Status.SELECT

        return task.cont


if __name__ == '__main__':
    app = ParticleText()
    app.run()
