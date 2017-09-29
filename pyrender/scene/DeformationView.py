import numpy as np
from numpy.linalg import norm
from .View import View
from .ViewDecorator import ViewDecorator
from pyrender.color.ColorMap import ColorMap

from PyMeshUtils import convert_to_face_attribute_from_name

class DeformationView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "deformation",
            "vector": vector_field,
            "deform_magnitude": scalar,
            "deform_factor": scalar,
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = DeformationView(nested_view, setting["vector"]);
        instance.deformation_magnitude = setting.get("deform_magnitude",
                instance.deformation_magnitude);
        instance.deformation_factor = setting.get("deform_factor",
                instance.deformation_factor);
        instance.compute_deformed_vertices();
        return instance;

    def __init__(self, nested_view, vector_field_name):
        super(DeformationView, self).__init__(nested_view);
        self.vector_field_name = vector_field_name;
        self.deformation_magnitude = None;
        self.deformation_factor = 1.0;
        self.__load_vector_field();

    def __load_vector_field(self):
        self.vector_field = self.mesh.get_vertex_attribute(
                self.vector_field_name);
        self.vector_field_max_magnitude = np.amax(
                norm(self.vector_field, axis=1));

    def compute_deformed_vertices(self):
        vts = self.view.vertices;
        if self.deformation_magnitude is not None:
            factor = self.deformation_factor *\
                    self.deformation_magnitude /\
                    self.vector_field_max_magnitude;
        else:
            factor = self.deformation_factor;
        vts += self.vector_field * factor;
        self.vertices = vts;
