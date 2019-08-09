import numpy as np
from numpy.linalg import norm
from pyrender.color.Color import get_color, Color
from pyrender.color.ColorMap import ColorMap
from pyrender.primitives.Primitive import Cylinder, Cone, Sphere
import pymesh

from .View import View

class WireView(View):
    @classmethod
    def create_from_setting(cls, setting):
        """ Syntax:
        {
            "type": "wire_network",
            "wire_network": wire_file,
            "color": color_name,
            "radius": radius,
            "bbox": [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        }
        """
        wire_file = setting["wire_network"];
        instance = WireView(wire_file);
        instance.color_name = setting.get("color", None);
        instance.radius = setting.get("radius", 0.1);
        if "bbox" in setting:
            instance.bmin = np.array(setting["bbox"][0]);
            instance.bmax = np.array(setting["bbox"][1]);
        instance.fit_into_unit_sphere();
        instance.generate_primitives();
        return instance;

    def __init__(self, wire_file):
        super(WireView, self).__init__();
        self.wires = pymesh.wires.WireNetwork();
        self.wires.load_from_file(wire_file);
        self.__init_wires();

    def __init_wires(self):
        if self.wires.num_vertices > 0:
            bmin, bmax = self.wires.bbox;
            self.bmin = bmin;
            self.bmax = bmax;
        else:
            self.bmin = np.zeros(self.wires.dim);
            self.bmax = np.ones(self.wires.dim);

    def fit_into_unit_sphere(self, diagonal_len=2.0):
        self.center = (self.bmin + self.bmax) * 0.5;
        self.scale = diagonal_len / norm(self.bmax - self.bmin);

    def generate_primitives(self):
        if self.color_name is None:
            self.color = get_color("nylon_white");
        elif self.color_name == "random":
            self.color = ColorMap("RdYlBu").get_color(
                    random.choice([0.1, 0.3, 0.5, 0.7, 0.9]));
        else:
            self.color = get_color(self.color_name);

        self.wires.add_attribute("edge_length");
        vertices = self.wires.vertices;
        edges = self.wires.edges;
        lengths = self.wires.get_attribute("edge_length");
        for v in vertices:
            ball = Sphere(v, self.radius);
            ball.color = self.color;
            self.primitives.append(ball);

        for e,l in zip(edges, lengths):
            if l <= 0.1 * self.radius : continue;
            cylinder = Cylinder(vertices[e[0]], vertices[e[1]], self.radius);
            cylinder.color = self.color;
            self.primitives.append(cylinder);

    @property
    def vertices(self):
        return np.zeros((0, 3));

    @property
    def faces(self):
        return np.zeros((0, 3), dtype=int);

    @property
    def voxels(self):
        return np.zeros((0, 4), dtype=int);

    @property
    def vertex_normals(self):
        return np.zeros((0, 3, 3));

    @property
    def face_normals(self):
        return np.zeros((0, 3));

    @property
    def vertex_colors(self):
        return np.zeros((0, 3, 4));
