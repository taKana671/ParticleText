import sys
from enum import Enum, auto

from direct.gui.DirectGui import DirectRadioButton
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode

from animations import SimplexParticles, TextColorScaleInterval


class Status(Enum):

    SHOW = auto()
    ANIMATION = auto()
    CHANGE = auto()
    HIDE = auto()


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


class EasingFuncDemo(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.set_background_color((0, 0, 0))

        self.camera.set_pos(0, -400, 0)
        self.camera.look_at(0, 0, 0)
        self.camLens.set_fov(90)

        self.create_gui()
        self.status = None
        self.change_func = False

        self.accept('escape', sys.exit)
        self.taskMgr.add(self.update, 'update')

    def create_gui(self):
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
        self.change_func = True

    def update(self, task):
        match self.status:

            case Status.SHOW:
                if not self.color_scale.is_playing():
                    self.animation.start()
                    self.status = Status.ANIMATION

            case Status.ANIMATION:
                if self.animation.to_particles():
                    self.status = Status.CHANGE

            case Status.CHANGE:
                if self.change_func:
                    self.status = Status.HIDE
                    self.color_scale = TextColorScaleInterval(self.animation.pts_np)
                    self.color_scale.start()
                    self.change_func = False

            case Status.HIDE:
                if not self.color_scale.is_playing():
                    self.animation.pts_np.remove_node()
                    self.status = None

            case _:
                func_name = '_'.join(self.mode + self.func)
                self.animation = SimplexParticles(func_name, func_name)
                self.animation.create_tweens()
                self.color_scale = TextColorScaleInterval(self.animation.pts_np, fade_out=False)
                self.animation.start()
                self.status = Status.SHOW

        return task.cont


if __name__ == '__main__':
    app = EasingFuncDemo()
    app.run()
