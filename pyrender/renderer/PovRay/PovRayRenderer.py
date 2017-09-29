import inspect
from mako.template import Template
from math import tan, atan2, degrees, radians
import numpy as np
import os.path
from subprocess import check_call

from pyrender.renderer.AbstractRenderer import AbstractRenderer
from pyrender.primitives.Primitive import Cylinder, Cone, Sphere

class PovRayRenderer(AbstractRenderer):
    def __init__(self, scene):
        super(PovRayRenderer, self).__init__(scene);

    def render(self):
        self.__initialize();
        self.__add_header();
        self.__add_lights();
        self.__add_active_camera();
        self.__add_transformations();
        self.__add_active_view();
        self.__add_primitives();
        self.__add_others();
        self.__run_povray();

    def __initialize(self):
        self.__initialize_povray_setting();
        self.__initialize_image_setting();
        self.__initialize_geometry_setting();

    def __initialize_povray_setting(self):
        self.povray_setting = "";

        self.pov_module_path = os.path.dirname(
                inspect.getfile(PovRayRenderer));
        template_file = os.path.join(self.pov_module_path,
                "mako_files/povray_template.mako");
        self.pov_template = Template(filename=template_file);

    def __initialize_image_setting(self):
        active_view = self.scene.active_view;
        self.output_dir = self.scene.output_dir;
        self.image_name = active_view.name;
        self.image_width = float(active_view.width);
        self.image_height = float(active_view.height);

        active_camera = self.scene.active_camera;
        active_camera.fovx = degrees(atan2(self.image_width,
                self.image_height / tan(radians(active_camera.fovy * 0.5))
                )) * 2.0;

    def __initialize_geometry_setting(self):
        active_view = self.scene.active_view;
        if len(active_view.vertices) > 0:
            self.global_transform = self.scene.global_transform[:3,:].ravel(order="F");
            global_rotation = self.scene.global_transform[:3, :3];

            vertices = active_view.vertices;
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
            self.global_transform = self.scene.global_transform[:3,:].ravel(order="F");

    def __add_header(self):
        header_setting = self.pov_template.get_def("header").render();
        global_setting = self.pov_template.get_def("global_setting").render(
                transform = self.global_transform,
                bbox_min = self.transformed_bbox_min,
                bbox_max = self.transformed_bbox_max,
                floor_height = self.floor_height);
        self.povray_setting += header_setting;
        self.povray_setting += global_setting;

    def __add_lights(self):
        #TODO: load lights from scene.
        light_setting = self.pov_template.get_def("add_lights").render();
        self.povray_setting += light_setting;

    def __add_active_camera(self):
        camera = self.scene.active_camera;
        camera_setting = self.pov_template.get_def("add_camera").render(
                location = camera.location,
                up_direction = camera.up_direction,
                look_at_point = camera.look_at_point,
                fovx = camera.fovx,
                width = self.image_width,
                height = self.image_height
                );
        self.povray_setting += camera_setting;

    def __add_transformations(self):
        active_view = self.scene.active_view;
        transformation_setting = \
                self.pov_template.get_def("add_transformations").render(
                        centroid = active_view.center,
                        scale = active_view.scale,
                        transform = active_view.transform.ravel(order="F")
                        );
        self.povray_setting += transformation_setting;

    def __add_active_view(self):
        active_view = self.scene.active_view;
        if len(active_view.vertices) == 0: return;
        view_setting = self.pov_template.get_def("add_view").render(
                vertices = active_view.vertices,
                triangles = active_view.faces,
                colors = active_view.vertex_colors
                );
        self.povray_setting += view_setting;

    def __add_primitives(self):
        primitives = self.scene.active_view.primitives;
        for shape in primitives:
            if isinstance(shape, Cylinder):
                cylinder_setting = \
                        self.pov_template.get_def("add_cylinder").render(
                                end_points = shape.end_points,
                                radii = [shape.radius, shape.radius],
                                color = shape.color);
                self.povray_setting += cylinder_setting;
            elif isinstance(shape, Cone):
                cone_setting = \
                        self.pov_template.get_def("add_cylinder").render(
                                end_points = shape.end_points,
                                radii = [shape.radius, 0.0],
                                color = shape.color);
                self.povray_setting += cone_setting;
            elif isinstance(shape, Sphere):
                sphere_setting =\
                        self.pov_template.get_def("add_sphere").render(
                                center = shape.center,
                                radius = shape.radius,
                                color = shape.color);
                self.povray_setting += sphere_setting;

    def __add_others(self):
        active_view = self.scene.active_view;
        if active_view.with_quarter:
            self.__add_quarter();
        if active_view.with_axis:
            self.__add_axis();
        if active_view.background != "n":
            self.__add_floor();

    def __add_quarter(self):
        quarter_setting = self.pov_template.get_def("add_quarter").render();
        self.povray_setting += quarter_setting;

    def __add_floor(self):
        floor_setting = self.pov_template.get_def("add_floor").render(
                background = self.scene.active_view.background);
        self.povray_setting += floor_setting;

    def __add_axis(self):
        axis_setting = self.pov_template.get_def("add_axis").render();
        self.povray_setting += axis_setting;

    def __run_povray(self):
        basename, ext = os.path.splitext(self.image_name);
        pov_file = os.path.join(self.output_dir, basename + ".pov");
        img_file = os.path.join(self.output_dir, basename + ".png");
        with open(pov_file, 'w') as fout:
            fout.write(self.povray_setting);

        options = "+A -D -V +WL0 +W{} -H{} -L{} +O{}".format(
                self.image_width, self.image_height,
                os.path.join(self.pov_module_path, "pov_files"),
                img_file);
        if self.scene.active_view.transparent_bg:
            options += " +ua";
        command = "povray {} {}".format(options, pov_file);
        print(command);
        check_call(command.split());

