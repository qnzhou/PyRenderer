import numpy as np
from numpy.linalg import norm
from math import pi
from .View import View
from .VectorView import VectorView
from pyrender.color.ColorMap import ColorMap
from pyrender.misc.cluster import Cluster

import PyMesh

class VectorClusterView(VectorView):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "vector_cluster",
            "vector": vector_field,
            "color_map": color_map,
            "radius": scalar,
            "stem_radius": scalar,
            "cluster_radius": scalar,
            "magnitude_filter": percentage,
            "max_length": max_length,
            "head_based": bool,
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = VectorClusterView(nested_view, setting["vector"]);
        instance.max_length = setting["max_length"];
        instance.radius = setting.get("radius", instance.max_length * 0.2);
        instance.stem_radius = setting.get("stem_radius", instance.radius * 0.5);
        instance.cluster_radius = setting.get("cluster_radius", 
                instance.radius * 1.5);
        instance.magnitude_filter = setting.get("magnitude_filter", 0.0);
        instance.color_map = setting.get("color_map", "jet");
        instance.head_based = setting.get("head_based", False);
        instance.generate_primitives();
        return instance;

    def __init__(self, nested_view, vector_field_name):
        super(VectorClusterView, self).__init__(nested_view, vector_field_name);

    def generate_primitives(self):
        self.load_vector_field();
        self.load_base_points();
        self.load_base_point_normals();
        magnitudes = norm(self.vector_field, axis=1);
        max_magnitude = np.max(magnitudes);
        magnitude_threshold = max(1e-6, max_magnitude * self.magnitude_filter);

        non_zero = magnitudes > magnitude_threshold;
        self.vector_field = self.vector_field[non_zero];
        self.base_points = self.base_points[non_zero];
        self.base_point_normals = self.base_point_normals[non_zero];

        self.cluster_vectors();
        self.create_arrows();

    def cluster_vectors(self):
        cluster = Cluster(self.base_points);
        cluster.use_normals(self.base_point_normals);
        cluster.normal_angle_threshold = pi / 3.0;
        cluster.use_vectors(self.vector_field);
        cluster.run(self.cluster_radius);

        self.base_points = np.array([seed[0] for seed in cluster.seeds]);
        self.vector_field = np.array([seed[2] for seed in cluster.seeds]);
