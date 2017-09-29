import numpy as np
from pyrender.color.Color import color_table

class Primitive(object):
    def __init__(self):
        self.color = color_table["nylon_white"];

class Cylinder(Primitive):
    def __init__(self, p0, p1, r):
        super(Cylinder, self).__init__();
        self.end_points = [p0, p1];
        self.radius = r;

class Cone(Primitive):
    def __init__(self, p0, p1, r):
        super(Cone, self).__init__();
        self.end_points = [p0, p1];
        self.radius = r;

class Sphere(Primitive):
    def __init__(self, center, radius):
        super(Sphere, self).__init__();
        self.center = center;
        self.radius = radius;
