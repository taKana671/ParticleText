import sys
from enum import Enum, auto

from direct.gui.DirectGui import DirectRadioButton
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import TextNode
from animations import SimplexParticles


class Particles(Enum):

    RANDOM = auto()
    PERLIN = auto()
    DELAY_PERLIN = auto()
    SPREAD_SIMPLEX = auto()


class Status(Enum):

    ANIMATION = auto()
    SELECT = auto()
    FINISH = auto()


class RadioButton(DirectRadioButton):

    def __init__(self, txt, pos, variable, command):
        super().__init__(
            parent=base.a2dBottomLeft,
            pos=pos,
            frameSize=(-2.5, 2.5, -0.5, 0.5),
            frameColor=(1, 1, 1, 0),
            scale=0.06,
            text_align=TextNode.ALeft,
            text=txt,
            text_pos=(-1.5, -0.3),
            text_fg=(1, 1, 1, 1),
            value=[txt],
            variable=variable,
            command=command
        )
        self.initialiseoptions(type(self))


class ChooseEasingFunc(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        self.camera.set_pos(0, -400, 0)
        self.camera.look_at(0, 0, 0)
        self.camLens.set_fov(90)

        self.create_entry()
        self.modes = list(Particles)
        self.idx = 0
        self.status = None
        self.text = ''
        self.entry = None
        self.ease_func = 'in_sine'
        self.finish = False

        # self.accept('c', self.change_text)
        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

    def create_entry(self):
        funcs = ['sine', 'cubic', 'quint', 'circ', 'elastic', 'quad', 'quart', 'expo', 'back', 'bounce']
        modes = ['in', 'out', 'in_out']
        self.func = funcs[:1]
        self.mode = modes[:1]
        start_z = 1.9

        radios = []
        for i, name in enumerate(funcs):
            z = start_z - i * 0.08
            pos = (0.2, 0, z)
            radio = RadioButton(name, pos, self.func, self.choose_easing)
            radios.append(radio)

        for r in radios:
            r.setOthers(radios)

        radios = []
        for i, name in enumerate(modes):
            z = start_z - i * 0.08
            pos = (0.52, 0, z)
            radio = RadioButton(name, pos, self.mode, self.choose_easing)
            radios.append(radio)

        for r in radios:
            r.setOthers(radios)

    def choose_easing(self):
        self.finish = True
        # print(self.func)
        # print(self.mode)

    def get_new_text(self, text):
        self.text = text
        # self.entry.detach_node()
        print(self.text)

    def update(self, task):
        dt = globalClock.get_dt()

        match self.status:

        #     case Status.SELECT:
        #         match self.modes[self.idx]:

        #             case Particles.RANDOM:
        #                 t = self.text if self.text else 'Panda3D Hello World'
        #                 self.animation = RandomParticles(t)

        #             case Particles.PERLIN:
        #                 t = self.text if self.text else 'Bullet Hello World'
        #                 self.animation = PerlinParticles(t)

        #             case Particles.DELAY_PERLIN:
        #                 t = self.text if self.text else 'Start 3D programming'
        #                 self.animation = DelayedPerlinParticles(t)

        #             case Particles.SPREAD_SIMPLEX:
        #                 t = self.text if self.text else 'Enjoy 3D programming'
        #                 self.animation = SpreadSimplexParticles(t)

        #         self.status = Status.ANIMATION
        #         self.idx = next_idx if (next_idx := self.idx + 1) < len(self.modes) else 0

            case Status.ANIMATION:
                self.animation.update(dt)

                if self.finish:
                    self.animation.finish()
                    self.status = Status.FINISH
                    self.finish = False

            case Status.FINISH:
                if self.animation.update(dt):
                    self.status = None

            case _:
                func_name = '_'.join(self.mode + self.func)
                self.animation = SimplexParticles(func_name, func_name)
                self.status = Status.ANIMATION

        return task.cont


if __name__ == '__main__':
    app = ChooseEasingFunc()
    app.run()
