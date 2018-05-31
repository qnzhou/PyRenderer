import inspect
import multiprocessing
import numpy as np
from numpy.linalg import norm
from math import atan2, degrees
import os.path
from collections import OrderedDict
import datetime
import tempfile

from mitsuba.core import PluginManager, Scheduler, Statistics, LocalWorker, Thread
from mitsuba.core import Transform, Point, Vector, Matrix4x4, Spectrum, Color3
from mitsuba.render import Scene, RenderQueue, RenderJob, SceneHandler

from pyrender.primitives.Primitive import Cylinder, Cone, Sphere
from pyrender.renderer.AbstractRenderer import AbstractRenderer
import pymesh
from .serialization import serialize_mesh

class MitsubaRenderer(AbstractRenderer):
    def __init__(self, scene):
        super(MitsubaRenderer, self).__init__(scene);

    def render(self):
        self.__initialize();
        self.__add_integrator();
        self.__add_lights();
        self.__add_active_camera();
        self.__add_active_view();
        self.__add_active_primitives();
        self.__add_others();
        self.__run_mitsuba();

    def __initialize(self):
        self.__initialize_mitsuba_setting();
        self.__initialize_image_setting();
        self.__initialize_geometry_setting();

    def __initialize_mitsuba_setting(self):
        self.plgr = PluginManager.getInstance();
        self.output_dir = self.scene.output_dir;

        mitsuba_module_path = os.path.dirname(
                inspect.getfile(MitsubaRenderer));
        self.file_resolver = Thread.getThread().getFileResolver();
        self.file_resolver.appendPath(os.path.join(
            mitsuba_module_path, "xml_files/"));
        self.file_resolver.appendPath(os.path.join(
            mitsuba_module_path, "textures/"));
        self.file_resolver.appendPath(os.path.join(
            mitsuba_module_path, "shapes/"));

        self.mitsuba_scene = Scene();

    def __initialize_image_setting(self):
        active_view = self.scene.active_view;
        self.image_name = os.path.join(self.output_dir, active_view.name);
        self.image_width = active_view.width;
        self.image_height = active_view.height;

    def __initialize_geometry_setting(self):
        active_view = self.scene.active_view;
        self.global_transform = self.scene.global_transform;
        self.floor_height = None;
        if len(active_view.vertices) > 0:
            global_rotation = self.scene.global_transform[:3, :3];

            vertices = (active_view.vertices - active_view.center) * active_view.scale;
            vertices = np.dot(active_view.rotation, vertices.T) +\
                    active_view.translation[:, np.newaxis];
            vertices = np.dot(global_rotation, vertices);
            vertices = vertices.T;
            self.transformed_bbox_min = np.amin(vertices, axis=0);
            self.transformed_bbox_max = np.amax(vertices, axis=0);

            center = 0.5 * (self.transformed_bbox_min + self.transformed_bbox_max);
            self.floor_height = self.transformed_bbox_min[1] - center[1];
        else:
            dim = active_view.vertices.shape[1];
            self.transformed_bbox_min = np.zeros(dim);
            self.transformed_bbox_max = np.ones(dim);
            self.floor_height = 0;

    def __add_integrator(self):
        if self.with_alpha:
            integrator = self.plgr.create({
                "type": "volpath",
                "rrDepth": 20
                });
        else:
            integrator = self.plgr.create({
                "type": "direct",
                "shadingSamples": 16
                });
        self.mitsuba_scene.addChild(integrator);

    def __add_lights(self):
        #TODO: load lights from scene
        front_light = self.plgr.create({
            "type": "sphere",
            "center": Point(3.0, 6.0, 4.0),
            "radius": 2.5,
            "emitter": {
                "type": "area",
                "radiance": Spectrum(10.0),
                "samplingWeight": 10.0
                }
            });

        side_light = self.plgr.create({
            "type": "point",
            "position": Point(4.0, 4.0, -1.0),
            "intensity": Spectrum(5.0)
            });

        back_light = self.plgr.create({
            "type": "point",
            "position": Point(-0, 5.0, -1),
            "intensity": Spectrum(5.0)
            });

        self.mitsuba_scene.addChild(front_light);
        #self.mitsuba_scene.addChild(side_light);
        #self.mitsuba_scene.addChild(back_light);

    def __add_active_camera(self):
        active_view = self.scene.active_view;
        camera = self.scene.active_camera;
        if active_view.transparent_bg:
            pixel_format = "rgba";
        else:
            pixel_format = "rgb";

        crop_bbox = np.array(camera.crop_bbox);
        if np.amax(crop_bbox) <= 1.0:
            # bbox is relative.
            crop_bbox[:,0] *= self.image_width;
            crop_bbox[:,1] *= self.image_height;

        assert(np.all(crop_bbox >= 0));
        assert(np.all(crop_bbox[:,0] <= self.image_width));
        assert(np.all(crop_bbox[:,1] <= self.image_height));

        mitsuba_camera = self.plgr.create({
            "type": "perspective",
            "fov": float(camera.fovy),
            "fovAxis": "y",
            "toWorld": Transform.lookAt(
                Point(*camera.location),
                Point(*camera.look_at_point),
                Vector(*camera.up_direction)),
            "film": {
                "type": "ldrfilm",
                "width": self.image_width,
                "height": self.image_height,
                "cropOffsetX": int(crop_bbox[0,0]),
                "cropOffsetY": int(crop_bbox[0,1]),
                "cropWidth": int(crop_bbox[1,0] - crop_bbox[0,0]),
                "cropHeight": int(crop_bbox[1,1] - crop_bbox[0,1]),
                "banner": False,
                "pixelFormat": pixel_format,
                "rfilter": {
                    "type": "gaussian"
                    }
                },
            "sampler": {
                "type": "halton",
                "sampleCount": 4,
                }
            });
        self.mitsuba_scene.addChild(mitsuba_camera);

    def __add_active_view(self):
        self.__add_view(self.scene.active_view);

    def __add_view(self, active_view, parent_transform=None):
        if len(active_view.subviews) > 0:
            for view in active_view.subviews:
                if parent_transform is None:
                    view_transform = self.__get_view_transform(active_view);
                else:
                    view_transform = parent_transform * self.__get_view_transform(active_view);
                self.__add_view(view, view_transform);
            return;

        if len(active_view.faces) == 0: return;

        old_active_view = self.scene.active_view;
        self.scene.active_view = active_view;
        mesh_file, ext = self.__save_temp_mesh(active_view);
        normalize_transform = self.__get_normalize_transform(active_view);
        view_transform = self.__get_view_transform(active_view);
        if parent_transform is not None:
            view_transform = parent_transform * view_transform;
        glob_transform = self.__get_glob_transform();

        total_transform = glob_transform * view_transform * normalize_transform;
        material_setting = self.__get_material_setting(active_view);
        setting = {
                "type": ext[1:],
                "filename": mesh_file,
                "faceNormals": True,
                "toWorld": total_transform
                }
        setting.update(material_setting);
        target_shape = self.plgr.create(setting);
        self.mitsuba_scene.addChild(target_shape);

        M = (view_transform * normalize_transform).getMatrix();
        M = np.array([
            [   M[0, 0],
                M[0, 1],
                M[0, 2],
                M[0, 3]],
            [   M[1, 0],
                M[1, 1],
                M[1, 2],
                M[1, 3]],
            [   M[2, 0],
                M[2, 1],
                M[2, 2],
                M[2, 3]],
            [   M[3, 0],
                M[3, 1],
                M[3, 2],
                M[3, 3]],
            ]);
        vertices = active_view.vertices;
        vertices = np.hstack((vertices, np.ones((len(vertices), 1))));
        vertices = np.dot(M, vertices.T).T
        vertices = np.divide(vertices[:,0:3],
                vertices[:,3][:,np.newaxis]);
        self.transformed_bbox_min = np.amin(vertices, axis=0);
        self.transformed_bbox_max = np.amax(vertices, axis=0);
        center = 0.5 * (self.transformed_bbox_min + self.transformed_bbox_max);
        floor_height = self.transformed_bbox_min[1] - center[1];
        if self.floor_height is None or self.floor_height > floor_height:
            self.floor_height = floor_height;

        self.scene.active_view = old_active_view;

    def __add_active_primitives(self):
        self.__add_primitives(self.scene.active_view);

    def __add_primitives(self, active_view, parent_transform=None):
        if len(active_view.subviews) > 0:
            for view in active_view.subviews:
                if parent_transform is None:
                    view_transform = self.__get_view_transform(active_view);
                else:
                    view_transform = parent_transform * self.__get_view_transform(active_view);
                self.__add_primitives(view, view_transform);
            return;

        old_active_view = self.scene.active_view;
        self.scene.active_view = active_view;
        scale = active_view.scale;
        normalize_transform = self.__get_normalize_transform(active_view);
        view_transform = self.__get_view_transform(active_view);
        if parent_transform is not None:
            view_transform = parent_transform * view_transform;
        glob_transform = self.__get_glob_transform();
        total_transform = glob_transform * view_transform * normalize_transform;

        primitives = self.scene.active_view.primitives;
        for shape in primitives:
            if shape.color[3] <= 0.0: continue;
            color = {
                    "type": "plastic",
                    "diffuseReflectance": Spectrum(shape.color[:3].tolist())
                    };
            if shape.color[3] < 1.0:
                color = {
                        "type": "mask",
                        "opacity": Spectrum(active_view.alpha),
                        "bsdf": color
                        };
            if isinstance(shape, Cylinder):
                if shape.radius <= 0.0: continue;
                setting = self.__add_cylinder(shape);
                setting["bsdf"] = color;
                setting["toWorld"] = total_transform
            elif isinstance(shape, Cone):
                if shape.radius <= 0.0: continue;
                setting = self.__add_cone(shape);
                setting["bsdf"] = color;
                setting["toWorld"] = total_transform * setting["toWorld"];
            elif isinstance(shape, Sphere):
                if shape.radius <= 0.0: continue;
                # Due to weird behavior in Mitsuba, all transformation is
                # applied directly on radius and center variable.
                setting = self.__add_sphere(shape);
                setting["radius"] *= scale;
                setting["center"] = total_transform * setting["center"];
                setting["bsdf"] = color;
            else:
                raise NotImplementedError("Unknown primitive: {}".format(shape));

            mitsuba_primative = self.plgr.create(setting);
            self.mitsuba_scene.addChild(mitsuba_primative);
        self.scene.active_view = old_active_view;

    def __add_sphere(self, shape):
        setting = {
                "type": "sphere",
                "radius": shape.radius,
                "center": Point(*shape.center)
                };
        return setting;

    def __add_cylinder(self, shape):
        setting = {
                "type": "cylinder",
                "p0": Point(*shape.end_points[0]),
                "p1": Point(*shape.end_points[1]),
                "radius": shape.radius
                };
        return setting;

    def __add_cone(self, shape):
        y_dir = np.array([0.0, 1.0, 0.0]);
        v = shape.end_points[1] - shape.end_points[0];
        center = 0.5 * (shape.end_points[0] + shape.end_points[1]);
        height = norm(v);
        scale = Transform.scale(
                Vector(shape.radius, height, shape.radius));
        axis = np.cross(y_dir, v);
        axis_len = norm(axis);
        angle = degrees(atan2(axis_len, np.dot(y_dir, v)));

        if (axis_len > 1e-6):
            axis /= axis_len;
            rotate = Transform.rotate(Vector(*axis), angle);
        else:
            axis = np.array([1.0, 0.0, 0.0]);
            rotate = Transform.rotate(Vector(*axis), angle);
        translate = Transform.translate(Vector(*center));

        cone_file = self.file_resolver.resolve("cone.ply");
        cone_transform = translate * rotate * scale;
        setting = {
                "type": "ply",
                "filename": cone_file,
                "toWorld": cone_transform
                }
        return setting;

    def __get_material_setting(self, active_view):
        setting = {};
        if self.with_wire_frame:
            diffuse_color = {
                    "type": "wireframe",
                    "edgeColor": Spectrum(0.0),
                    "lineWidth": active_view.line_width,
                    "interiorColor":
                        Spectrum(active_view.vertex_colors[0][0].tolist()[0:3]),
                    };
        elif self.with_texture_coordinates:
            diffuse_color = {
                    "type": "checkerboard",
                    "color0": Spectrum([1.0, 1.0, 1.0]),
                    "color1": Spectrum([0.5, 0.5, 0.5]),
                    "flipTexCoords": False,
                    };
        else:
            if self.with_colors:
                diffuse_color = { "type": "vertexcolors" }
            else:
                diffuse_color = Spectrum(0.2);

        setting["bsdf"] = {
                "type": "roughplastic",
                "distribution": "beckmann",
                "alpha": 0.2,
                "diffuseReflectance": diffuse_color,
                };
        setting["bsdf"] = {
                "type": "twosided",
                "bsdf": setting["bsdf"]
                };
        if self.with_alpha:
            setting["bsdf"] = {
                    "type": "mask",
                    "opacity": Spectrum(active_view.alpha),
                    "bsdf": setting["bsdf"]
                    };
        if not self.with_colors and \
                not self.with_alpha and \
                not self.with_wire_frame and \
                not self.with_texture_coordinates:
            setting["subsurface"] = {
                    "type": "dipole",
                    "material": "Skimmilk",
                    "scale": 0.5
                    };
        elif self.with_texture_coordinates:
            setting["bsdf"]["bsdf"]["nonlinear"] = True;
        elif not self.with_alpha and not self.with_texture_coordinates:
            setting["subsurface"] = {
                    "type": "dipole",
                    "material": "sprite",
                    "scale": 0.5
                    };
        return setting;

    def __add_others(self):
        active_view = self.scene.active_view;
        if active_view.with_quarter:
            self.__add_quarter();
        if active_view.with_axis:
            self.__add_axis();
        if active_view.background != "n":
            self.__add_floor();

    def __add_quarter(self):
        scale = self.scene.active_view.scale;
        radius = 12.13 * scale;
        thickness = 0.875 * scale;
        face_scale = Transform.scale(Vector(radius));
        tail_offset = Transform.translate(Vector(0, 0, thickness));
        head_offset = Transform.translate(Vector(0, 0, -thickness)) *\
                Transform.scale(Vector(1.0, 1.0, -1.0));

        bbox_diag = 0.5 * norm(
                self.transformed_bbox_max - self.transformed_bbox_min);
        custom_transform = Transform.translate(Vector(
            0.5,
            self.floor_height + radius + 0.01,
            -bbox_diag - 0.01));

        head_texture = self.file_resolver.resolve("head.png");
        tail_texture = self.file_resolver.resolve("tail.png");
        side_texture = self.file_resolver.resolve("side.png");

        quarter_ring = self.plgr.create({
            "type": "cylinder",
            "p0": Point(0.0, 0.0, thickness),
            "p1": Point(0.0, 0.0, -thickness),
            "radius": radius,
            "toWorld": custom_transform,
            "bsdf": {
                "type": "bumpmap",
                "texture": {
                    "type": "scale",
                    "scale": 0.01,
                    "texture": {
                        "type": "bitmap",
                        "filename": side_texture,
                        "gamma": 1.0,
                        "uscale": 100.0,
                        },
                    },
                "bsdf": {
                    "type": "roughconductor",
                    "distribution": "ggx",
                    "alpha": 0.5,
                    "material": "Ni_palik"
                    #"diffuseReflectance": Spectrum(0.5)
                    }
                }
            });
        head = self.plgr.create({
            "type": "disk",
            "toWorld": custom_transform * head_offset * face_scale,
            "bsdf": {
                "type": "diffuse",
                "reflectance": {
                    "type": "bitmap",
                    "filename": head_texture
                    }
                }
            });
        tail = self.plgr.create({
            "type": "disk",
            "toWorld": custom_transform * tail_offset * face_scale,
            "bsdf": {
                "type": "diffuse",
                "reflectance": {
                    "type": "bitmap",
                    "filename": tail_texture
                    }
                }
            });

        self.mitsuba_scene.addChild(quarter_ring);
        self.mitsuba_scene.addChild(head);
        self.mitsuba_scene.addChild(tail);

    def __add_axis(self):
        raise NotImplementedError("Adding axis is not supported");

    def __add_floor(self):
        rotate_transform = Transform.rotate(Vector(-1, 0, 0), 90);
        scale_transform = Transform.scale(Vector(100, 100, 100));
        translate_transform = Transform.translate(
                Vector(0.0, self.floor_height, 0.0));
        total_transform = translate_transform * scale_transform\
                * rotate_transform;

        if self.scene.active_view.background == "d":
            reflectance = Spectrum(0.05);
        elif self.scene.active_view.background == "l":
            reflectance = Spectrum(0.5);
        else:
            reflectance = Spectrum(0.0);

        floor = self.plgr.create({
            "type": "rectangle",
            "toWorld": total_transform,
            "bsdf": {
                "type": "roughdiffuse",
                "diffuseReflectance": reflectance,
                "alpha": 0.5
                }
            });
        self.mitsuba_scene.addChild(floor);

    def __run_mitsuba(self):
        self.mitsuba_scene.configure();

        scheduler = Scheduler.getInstance();
        for i in range(multiprocessing.cpu_count()):
            scheduler.registerWorker(LocalWorker(i, "worker_{}".format(i)));
        scheduler.start();

        queue = RenderQueue();
        self.mitsuba_scene.setDestinationFile(self.image_name);

        job = RenderJob("render job: {}".format(
            self.image_name), self.mitsuba_scene, queue);
        job.start();

        queue.waitLeft(0);
        queue.join();

        print(Statistics.getInstance().getStats());
        scheduler.stop();

    def __save_temp_mesh(self, active_view):
        basename, ext = os.path.splitext(self.image_name);
        path, name = os.path.split(basename);
        now = datetime.datetime.now()
        stamp = now.isoformat();
        tmp_dir = tempfile.gettempdir();
        ext = ".serialized";

        tmp_mesh_name = os.path.join(tmp_dir, "{}_{}{}".format(
            name, stamp, ext));

        vertices = active_view.vertices;
        faces = active_view.faces;
        voxels = active_view.voxels;

        dim = vertices.shape[1];
        num_faces, vertex_per_face = faces.shape;
        vertices = vertices[faces.ravel(order="C")];
        colors = active_view.vertex_colors.reshape((-1, 4), order="C");
        faces = np.arange(len(vertices), dtype=int).reshape(
                (num_faces, vertex_per_face), order="C");

        mesh = pymesh.form_mesh(vertices, faces);

        if self.with_texture_coordinates:
            uvs = active_view.texture_coordinates;
        else:
            uvs = None;

        data = serialize_mesh(mesh, None, colors, uvs);
        with open(tmp_mesh_name, 'wb') as fout:
            fout.write(data);
        return tmp_mesh_name, ext;

    def __get_normalize_transform(self, active_view):
        centroid = active_view.center
        scale = active_view.scale

        normalize_transform = Transform.scale(Vector(scale, scale, scale)) *\
                Transform.translate(Vector(*(-1 * centroid)));
        return normalize_transform;

    def __get_view_transform(self, active_view):
        transform = np.eye(4);
        transform[0:3, :] = active_view.transform.reshape((3, 4), order="F");
        view_transform = Transform(Matrix4x4(transform.ravel(order="C").tolist()));
        return view_transform;

    def __get_glob_transform(self):
        glob_transform = Transform(
                Matrix4x4(self.global_transform.ravel(order="C").tolist()));
        return glob_transform;

    @property
    def with_colors(self):
        return self.scene.active_view.with_colors;

    @property
    def with_alpha(self):
        return self.scene.active_view.with_alpha;

    @property
    def with_wire_frame(self):
        return self.scene.active_view.with_wire_frame;

    @property
    def with_uniform_colors(self):
        return self.scene.active_view.with_uniform_colors;

    @property
    def with_texture_coordinates(self):
        return self.scene.active_view.with_texture_coordinates;

