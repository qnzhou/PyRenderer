#!/usr/bin/env python
import os

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    raise ImportError("PyOpenGL is not installed properly");

#from GUIBackEnd import GUIBackEnd
from pyrender.renderer.RendererFactory import RendererFactory

RAISE_WINDOW_CMD = \
'''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' '''

class GUIFrontEnd:
    def __init__(self, scene):
        #self.__class__.back_end = GUIBackEnd(scene);
        self.__class__.back_end =\
                RendererFactory.create_OpenGL_renderer_from_scene(scene);
        self.__register_callbacks();
        os.system(RAISE_WINDOW_CMD);
        glutMainLoop()

    def __register_callbacks(self):
        glutDisplayFunc      (self.__class__.display);
        glutMouseFunc        (self.__class__.mouse);
        glutKeyboardFunc     (self.__class__.keyboard);
        glutPassiveMotionFunc(self.__class__.passivemotion);
        glutMotionFunc       (self.__class__.motion);

    @classmethod
    def display(cls):
        try:
            cls.back_end.render();
        except Exception as e:
            import traceback
            import sys
            traceback.print_exc();
            sys.exit(-1);

    @classmethod
    def idle(cls):
        cls.back_end.idle();

    @classmethod
    def mouse(cls, button, state, x, y):
        cls.back_end.mouse(button, state, x, y);

    @classmethod
    def keyboard(cls, key, x, y):
        cls.back_end.keyboard(key, x, y);

    @classmethod
    def passivemotion(cls, x, y):
        cls.back_end.passivemotion(x, y);

    @classmethod
    def motion(cls, x, y):
        cls.back_end.motion(x, y);

if __name__ == "__main__":
    window = GUIFrontEnd();
