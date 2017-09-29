import numpy as np

from .View import View
from .ViewDecorator import ViewDecorator
from pyrender.primitives.Primitive import Sphere
from pyrender.color.ColorMap import ColorMap
from pyrender.misc.cluster import cluster

class SphereView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ Syntax:
        {
            "type": "sphere",
            "scalar": scalar_field,
            "color_map": color_map,
            "radius_range": [min_radius, max_radius],
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = SphereView(nested_view, setting["scalar"]);
        instance.color_map = setting.get("color_map", "jet");
        instance.radius_range = setting["radius_range"];
        instance.generate_primitives();
        return instance;

    def __init__(self, nested_view, scalar_field_name):
        super(SphereView, self).__init__(nested_view);
        self.scalar_field_name = scalar_field_name;
        self.__load_scalar_field();
        self.__load_base_points();

    def generate_primitives(self):
        assert(len(self.scalar_field) == len(self.base_points));
        assert(self.radius_range[1] > self.radius_range[0]);

        self.__cluster_points();

        # hide actual mesh
        color = self.vertex_colors;
        color[:,:,-1] = 0.0;
        self.vertex_colors = color;

        min_val = np.amin(self.scalar_field);
        max_val = np.amax(self.scalar_field);
        radius_gap = self.radius_range[1] - self.radius_range[0];
        value_gap = max_val - min_val;
        for value, base in zip(self.scalar_field, self.base_points):
            ratio = (value - min_val) / value_gap;
            radius = self.radius_range[0] + ratio * radius_gap;
            if radius > 1e-6:
                ball = Sphere(base, radius);
                ball.color = self.color_map.get_color(ratio).color;
                self.primitives.append(ball);

    def __load_scalar_field(self):
        if not self.mesh.has_attribute(self.scalar_field_name):
            raise RuntimeError("Scalar field {} does not exist!".format(
                self.scalar_field_name));
        self.scalar_field = self.mesh.get_attribute(self.scalar_field_name).ravel(); 

    def __load_base_points(self):
        num_entries = len(self.scalar_field);
        if num_entries == self.mesh.num_vertices:
            self.base_points = self.mesh.vertices;
        elif num_entries == self.mesh.num_faces:
            if not self.mesh.has_attribute("face_centroid"):
                self.mesh.add_attribute("face_centroid");
            self.base_points = self.mesh.get_attribute("face_centroid")\
                    .reshape((-1, 3), order="C");
        elif num_entries == self.mesh.num_voxels:
            if not self.mesh.has_attribute("voxel_centroid"):
                self.mesh.add_attribute("voxel_centroid");
            self.base_points = self.mesh.get_attribute("voxel_centroid")\
                    .reshape((-1, 3), order="C");

    def __cluster_points(self):
        cluster_radius = self.radius_range[1] * 2;
        clusters = cluster(self.scalar_field, self.base_points,
                cluster_radius);

        self.base_points = np.array([
            np.mean(self.base_points[indices], axis=0)
            for indices in clusters]);
        self.scalar_field = np.array([
            np.mean(self.scalar_field[indices], axis=0)
            for indices in clusters]);

    @property
    def color_map(self):
        return self.__color_map;

    @color_map.setter
    def color_map(self, val):
        self.__color_map = ColorMap(val);

