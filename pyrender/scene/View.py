import os.path
import numpy as np
from numpy.linalg import norm

class View(object):
    @classmethod
    def create_from_setting(cls, setting):
        view_type = setting["type"];
        if view_type == "mesh_only":
            from .MeshView import MeshView;
            instance = MeshView.create_from_setting(setting);
        elif view_type == "scalar":
            from .ScalarView import ScalarView;
            instance = ScalarView.create_from_setting(setting);
        elif view_type == "vector":
            from .VectorView import VectorView;
            instance = VectorView.create_from_setting(setting);
        elif view_type == "vector_cluster":
            from .VectorClusterView import VectorClusterView
            instance = VectorClusterView.create_from_setting(setting);
        elif view_type == "deformation":
            from .DeformationView import DeformationView
            instance = DeformationView.create_from_setting(setting);
        elif view_type == "composite":
            from .CompositeView import CompositeView
            instance = CompositeView.create_from_setting(setting);
        elif view_type == "circum":
            from .CircumView import CircumView
            instance = CircumView.create_from_setting(setting);
        elif view_type == "deformation_sequence":
            from .DeformationSequenceView import DeformationSequenceView
            instance = DeformationSequenceView.create_from_setting(setting);
        elif view_type == "sphere":
            from .SphereView import SphereView
            instance = SphereView.create_from_setting(setting);
        elif view_type == "clipped":
            from .ClippedView import ClippedView
            instance = ClippedView.create_from_setting(setting);
        elif view_type == "wire_network":
            from .WireView import WireView
            instance = WireView.create_from_setting(setting);
        else:
            raise NotImplementedError(
                    "View type {} is not supported.".format(view_type));

        # Optional generic setting
        if isinstance(instance, View):
            instance.name = setting.get("name", instance.name);
            instance.width = setting.get("width", instance.width);
            instance.height = setting.get("height", instance.height);
            instance.with_quarter = setting.get("with_quarter",
                    instance.with_quarter);
            instance.with_axis = setting.get("with_axis", instance.with_axis);
            instance.transparent_bg = setting.get("transparent_bg",
                    instance.transparent_bg);
            instance.background = setting.get("background", instance.background);
            instance.transform = setting.get("transform", instance.transform);
            if "alpha" in setting:
                instance.alpha = setting["alpha"];

        return instance;

    def __init__(self):
        self.name = "viewer_output.png";
        self.transparent_bg = False;
        self.width = 800;
        self.height = 600;
        self.with_quarter = False;
        self.with_axis = False;
        self.background = "d";
        self.default_transform = np.array([
            1.0, 0.0, 0.0,   # rotation column 1
            0.0, 1.0, 0.0,   # rotation column 2
            0.0, 0.0, 1.0,   # rotation column 3
            0.0, 0.0, 0.0]); # translation vector
        self.transform = np.copy(self.default_transform);
        self.alpha = 1.0;
        self.primitives = [];
        self.subviews = [];

    def __validate_transform_field(self):
        if len(self.transform) != 12:
            raise RuntimeError("transform field is ill-formated.");

    @property
    def vertices(self):
        raise NotImplementedError("Calling abstract method");

    @property
    def faces(self):
        raise NotImplementedError("Calling abstract method");

    @property
    def voxels(self):
        raise NotImplementedError("Calling abstract method");

    @property
    def vertex_normals(self):
        raise NotImplementedError("Calling abstract method");

    @property
    def face_normals(self):
        raise NotImplementedError("Calling abstract method");

    @property
    def vertex_colors(self):
        raise NotImplementedError("Calling abstract method");

    @property
    def with_colors(self):
        return False;

    @property
    def with_uniform_colors(self):
        return True;

    @property
    def with_wire_frame(self):
        if hasattr(self, "__with_wire_frame"):
            return self.__with_wire_frame;
        else:
            return False;

    @with_wire_frame.setter
    def with_wire_frame(self, val):
        self.__with_wire_frame = val;

    @property
    def with_alpha(self):
        return False;

    @property
    def primitives(self):
        return self.__primitives;

    @primitives.setter
    def primitives(self, val):
        self.__primitives = val;

    @property
    def transform(self):
        return self.__transform;

    @transform.setter
    def transform(self, val):
        if val is None:
            pass; # Use the default values.
        elif isinstance(val, list):
            self.__transform = np.array(val);
        elif isinstance(val, np.ndarray):
            self.__transform = val;
        else:
            raise RuntimeError("Unknow transform field format: {}".format(val));

        self.__validate_transform_field();

    @property
    def rotation(self):
        return self.transform[0:9].reshape((3,3), order="F");

    @rotation.setter
    def rotation(self, val):
        val = val.ravel(order="F");
        assert(len(val) ==  9);
        self.transform[0:9] = val;

    @property
    def translation(self):
        return self.transform[-3:];

    @translation.setter
    def translation(self, val):
        assert(len(val) == 3);
        self.transform[-3:] = val;

    @property
    def background(self):
        return self.__background;

    @background.setter
    def background(self, val):
        if val in ["d", "l", "n"]:
            self.__background = val;
        else:
            raise RuntimeError("Background \"{}\" is invalid".format(val));

    @property
    def subviews(self):
        return self.__subviews;

    @subviews.setter
    def subviews(self, val):
        self.__subviews = val;

