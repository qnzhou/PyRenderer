import numpy as np
from numpy.linalg import norm
from .View import View
from pyrender.color.ColorMap import ColorMap

from .DeformationView import DeformationView

class CompositeView(View):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "composite",
            "views": [
                {
                    # other views
                },
                {
                    # other views
                },
            "unified_deform_magnitude": scalar
            ]
        }
        """
        views = [];
        for view_setting in setting["views"]:
            view = View.create_from_setting(view_setting);
            if not isinstance(view, View):
                raise RuntimeError(
                        "Subview of composite view must be a simple view!");
            views.append(view);
        instance = CompositeView(views);
        instance.unified_deformation_magnitude =\
                setting.get("unified_deform_magnitude",
                        instance.unified_deformation_magnitude);
        instance.initialize_views();
        return instance;

    def __init__(self, views):
        super(CompositeView, self).__init__();
        self.views = views;
        self.subviews = views;
        self.unified_deformation_magnitude = None;

    def initialize_views(self):
        self.__unify_deformation_views();
        self.__combine_views();
        self.__fit_into_unit_sphere();

    def __unify_deformation_views(self):
        if self.unified_deformation_magnitude is None: return;
        magnitudes = [ ];
        for view in self.views:
            if isinstance(view, DeformationView):
                magnitudes.append(view.vector_field_max_magnitude);
        max_magnitude = np.max(magnitudes);
        for view in self.views:
            if isinstance(view, DeformationView):
                view.deformation_magnitude = \
                        self.unified_deformation_magnitude *\
                        view.vector_field_max_magnitude / max_magnitude;

    def __combine_views(self):
        vertices = [];
        faces = [];
        voxels = [];
        vertex_normals = [];
        face_normals = [];
        vertex_colors = [];

        num_vertices = 0;
        for view in self.views:
            vtx = view.vertices;
            vtx = np.dot(view.rotation, vtx.T) + \
                    view.translation[:, np.newaxis];
            vtx = vtx.T;

            vertices.append(vtx);
            if len(view.faces) > 0:
                faces.append(view.faces + num_vertices);
            if len(view.voxels) > 0:
                voxels.append(view.voxels + num_vertices);
            if len(view.vertex_normals) > 0:
                vertex_normals.append(view.vertex_normals);
            if len(view.face_normals) > 0:
                face_normals.append(view.face_normals);
            if len(view.vertex_colors) > 0:
                vertex_colors.append(view.vertex_colors);
            num_vertices += len(vtx);

        if len(vertices) > 0:
            self.__vertices = np.vstack(vertices);
        else:
            self.__vertices = np.zeros((0, 3));
        if len(faces) > 0:
            self.__faces = np.vstack(faces);
        else:
            self.__faces = np.zeros((0, 3));
        if len(voxels) > 0:
            self.__voxels = np.vstack(voxels);
        else:
            self.__voxels = np.zeros((0, 4));
        if len(vertex_normals) > 0:
            self.__vertex_normals = np.vstack(vertex_normals);
        else:
            self.__vertex_normals = np.zeros((0, 3, 3));
        if len(face_normals) > 0:
            self.__face_normals = np.vstack(face_normals);
        else:
            self.__face_normals = np.zeros((0, 3));
        if len(vertex_colors) > 0:
            self.__vertex_colors = np.vstack(vertex_colors);
        else:
            self.__vertex_colors = np.zeros((0, 3, 4));
        self.primitives = sum([view.primitives for view in self.views], []);

        self.with_wire_frame = np.any([view.with_wire_frame for view in
            self.views]);

    def __fit_into_unit_sphere(self, diagonal_len=2.0):
        self.bmin = np.amin(self.vertices, axis=0);
        self.bmax = np.amax(self.vertices, axis=0);
        self.center = (self.bmin + self.bmax) * 0.5;
        self.scale = diagonal_len / norm(self.bmax - self.bmin);

    @property
    def vertices(self):
        return self.__vertices;

    @property
    def faces(self):
        return self.__faces;

    @property
    def voxels(self):
        return self.__voxels;

    @property
    def vertex_normals(self):
        return self.__vertex_normals;

    @property
    def face_normals(self):
        return self.__face_normals;

    @property
    def vertex_colors(self):
        return self.__vertex_colors;

    @property
    def with_colors(self):
        return True;

    @property
    def with_alpha(self):
        return np.any([v.with_alpha for v in self.views]);

