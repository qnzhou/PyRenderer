import pymesh
import numpy as np
from numpy.linalg import norm

from .View import View
from .ViewDecorator import ViewDecorator

class ClippedView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "clipped",
            "plane": +X,+Y,+Z,-X,-Y,-Z,
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = ClippedView(nested_view, setting["plane"]);
        return instance;

    def __init__(self, nested_view, plane):
        super(ClippedView, self).__init__(nested_view);
        self.plane = plane;
        bbox_min, bbox_max = self.mesh.bbox;
        center = (bbox_min + bbox_max) * 0.5;
        if plane == "+X":
            should_keep = lambda(v) : v[0] > center[0];
        elif plane == "+Y":
            should_keep = lambda(v) : v[1] > center[1];
        elif plane == "+Z":
            should_keep = lambda(v) : v[2] > center[2];
        elif plane == "-X":
            should_keep = lambda(v) : v[0] < center[0];
        elif plane == "-Y":
            should_keep = lambda(v) : v[1] < center[1];
        elif plane == "-Z":
            should_keep = lambda(v) : v[2] < center[2];
        else:
            raise NotImplementedError("Unknown plane type: {}".format(plane));

        v_to_keep = np.array([should_keep(v) for v in self.view.vertices]);
        if len(self.view.voxels) > 0:
            self.V_to_keep = np.all(v_to_keep[self.view.voxels], axis=1);
            voxels = self.view.voxels[self.V_to_keep];
            self.mesh = pymesh.form_mesh(self.view.vertices, np.array([]), voxels);
        else:
            self.f_to_keep = np.all(v_to_keep[self.view.faces], axis=1);
            faces = self.view.faces[self.f_to_keep];
            self.mesh = pymesh.form_mesh(self.view.vertices, faces);

        self.mesh.add_attribute("face_normal");

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
    def face_normals(self):
        normals = self.mesh.get_face_attribute("face_normal");
        return np.repeat(normals, self.mesh.vertex_per_face, axis=0);

