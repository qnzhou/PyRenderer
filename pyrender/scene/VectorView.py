import numpy as np
from numpy.linalg import norm
from .View import View
from .ViewDecorator import ViewDecorator
from pyrender.primitives.Primitive import Cylinder, Cone
from pyrender.color.ColorMap import ColorMap

class VectorView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ Syntax:
        {
            "type": "vector",
            "vector": vector_field,
            "color_map": color_map,
            "radius": scalar,
            "stem_radius": scalar,
            "max_length": max_length,
            "head_based": bool,
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = VectorView(nested_view, setting["vector"]);
        instance.max_length = setting["max_length"];
        instance.radius = setting.get("radius", instance.max_length * 0.2);
        instance.stem_radius = setting.get("stem_radius", instance.radius * 0.5);
        instance.color_map = setting.get("color_map", "jet");
        instance.head_based = setting.get("head_based", False);
        instance.generate_primitives();
        return instance;

    def __init__(self, nested_view, vector_field_name):
        super(VectorView, self).__init__(nested_view);
        self.vector_field_name = vector_field_name;

    def generate_primitives(self):
        self.load_vector_field();
        self.load_base_points();
        self.create_arrows();

    def create_arrows(self):
        magnitudes = norm(self.vector_field, axis=1);
        scale = self.max_length / np.amax(magnitudes);
        scaled_vectors = self.vector_field * scale;
        magnitudes *= scale;

        for v,p,l in zip(scaled_vectors, self.base_points, magnitudes):
            if l < 1e-6: continue;
            arrow_scale = l / self.max_length;

            c = self.color_map.get_color(l/self.max_length).color;
            v = v / l;
            if l < self.radius:
                if self.head_based:
                    arrow_head = Cone(p-v * l, p, l * arrow_scale);
                else:
                    arrow_head = Cone(p, p+v * l, l * arrow_scale);
                arrow_head.color = c;
                self.primitives.append(arrow_head);
            else:
                if self.head_based:
                    p2 = p - v * self.radius;
                    arrow_body = Cylinder(p2, p-v*l,
                            self.stem_radius * arrow_scale);
                    arrow_head = Cone(p2, p,
                            self.radius * arrow_scale);
                else:
                    p2 = p + v*(l - self.radius);
                    arrow_body = Cylinder(p, p2,
                            self.stem_radius * arrow_scale);
                    arrow_head = Cone(p2, p+v*l,
                            self.radius * arrow_scale);
                arrow_body.color = c;
                arrow_head.color = c;
                self.primitives.append(arrow_body);
                self.primitives.append(arrow_head);

    def load_vector_field(self):
        if not self.mesh.has_attribute(self.vector_field_name):
            raise RuntimeError("Vector attribute {} does not exist!".format(
                self.vector_field_name));

        field = self.mesh.get_attribute(self.vector_field_name).ravel();
        if (len(field) % 3 != 0):
            raise RuntimeError("Vector attribute {} is invalid!".format(
                self.vector_field_name));

        self.vector_field = field.reshape((-1, 3));

    def load_base_points(self):
        if len(self.vector_field) == self.mesh.num_vertices:
            self.base_points = self.mesh.vertices;
        elif len(self.vector_field) == self.mesh.num_faces:
            if not self.mesh.has_attribute("face_centroid"):
                self.mesh.add_attribute("face_centroid");
            self.base_points = self.mesh.get_attribute("face_centroid")\
                    .reshape((-1, 3));
        elif len(self.vector_field) == self.mesh.num_voxels:
            if not self.mesh.has_attribute("voxel_centroid"):
                self.mesh.add_attribute("voxel_centroid");
            self.base_points = self.mesh.get_attribute("voxel_centroid")\
                    .reshape((-1, 3));
        else:
            raise NotImplementedError("Unknown vector field type");

    def load_base_point_normals(self):
        if len(self.vector_field) == self.mesh.num_vertices:
            if not self.mesh.has_attribute("vertex_normal"):
                self.mesh.add_attribute("vertex_normal");
            self.base_point_normals = self.mesh.get_vertex_attribute(
                    "vertex_normal");
        elif len(self.vector_field) == self.mesh.num_faces:
            if not self.mesh.has_attribute("face_normal"):
                self.mesh.add_attribute("face_normal")
            self.base_point_normals = self.mesh.get_face_attribute(
                    "face_normal");
        elif len(self.vector_field) == self.mesh.num_voxels:
            raise NotImplementedError(
                    "base point normal of per voxel vector field is not supported");
        else:
            raise NotImplementedError("Unknown vector field type");

    @property
    def color_map(self):
        return self.__color_map;

    @color_map.setter
    def color_map(self, val):
        self.__color_map = ColorMap(val);

