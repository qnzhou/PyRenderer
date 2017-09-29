from math import pi
import numpy as np
from numpy.linalg import norm
import PyMesh

class Cluster:
    def __init__(self, points):
        self.points = points;
        self.normals = None;
        self.normal_angle_threshold = pi / 2.0;
        self.vectors = None;
        self.vector_angle_threshold = pi / 2.0;

    def use_normals(self, normals):
        self.normals = normals;

    def use_vectors(self, vectors):
        self.vectors = vectors;

    def run(self, cluster_radius, max_iterations = 10):
        self.radius = cluster_radius;
        self.__init_clusters();
        for i in range(max_iterations):
            converged = self.__update_clusters();
            if converged: break;

    def __init_clusters(self):
        num_pts = len(self.points);

        self.grid = PyMesh.HashGrid.create(self.radius);
        self.grid.insert_multiple(np.arange(num_pts, dtype=int), self.points);

        self.seeds = [];
        self.clusters = [];

        visited = np.zeros(num_pts, dtype=bool);
        for i in range(num_pts):
            if visited[i]: continue;
            seed_point, seed_normal, seed_vector = self.__get_data(i);

            neighbors = self.grid.get_items_near_point(seed_point).ravel();
            neighbors = self.__filter_based_on_distance(seed_point, neighbors);
            neighbors = self.__filter_based_on_normal(seed_normal, neighbors);
            neighbors = self.__filter_based_on_vector(seed_vector, neighbors);

            visited[neighbors] = True;
            self.seeds.append((seed_point, seed_normal, seed_vector));
            self.clusters.append(neighbors);

    def __update_clusters(self):
        self.__update_cluster_seeds();
        seed_offsets = self.__form_clusters();
        return np.amax(seed_offsets) < 0.1 * self.radius;

    def __update_cluster_seeds(self):
        num_clusters = len(self.clusters);
        assert(num_clusters == len(self.seeds));

        seed_offsets = [];
        for i in range(num_clusters):
            curr_seed_point, curr_seed_normal, curr_seed_vector = self.seeds[i];
            indices = self.clusters[i];

            seed_point = np.mean(self.points[indices], axis=0);
            seed_normal = np.mean(self.normals[indices], axis=0);
            seed_vector = np.mean(self.vectors[indices], axis=0);
            self.seeds[i] = (seed_point, seed_normal, seed_vector);

            seed_offsets.append(norm(curr_seed_point - seed_point));
        return seed_offsets;

    def __form_clusters(self):
        num_clusters = len(self.clusters);
        num_pts = len(self.points);
        visited = np.zeros(num_pts, dtype=bool);

        for i in range(num_clusters):
            seed_point, seed_normal, seed_vector = self.seeds[i];

            neighbors = self.grid.get_items_near_point(seed_point).ravel();
            neighbors = neighbors[np.logical_not(visited[neighbors])];

            neighbors = self.__filter_based_on_distance(seed_point, neighbors);
            neighbors = self.__filter_based_on_normal(seed_normal, neighbors);
            neighbors = self.__filter_based_on_vector(seed_vector, neighbors);

            visited[neighbors] = True;
            self.seeds.append((seed_point, seed_normal, seed_vector));
            self.clusters.append(neighbors);

    def __filter_based_on_distance(self, seed_point, candidates):
        candidate_points = self.points[candidates];
        distances = norm(candidate_points - seed_point, axis=1);
        return candidates[distances < self.radius];

    def __filter_based_on_normal(self, seed_normal, candidates):
        candidate_normals = self.normals[candidates];
        projections = np.dot(candidate_normals, seed_normal);
        projections = np.clip(projections, -1.0, 1.0);
        angles = np.arccos(projections);
        return candidates[np.fabs(angles) < self.normal_angle_threshold];

    def __filter_based_on_vector(self, seed_vector, candidates):
        candidate_vectors = self.vectors[candidates];
        projections = np.dot(candidate_vectors, seed_vector);
        cross_vectors = norm(np.cross(candidate_vectors, seed_vector), axis=1);
        angles = np.arctan2(cross_vectors, projections);
        assert(not np.isnan(angles).any());
        return candidates[np.fabs(angles) < self.vector_angle_threshold];

    def __get_data(self, i):
        p = self.points[i];
        n = np.zeros(3) if self.normals is None else self.normals[i];
        v = np.zeros(3) if self.vectors is None else self.vectors[i];
        return p,n,v;

