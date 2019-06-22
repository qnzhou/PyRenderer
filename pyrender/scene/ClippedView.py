import pymesh
import numpy as np
from numpy.linalg import norm
import tempfile
import hashlib
import os.path

from .View import View
from .ViewDecorator import ViewDecorator
from .MeshView import MeshView
from pyrender.color.Color import color_table, Color

class ClippedView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "clipped",
            "plane": +X,+Y,+Z,-X,-Y,-Z, or [nx, ny, nz, o]
                s.t. the plane define is nx*x + ny*y + nz*z < o
            "cut_ratio": float between 0 and 1,
            "interior_color": "color_name"
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = ClippedView(nested_view, setting["plane"],
                setting.get("interior_color", "blue"),
                setting.get("exterior_color", "yellow"),
                setting.get("cut_ratio", 0.5));
        return instance;

    def __init__(self, nested_view, plane, interior_color, exterior_color,
            cut_ratio):
        super(ClippedView, self).__init__(nested_view);
        self.plane = plane;
        bbox_min = self.view.bmin;
        bbox_max = self.view.bmax;
        center = bbox_min * cut_ratio + bbox_max * (1.0 - cut_ratio);
        if plane == "+X":
            should_keep = lambda v: v[0] > center[0];
        elif plane == "+Y":
            should_keep = lambda v: v[1] > center[1];
        elif plane == "+Z":
            should_keep = lambda v: v[2] > center[2];
        elif plane == "-X":
            should_keep = lambda v: v[0] < center[0];
        elif plane == "-Y":
            should_keep = lambda v: v[1] < center[1];
        elif plane == "-Z":
            should_keep = lambda v: v[2] < center[2];
        elif isinstance(plane, list) and len(plane) == 4:
            n = np.array(plane[:3]);
            n = n / norm(n);
            should_keep = lambda v: np.dot(v-center, n) < plane[3];
        else:
            raise NotImplementedError("Unknown plane type: {}".format(plane));

        if len(self.view.voxels) > 0:
            mesh = pymesh.form_mesh(self.view.vertices, np.array([]),
                    self.view.voxels);
            mesh.add_attribute("voxel_centroid");
            mesh.add_attribute("voxel_face_index");
            voxel_face_id = mesh.get_voxel_attribute("voxel_face_index").astype(int);
            centroids = mesh.get_voxel_attribute("voxel_centroid");
            self.V_to_keep = [should_keep(v) for v in centroids];
            voxels_to_keep = self.view.voxels[self.V_to_keep];
            voxel_face_id = voxel_face_id[self.V_to_keep];
            self.mesh = pymesh.form_mesh(self.view.vertices, np.zeros((0,3)), voxels_to_keep);
            self.mesh.add_attribute("voxel_face_index");
            new_voxel_face_id = self.mesh.get_voxel_attribute("voxel_face_index").astype(int);

            old_vertex_colors = self.vertex_colors;
            new_vertex_colors = np.zeros((self.mesh.num_faces, 3, 4));
            cut_color = color_table[interior_color];
            cut_color = np.array([cut_color.red, cut_color.green,
                cut_color.blue, cut_color.alpha]);
            is_interface = np.zeros(self.mesh.num_faces, dtype=bool);
            for old_i,new_i in zip(voxel_face_id.ravel(), new_voxel_face_id.ravel()):
                if new_i >= 0 and old_i >= 0:
                    new_vertex_colors[new_i] = old_vertex_colors[old_i];
                elif new_i >= 0:
                    is_interface[new_i] = True;
                    new_vertex_colors[new_i,:] = cut_color;

            self.vertex_colors = new_vertex_colors;
            self.interface = pymesh.form_mesh(self.mesh.vertices,
                    self.mesh.faces[is_interface]);
            self.boundary = pymesh.form_mesh(self.mesh.vertices,
                    self.mesh.faces[np.logical_not(is_interface)]);
            #self.vertex_colors = new_vertex_colors[is_interface];
            tmp_dir = tempfile.gettempdir();
            m = hashlib.md5();
            m.update(self.mesh.vertices);
            name = m.hexdigest();
            bd_mesh_file = os.path.join(tmp_dir, "{}_bd.msh".format(name));
            interface_mesh_file = os.path.join(tmp_dir, "{}_interface.msh".format(name));
            pymesh.save_mesh(bd_mesh_file, self.boundary);
            pymesh.save_mesh(interface_mesh_file, self.interface);
            self.subviews = [
                    MeshView.create_from_setting({
                        "type": "mesh_only",
                        "mesh": bd_mesh_file,
                        "color": exterior_color,
                        "wire_frame": True,
                        "bbox": [self.bmin, self.bmax]
                        }),
                    MeshView.create_from_setting({
                        "type": "mesh_only",
                        "mesh": interface_mesh_file,
                        "color": interior_color,
                        "wire_frame": True,
                        "bbox": [self.bmin, self.bmax]
                        }),
                    ];
        else:
            centroids = np.mean(self.view.vertices[self.view.faces], axis=1);
            self.V_to_keep = [should_keep(v) for v in centroids];
            faces = self.view.faces[self.V_to_keep];
            self.mesh = pymesh.form_mesh(self.view.vertices, faces);
            self.vertex_colors = self.vertex_colors[self.V_to_keep];

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

    @property
    def with_colors(self):
        return True;

    @property
    def with_uniform_colors(self):
        return True;

