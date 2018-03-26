import numpy as np
from numpy.linalg import norm
from pyrender.color.Color import color_table, Color
from pyrender.color.ColorMap import ColorMap
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
            "line_width": float, # default to 0.001
            "bbox": [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        }
        """
        mesh_file = setting["mesh"];
        instance = MeshView(mesh_file);
        instance.color_name = setting.get("color", None);
        instance.with_wire_frame = setting.get("wire_frame", False);
        instance.line_width = setting.get("line_width", instance.line_width);
        if "bbox" in setting:
            instance.bmin = np.array(setting["bbox"][0]);
            instance.bmax = np.array(setting["bbox"][1]);
        instance.fit_into_unit_sphere();
        return instance;

    def __init__(self, mesh_file):
        super(MeshView, self).__init__();
        self.mesh = pymesh.load_mesh(mesh_file);
        self.__init_mesh();

    def __init_mesh(self):
        self.mesh.add_attribute("vertex_normal");
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
        return normals[self.mesh.faces];

    @property
    def face_normals(self):
        """ Return corner field.  One vector per face corner.
        """
        normals = self.mesh.get_face_attribute("face_normal");
        return np.repeat(normals, self.mesh.vertex_per_face, axis=0);

    @property
    def vertex_colors(self):
        """ Return corner field.  One vector per face corner.
        """
        if self.color_name == "random":
            c = ColorMap("RdYlBu").get_color(
                    random.choice([0.1, 0.3, 0.5, 0.7, 0.9]));
        elif self.color_name is not None:
            c = color_table[self.color_name];
        else:
            c = color_table["nylon_white"];

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

