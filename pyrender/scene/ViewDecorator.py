from copy import deepcopy
import numpy as np
from .MeshView import MeshView

class ViewDecorator(MeshView):
    def __init__(self, view):
        self.view = view;

        # Deep copy all view properties.
        self.transform = deepcopy(self.view.transform);
        self.background = deepcopy(self.view.background);

    def __getattr__(self, name):
        """ This call forwards all attribute access to the view object.
        """
        return getattr(self.view, name);

    # The following overwrite the defined properties of MeshView class.

    @property
    def vertices(self):
        if not hasattr(self, "_vertices"):
            return self.view.vertices;
        else:
            return self._vertices;

    @vertices.setter
    def vertices(self, value):
        self._vertices = value;

    @property
    def faces(self):
        if not hasattr(self, "_faces"):
            return self.view.faces;
        else:
            return self._faces;

    @faces.setter
    def faces(self, value):
        self._faces = value;

    @property
    def voxels(self):
        if not hasattr(self, "_voxels"):
            return self.view.voxels;
        else:
            return self._voxels;

    @voxels.setter
    def voxels(self, value):
        self._voxels = value;

    @property
    def vertex_normals(self):
        if not hasattr(self, "_vertex_normals"):
            return self.view.vertex_normals;
        else:
            return self._vertex_normals;

    @vertex_normals.setter
    def vertex_normals(self, value):
        self._vertex_normals = value;

    @property
    def face_normals(self):
        if not hasattr(self, "_face_normals"):
            return self.view.face_normals;
        else:
            return self._face_normals;

    @face_normals.setter
    def face_normals(self, value):
        self._face_normals = value;

    @property
    def vertex_colors(self):
        if not hasattr(self, "_vertex_colors"):
            return self.view.vertex_colors;
        else:
            return self._vertex_colors;

    @vertex_colors.setter
    def vertex_colors(self, value):
        self._vertex_colors = value;

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

        assert(len(self.transform) == 12);

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
    def with_colors(self):
        return self.view.with_colors;

    @property
    def with_uniform_colors(self):
        return self.view.with_uniform_colors;

    @property
    def with_wire_frame(self):
        return self.view.with_wire_frame;

    @with_wire_frame.setter
    def with_wire_frame(self, val):
        self.view.with_wire_frame = val;

    @property
    def line_width(self):
        return self.view.line_width;

    @line_width.setter
    def line_width(self, line_width):
        self.view.line_width = line_width;

    @property
    def with_alpha(self):
        return self.view.with_alpha;

    @property
    def subviews(self):
        return self.view.subviews;

    @subviews.setter
    def subviews(self, val):
        self.view.subviews = val;

