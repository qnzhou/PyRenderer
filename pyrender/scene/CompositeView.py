import numpy as np
from numpy.linalg import norm
from .View import View
from pyrender.color.ColorMap import ColorMap

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
        return instance;

    def __init__(self, views):
        super(CompositeView, self).__init__();
        self.views = views;
        self.subviews = views;
        vertices = self.vertices;
        self.bmin = np.amin(vertices, axis=0);
        self.bmax = np.amax(vertices, axis=0);
        self.center = 0.5 * (self.bmin + self.bmax);
        self.scale = 2.0 / norm(self.bmax - self.bmin);

    @property
    def vertices(self):
        return np.vstack([view.vertices for view in self.subviews]);

    @property
    def faces(self):
        offsets = [0] + [view.vertices.shape[0] for view in self.subviews];
        offsets = offsets[0:-1];
        return np.vstack([view.facets + offset
            for view, offset in zip(self.subviews, offsets)]);

    @property
    def voxels(self):
        offsets = [0] + [view.vertices.shape[0] for view in self.subviews];
        offsets = offsets[0:-1];
        return np.vstack([view.voxels + offset
            for view, offset in zip(self.subviews, offsets)]);

    @property
    def vertex_normals(self):
        return np.vstack([view.vertex_normals for view in self.subviews]);

    @property
    def face_normals(self):
        return np.vstack([view.face_normals for view in self.subviews]);

    @property
    def vertex_colors(self):
        return np.vstack([view.vertex_colors for view in self.subviews]);

    @property
    def with_colors(self):
        return np.any([view.with_colors for view in self.subviews]);

    @property
    def with_uniform_colors(self):
        return np.all([view.with_uniform_colors for view in self.subviews]);

    @property
    def with_alpha(self):
        return np.any([view.with_alpha for view in self.subviews]);

