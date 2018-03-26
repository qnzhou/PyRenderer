import inspect
import json
import numpy as np
from numpy.linalg import norm
import os
import os.path
import sys

from .Camera import Camera
from .Light import Light
from .View import View

from pyrender.misc.json_utils import remove_unicode
from pyrender.misc.quaternion import Quaternion
from pyrender.misc.direction import direction_map

class Scene(object):
    @classmethod
    def create_from_file(cls, scene_file):
        instance = cls();
        instance.update_scene_from_file(scene_file);
        return instance;

    @classmethod
    def create_from_dict(cls, setting):
        instance = cls();
        instance.update_scene_from_dict(setting);
        return instance;

    @classmethod
    def create_basic_scene(cls, mesh_file):
        setting = {
                "views": [{
                    "type": "mesh_only",
                    "mesh": mesh_file
                    }]
                };
        return cls.create_from_dict(setting);

    @classmethod
    def create_basic_scalar_scene(cls,
            mesh_file, scalar_field, color_map="jet",
            bounds=None, discrete=False, normalize=False):
        setting = {
                "views": [{
                    "type": "scalar",
                    "scalar": scalar_field,
                    "normalize": normalize,
                    "color_map": color_map,
                    "discrete": discrete,
                    "view": {
                        "type": "mesh_only",
                        "mesh": mesh_file,
                        }
                    }]
                };
        if bounds is not None:
            setting["views"][0]["bounds"] = bounds;
        return cls.create_from_dict(setting);

    @classmethod
    def create_texture_scene(cls, mesh_file, uv_scale, uv_offset):
        setting = {
                "views": [{
                    "type": "texture",
                    "uv_scale": uv_scale,
                    "uv_offset": uv_offset,
                    "view": {
                        "type": "mesh_only",
                        "mesh": mesh_file
                        }
                    }]
                };
        return cls.create_from_dict(setting);

    def update_scene_from_file(self, scene_file):
        self.scene_file = scene_file;
        if scene_file is not None:
            customized_setting = self.__load_setting(scene_file);
            self.update_scene_from_dict(customized_setting);
        else:
            self.update_scene_from_dict({});

    def update_scene_from_dict(self, custom_setting):
        setting = self.__load_default_setting();
        setting.update(custom_setting);

        self.__initialize_scene(setting);
        self.__initialize_cameras(setting);
        self.__initialize_lights(setting);
        self.__initialize_views(setting);

    def activate_camera(self, camera_idx=0):
        if len(self.cameras) == 0:
            raise RuntimeError("At least one camera is required.");
        self.__active_camera_idx = camera_idx;

    def activate_view(self, view_idx=0):
        if len(self.views) == 0:
            raise RuntimeError("At least one image is required");
        self.__active_view_idx = view_idx;

    def set_orientation(self, up_dir=None, front_dir=None,
            facing_camera=None, head_on=None):
        if up_dir is not None:
            self.up_dir = up_dir;
        if front_dir is not None:
            self.front_dir = front_dir;
        if facing_camera is not None:
            self.facing_camera = facing_camera;
        if head_on is not None:
            self.head_on = head_on;
        self.__compute_global_transform();

    def __initialize_scene(self, setting):
        curr_dir = os.getcwd();
        self.output_dir = setting.get("output_dir", curr_dir);
        self.up_dir = setting.get("up_dir", None);
        self.front_dir = setting.get("front_dir", None);
        self.facing_camera = setting.get("facing_camera", False);
        self.head_on = setting.get("head_on", False);

    def __initialize_cameras(self, setting):
        camera_configs = setting.get("cameras");
        self.cameras = [Camera.create_from_setting(cam_setting)
                for cam_setting in camera_configs];
        self.activate_camera();

    def __initialize_lights(self, setting):
        light_configs = setting.get("lights");
        self.lights = [Light.create_from_setting(light_setting)
                for light_setting in light_configs];

    def __initialize_views(self, setting):
        setting = self.__remove_relative_mesh_path(setting);
        view_configs = setting.get("views");
        views = [View.create_from_setting(view_setting)
                for view_setting in view_configs];
        self.views = [];
        for view in views:
            if isinstance(view, list):
                self.views += view;
            else:
                self.views.append(view);
        self.activate_view();
        self.__compute_global_transform();

    def __remove_relative_mesh_path(self, setting):
        if not hasattr(self, "scene_file"):
            return setting;

        scene_file_dir = os.path.dirname(self.scene_file);

        def remove_rel_path(config):
            if isinstance(config, list):
                return [remove_rel_path(val) for val in config]
            elif isinstance(config, dict):
                for key,val in config.items():
                    if key == "mesh":
                        mesh_file = val;
                        if mesh_file is not None and (not os.path.isabs(mesh_file)):
                            config[key] = os.path.join(scene_file_dir, mesh_file);
                    else:
                        val = remove_rel_path(val);
                        config[key] = val;
                return config
            else:
                return config;

        return remove_rel_path(setting);

    def __compute_global_transform(self):
        self.global_transform = np.eye(4);
        orientation = Quaternion();
        if self.up_dir is not None:
            up_dir = direction_map[self.up_dir];
            cur_dir = orientation.rotate(up_dir);
            tar_dir = self.active_camera.up_direction;
            rot = Quaternion.fromData(cur_dir, tar_dir);
            orientation = rot * orientation;

        if self.front_dir is not None:
            front_dir = direction_map[self.front_dir];
            cur_dir = orientation.rotate(front_dir);
            if self.facing_camera or self.head_on:
                camera_dir = self.active_camera.location - self.active_camera.look_at_point;
                tar_dir = np.array([camera_dir[0], 0.0, camera_dir[2]]);
                tar_dir /= norm(tar_dir);
            else:
                tar_dir = direction_map['Z'];
            if self.up_dir is not None:
                rot = Quaternion.fromDataBestFit(cur_dir, tar_dir,
                        self.active_camera.up_direction);
            else:
                rot = Quaternion.fromData(cur_dir, tar_dir);
            orientation = rot * orientation;

            if self.head_on:
                camera_dir /= norm(camera_dir);
                rot = Quaternion.fromData(tar_dir, camera_dir);
                orientation = rot * orientation;
        init_rot_matrix = orientation.to_matrix();

        self.global_transform[:3,:3] = init_rot_matrix;

    def __load_default_setting(self):
        scene_dir = os.path.dirname(inspect.getfile(Scene));
        DEFAULT_SCENE_FILE = os.path.join(scene_dir, "default_scene.json");
        return self.__load_setting(DEFAULT_SCENE_FILE);

    def __load_setting(self, scene_file):
        with open(scene_file, 'r') as fin:
            setting = json.load(fin);
            setting = remove_unicode(setting);
            return setting;

    @property
    def active_camera(self):
        return self.cameras[self.__active_camera_idx]

    @property
    def active_view(self):
        return self.views[self.__active_view_idx]

    @active_view.setter
    def active_view(self, val):
        self.views[self.__active_view_idx] = val;


