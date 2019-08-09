import numpy as np
from numpy.linalg import norm
import math
from pyrender.color.Color import get_color, Color
from pyrender.color.ColorMap import ColorMap
from pyrender.primitives.Primitive import Cylinder, Cone, Sphere
import pymesh
import random
from .View import View

class MeshView(View):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "mesh_only",
            "mesh": mesh_file,
            "color": color_name,
            "wire_frame": bool,
            "line_color": color_name,
            "line_width": float, # default to 0.1
            "smooth_normal": bool,
            "bbox": [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        }
        """
        mesh_file = setting["mesh"];
        instance = MeshView(mesh_file);
        instance.color_name = setting.get("color", None);
        instance.line_width = setting.get("line_width", instance.line_width);
        instance.line_color = setting.get("line_color", "dark_gray");
        instance.smooth_normal = setting.get("smooth_normal", False);
        if "bbox" in setting:
            instance.bmin = np.array(setting["bbox"][0]);
            instance.bmax = np.array(setting["bbox"][1]);
        instance.fit_into_unit_sphere();
        instance.with_wire_frame = setting.get("wire_frame", False);
        return instance;

    def __init__(self, mesh_file):
        super(MeshView, self).__init__();
        self.mesh = pymesh.load_mesh(mesh_file);
        self.__init_mesh();

    def __init_mesh(self):
        if not self.mesh.has_attribute("vertex_normal"):
            self.mesh.add_attribute("vertex_normal");
        if not self.mesh.has_attribute("face_normal"):
            self.mesh.add_attribute("face_normal");
        if self.mesh.num_vertices > 0:
            bmin, bmax = self.mesh.bbox;
            self.bmin = bmin;
            self.bmax = bmax;
        else:
            self.bmin = np.zeros(self.mesh.dim);
            self.bmax = np.ones(self.mesh.dim);

    def fit_into_unit_sphere(self, diagonal_len=2.0):
        self.center = (self.bmin + self.bmax) * 0.5;
        self.scale = diagonal_len / norm(self.bmax - self.bmin);

    def generate_primitives(self):
        if self.mesh.num_faces <= 0:
            return;

        self.primitives = [];
        d = norm(self.bmax - self.bmin) / math.sqrt(self.mesh.dim);
        radius = d * self.line_width;
        assert(radius > 0);
        vertices, edges = pymesh.mesh_to_graph(self.mesh);
        lengths = norm(vertices[edges[:,0],:] - vertices[edges[:,1],:], axis=1);
        color = get_color(self.line_color);
        for v in vertices:
            ball = Sphere(v, radius);
            ball.color = color;
            self.primitives.append(ball);

        for e,l in zip(edges, lengths):
            if l <= 0.5 * radius : continue;
            cylinder = Cylinder(vertices[e[0]], vertices[e[1]], radius);
            cylinder.color = color;
            self.primitives.append(cylinder);

    @property
    def vertices(self):
        return self.mesh.vertices;

    @property
    def faces(self):
        return self.mesh.faces;

    @property
    def voxels(self):
        return self.mesh.voxels;

    @property
    def vertex_normals(self):
        """ Return corner field.  One vector per face corner.
        """
        normals = self.mesh.get_vertex_attribute("vertex_normal");
        return normals[self.mesh.faces.ravel(order="C")];

    @property
    def face_normals(self):
        """ Return corner field.  One vector per face corner.
        """
        normals = self.mesh.get_face_attribute("face_normal");
        return np.repeat(normals, self.mesh.vertex_per_face, axis=0);

    @property
    def use_smooth_normal(self):
        return self.smooth_normal;

    @property
    def vertex_colors(self):
        """ Return corner field.  One vector per face corner.
        """
        if self.color_name == "random":
            c = ColorMap("RdYlBu").get_color(
                    random.choice([0.1, 0.3, 0.5, 0.7, 0.9]));
        elif self.color_name is not None:
            c = get_color(self.color_name);
        else:
            c = get_color("nylon_white");

        c.color[-1] = self.alpha;
        colors = np.array([[c.color] * self.mesh.vertex_per_face] *
                self.mesh.num_faces);
        return colors;

    @property
    def with_colors(self):
        return self.color_name != None;

    @property
    def with_uniform_colors(self):
        return True;

    @property
    def with_wire_frame(self):
        return self.__with_wire_frame;

    @with_wire_frame.setter
    def with_wire_frame(self, val):
        self.__with_wire_frame = val;
        if val:
            self.generate_primitives();

    @property
    def with_alpha(self):
        return self.alpha != 1.0;

    @property
    def with_texture_coordinates(self):
        return False;

    @property
    def texture_coordinates(self):
        if self.with_texture_coordinates:
            return self.mesh.get_attribute("corner_texture");
        else:
            return np.array([]);

