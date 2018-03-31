import numpy as np
from numpy.linalg import norm
import random
from .View import View
from .ViewDecorator import ViewDecorator
from pyrender.color.ColorMap import ColorMap
import pymesh

class ScalarView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "scalar",
            "scalar": scalar_field,
            "color_map": color_map,
            "discrete": boolean,
            "normalize": boolean,
            "alpha": float,
            "bounds": [min_val, max_val], # use None if not needed
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = ScalarView(nested_view, setting["scalar"]);
        instance.discrete = setting.get("discrete", False);
        instance.normalize = setting.get("normalize", True);
        instance.color_map = setting.get("color_map", "jet");
        instance.alpha = setting.get("alpha", 1.0);
        instance.bounds = setting.get("bounds", [None, None]);
        assert(len(instance.bounds) == 2);
        instance.update_vertex_color();
        return instance;

    def __init__(self, nested_view, scalar_field_name):
        super(ScalarView, self).__init__(nested_view);
        self.scalar_field_name = scalar_field_name;

    def update_vertex_color(self):
        if len(self.mesh.vertices) == 0:
            return;
        self.__load_scalar_field();

        self.vertex_colors = [];
        if self.discrete:
            unique_values = np.unique(self.scalar_field);
            keys = np.linspace(0, 1, len(unique_values));
            random.shuffle(keys);
            value_to_color = {
                    v:self.color_map.get_color(k).color
                    for v,k in zip(unique_values, keys)};
            for face_values in self.scalar_field:
                colors = [value_to_color[v] for v in face_values];
                self.vertex_colors.append(colors);
        else:
            for face_values in self.scalar_field:
                colors = [self.color_map.get_color(v).color
                        for v in face_values];
                self.vertex_colors.append(colors);
        self.vertex_colors = np.array(self.vertex_colors);
        self.vertex_colors[:,:,-1] = self.alpha;

    def __load_scalar_field(self):
        if not self.mesh.has_attribute(self.scalar_field_name):
            raise RuntimeError("Scalar attribute {} does not exist!".format(
                self.scalar_field_name));
        field = self.mesh.get_attribute(self.scalar_field_name).ravel().copy();

        if self.normalize:
            field = self.__normalize_scalar_field(field);
        field = self.__convert_to_corner_field(field);

        min_val = np.amin(field) if self.bounds[0] is None else self.bounds[0];
        max_val = np.amax(field) if self.bounds[1] is None else self.bounds[1];

        if max_val > min_val:
            field = (field - min_val) / (max_val - min_val);
            np.clip(field, 0.0, 1.0, field);
        else:
            field = np.zeros_like(field);

        self.scalar_field = field.reshape((-1, self.mesh.vertex_per_face));
        assert(self.scalar_field.shape[0] == self.mesh.num_faces);

    def __convert_to_corner_field(self, field):
        field_size = len(field);
        num_vertices = self.mesh.num_vertices;
        num_faces = self.mesh.num_faces;
        num_voxels = self.mesh.num_voxels;

        if field_size == num_vertices:
            vertex_indices = self.mesh.faces;
            field = field[vertex_indices];
        elif field_size == num_faces:
            field = np.repeat(field, self.mesh.vertex_per_face);
        elif field_size == num_voxels:
            field = pymesh.convert_to_face_attribute_from_name(self.mesh,
                    self.scalar_field_name);
            field = np.repeat(field, self.mesh.vertex_per_face);
        else:
            raise RuntimeError("Attribute {} is not a valid scalar field"\
                    .format(self.scalar_field_name));
        return field;

    def __normalize_scalar_field(self, field):
        field_size = len(field);
        num_vertices = self.mesh.num_vertices;
        num_faces = self.mesh.num_faces;
        num_voxels = self.mesh.num_voxels;

        if field_size == num_vertices:
            return self.__normalize_vertex_field(field);
        elif field_size == num_faces:
            return self.__normalize_face_field(field);
        elif field_size == num_voxels:
            return self.__normalize_voxel_field(field);

    def __normalize_vertex_field(self, field):
        if self.mesh.num_voxels > 0:
            element_volume_field_name = "vertex_volume";
        else:
            element_volume_field_name = "vertex_area";

        if not self.mesh.has_attribute(element_volume_field_name):
            self.mesh.add_attribute(element_volume_field_name);
        weights = self.mesh.get_attribute(element_volume_field_name).ravel();
        return self.__normalize_field_with_weight(field, weights);

    def __normalize_face_field(self, field):
        face_area_field_name = "face_area";
        if not self.mesh.has_attribute(face_area_field_name):
            self.mesh.add_attribute(face_area_field_name);
        weights = self.mesh.get_attribute(face_area_field_name).ravel();
        return self.__normalize_field_with_weight(field, weights);

    def __normalize_voxel_field(self, field):
        voxel_volume_field_name = "voxel_volume";
        if not self.mesh.has_attribute(voxel_volume_field_name):
            self.mesh.add_attribute(voxel_volume_field_name);
        weights = self.mesh.get_attribute(voxel_volume_field_name).ravel();
        return self.__normalize_field_with_weight(field, weights);

    def __normalize_field_with_weight(self, field, weights):
        assert(len(field) == len(weights));

        order = np.argsort(field);
        cumu_weights = np.cumsum(weights[order]);
        cumu_weights /= cumu_weights[-1];

        field[order] = cumu_weights;
        return field;


    @property
    def color_map(self):
        return self.__color_map;

    @color_map.setter
    def color_map(self, val):
        self.__color_map = ColorMap(val);

    @property
    def with_colors(self):
        return True;

    @property
    def with_uniform_colors(self):
        return False;

    @property
    def with_alpha(self):
        return self.alpha != 1.0;
