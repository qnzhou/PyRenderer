import sys
from time import clock,sleep
import numpy as np
from numpy.linalg import norm, inv
from math import pi, tan, atan
import os
import os.path
import warnings

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    raise ImportError("PyOpenGL is not installed properly");

from pyrender.renderer.AbstractRenderer import AbstractRenderer
from pyrender.color.Color import Color, color_table
from pyrender.primitives.Primitive import Cylinder, Cone, Sphere
from pyrender.scene.Scene import Scene
from pyrender.misc.quaternion import Quaternion

from .Console import Console
from .Logger import Logger
from .Trackball2 import Trackball
from .timer2 import Timer

class OpenGLRenderer(AbstractRenderer):
    LIGHT_NAMES = [
            GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3,
            GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7,
            ];

    DEFAULT_BG_COLOR = list(color_table["dark_background"])
    DEFAULT_FG_COLOR = list(color_table["nylon_white"])

    def __init__(self, scene):
        super(self.__class__, self).__init__(scene);
        self.__restore_default();
        self.__init_glut_window();
        self.__init_opengl();
        self.__init_status_states();
        self.__init_log_states();
        self.__init_console();
        self.__init_axis_states();
        self.__init_display_states();
        self.__setup_scene();
        self.__timer = Timer("OpenGL Timer");

    def render(self):
        glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT );

        self.__push_matrices();

        # Draw view
        self.__draw_mesh();
        self.__draw_primitives();
        if not self.__render_mesh_only:
            self.__draw_axis();
            self.__show_log();
            self.__show_status();
            self.__show_console();

        self.__pop_matrices();

        # Refresh screen
        glutSwapBuffers();

        self.__abort_on_error();
        self.__update_frame_count();

    def idle(self):
        glutPostRedisplay();

    def mouse(self, button, state, x, y):
        if state == GLUT_UP:
            self.__mouse_button = -1;
            self.__point_cloud = False;
        elif state == GLUT_DOWN:
            self.__mouse_button = button;
            self.__point_cloud = True;
        self.__mouse_location = [x,y];

        #buttons = ["left", "middle", "right"];
        #states = ["pressed", "released"];
        #self.__logger.log("mouse: {} button {} at <{}, {}>".format(
        #    buttons[button], states[state], x, y));
        glutPostRedisplay();

    def keyboard(self, key, x, y):
        # Capture special key [TAB].
        if ord(key) == 9:
            self.__render_mesh_only = not self.__render_mesh_only;
        elif not self.__render_mesh_only:
            self.__console.keyboard(key);
        glutPostRedisplay();

    def passivemotion(self, x, y):
        self.__mouse_location = [x,y]
        glutPostRedisplay();

    def motion(self, x, y):
        if self.__mouse_button == GLUT_LEFT_BUTTON:
            # Rotation
            self.__trackball.drag(self.__mouse_location[0],
                    self.__mouse_location[1], x, y);
        elif self.__mouse_button == GLUT_RIGHT_BUTTON:
            # Translation
            curr_p = np.array(self.__window_to_world(x,y));
            prev_p = np.array(self.__window_to_world(
                self.__mouse_location[0],
                self.__mouse_location[1]));

            camera = self.scene.active_camera
            focal_length = camera.focal_length;
            img_plane_depth = camera.near_plane;
            displacement = (curr_p - prev_p) * focal_length / img_plane_depth;
            self.__translation += displacement;
        elif self.__mouse_button == GLUT_MIDDLE_BUTTON:
            # Zoom
            dy = y - self.__mouse_location[1];
            viewport = glGetIntegerv(GL_VIEWPORT);
            window_height = viewport[3];
            zoom_factor = 1.0 - float(dy) / float(window_height);
            zoom_factor = np.clip(zoom_factor, 0.0, 2.0);

            camera = self.scene.active_camera;
            camera.zoom(zoom_factor);
        self.__mouse_location = [x,y];
        glutPostRedisplay();

    def __abort_on_error(self):
        err_code = glGetError();
        err_text = {
                GL_NO_ERROR: "no error",
                GL_INVALID_ENUM: "invalid enum value",
                GL_INVALID_VALUE: "numerical values out of range",
                GL_INVALID_OPERATION: "specified operation not allowed",
                GL_INVALID_FRAMEBUFFER_OPERATION: "framebuffer object not complete",
                GL_OUT_OF_MEMORY: "out of memory",
                GL_STACK_UNDERFLOW: "stack underflow",
                GL_STACK_OVERFLOW: "stack overflow",
                };
        if err_code != GL_NO_ERROR:
            #assert(error_code in err_text);
            #raise RuntimeError("OpenGL Error: {}".format(err_text[err_code]));
            self.__abort(-1);

    def __abort(self, r_val=0):
        sys.exit(r_val);

    def __restore_default(self):
        self.__render_mesh_only = False;
        self.__window_size = [800, 600];
        self.__trackball = Trackball(self.scene);
        self.__translation = np.zeros(3, dtype=float);
        self.scene.active_camera.reset();

    def __init_glut_window(self):
        glutInitWindowSize(self.__window_size[0], self.__window_size[1]);
        glutInitDisplayMode( GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH );
        glutInit();
        glutCreateWindow("QView");

    def __init_opengl(self):
        glClearColor(*self.DEFAULT_BG_COLOR);

        # Line anti-aliasing
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glEnable(GL_LINE_SMOOTH);
        glEnable(GL_POINT_SMOOTH)

    def __init_status_states(self):
        self.__frames = 0;
        self.__fps = 0;
        self.__mouse_location = [0, 0];
        self.__mouse_button = -1;
        self.__prev_tic = clock();
        self.__status_location = [5, 2];
        self.__status_line_height = 15;
        #self.__status_font = GLUT_BITMAP_HELVETICA_12;
        self.__status_font = GLUT_BITMAP_8_BY_13;
        self.__status_color = [1.0, 1.0, 0.0, 0.5];

    def __init_log_states(self):
        self.__logger = Logger();
        self.__log_location = [-250, 2];
        self.__log_line_height = 15;
        self.__log_font = GLUT_BITMAP_HELVETICA_12;
        self.__log_color = [1.0, 1.0, 1.0, 0.5];

    def __init_console(self):
        self.__console = Console("Press [TAB] to toggle visibility");
        self.__console_location = [2, -10];
        self.__console_line_height = -15;
        self.__console_font = GLUT_BITMAP_8_BY_13;
        self.__console_color = [1.0, 1.0, 1.0, 0.5];

        self.__register_commands();

    def __register_commands(self):
        self.__console.register_cmd("quit", self.__abort);
        self.__console.register_cmd("reset", self.__restore_default,\
                "reset display");
        self.__console.register_cmd("wire", self.__toggle_wire_frame,\
                "toggle wire frame");
        self.__console.register_cmd("flat", self.__toggle_flat_shading,\
                "toggle flat shading");
        self.__console.register_cmd("show", self.__show_fields,\
                "show views, meshes (e.g. show views)");
        self.__console.register_cmd("set", self.__set_fields,\
                "set view or mesh (e.g. set view 0)");
        self.__console.register_cmd("render", self.__render_scene,\
                "render scene (e.g. render tmp.png povray)");
        self.__console.register_cmd("print", self.__print,
                "print information (e.g. transform)");
        self.__console.register_cmd("timing", self.__print_timing,\
                "show timing");

    def __init_axis_states(self):
        self.__axis_screen_size = 50;
        self.__axis_screen_spacing = 5;

    def __init_display_states(self):
        self.__wire_frame = False;
        self.__point_cloud = False;
        self.__flat_shading = True;

    def __setup_scene(self):
        self.__set_lights();
        self.__extract_data_from_view();
        self.__initialize_buffers();

    def __set_lights(self):
        lights = self.scene.lights;
        for i,light in enumerate(lights):
            light_name = self.__class__.LIGHT_NAMES[i];
            glLightfv(light_name, GL_POSITION,  light.location);
            glLightfv(light_name, GL_AMBIENT,   light.ambient_color);
            glLightfv(light_name, GL_DIFFUSE,   light.diffuse_color);
            glLightfv(light_name, GL_SPECULAR,  light.specular_color);
            glEnable(light_name);
        glEnable(GL_NORMALIZE); 
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE);

    def __extract_data_from_view(self):
        view = self.scene.active_view;
        self.__vertex_per_face  = view.mesh.vertex_per_face;
        self.__vertex_per_voxel = view.mesh.vertex_per_voxel;
        need_duplicate = self.__flat_shading;

        self.__vertices = view.vertices[view.faces.ravel(order="C")];
        self.__vertex_colors = view.vertex_colors;
        self.__faces = view.faces;

        if self.__flat_shading:
            self.__normals = view.face_normals;
        else:
            self.__normals = view.vertex_normals;

        self.__num_vertices = len(self.__vertices);
        self.__num_faces = len(self.__faces);

        if self.__vertices.itemsize == 8:
            self.__gl_float_data_type = GL_DOUBLE
        elif self.__vertices.itemsize == 4:
            self.__gl_float_data_type = GL_FLOAT
        else:
            raise RuntimeError("Unknown OpenGL type with {} bytes."
                    .format(self.__vertices.itemsize));

        if self.__vertex_per_face == 3:
            self.primitive_type = GL_TRIANGLES;
        elif self.__vertex_per_face == 4:
            self.primitive_type = GL_QUADS;
        else:
            raise NotImplementedError(
                    "Unknow face type consisting of {} vertices"
                    .format(self.__vertex_per_face));

    def __initialize_buffers(self):
        self.__initialize_vertex_buffer();
        if self.__normals is not None:
            self.__initialize_vertex_normal_buffer();
        if self.__vertex_colors is not None:
            self.__initialize_vertex_color_buffer();
        self.__initialize_element_index_buffer();

    def __initialize_vertex_buffer(self):
        #TODO: Error checking
        self.__vertex_buffer = glGenBuffers(1);
        glBindBuffer(GL_ARRAY_BUFFER, self.__vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, self.__vertices, GL_STATIC_DRAW);
        #TODO: remove hard coded 3
        glVertexPointer(3, self.__gl_float_data_type, 0, None);

    def __initialize_vertex_normal_buffer(self, sign=1):
        self.__normal_buffer = glGenBuffers(1);
        glBindBuffer(GL_ARRAY_BUFFER, self.__normal_buffer);
        glBufferData(GL_ARRAY_BUFFER, self.__normals * sign, GL_STATIC_DRAW);
        glNormalPointer(self.__gl_float_data_type, 0, None);

    def __initialize_vertex_color_buffer(self):
        self.__color_buffer = glGenBuffers(1);
        glBindBuffer(GL_ARRAY_BUFFER, self.__color_buffer);
        glBufferData(GL_ARRAY_BUFFER, self.__vertex_colors, GL_STATIC_DRAW);
        glColorPointer(4, self.__gl_float_data_type, 0, None);

    def __initialize_element_index_buffer(self):
        self.__index_buffer = glGenBuffers(1);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.__index_buffer);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.__faces, GL_STATIC_DRAW);

    def __push_matrices(self):
        self.__push_projection_matrix();
        self.__push_camera_view_matrix();
        self.__push_modelview_matrix();

    def __push_projection_matrix(self):
        camera = self.scene.active_camera;

        glMatrixMode(GL_PROJECTION);
        glPushMatrix();
        glLoadIdentity();
        viewport = glGetIntegerv(GL_VIEWPORT);
        aspect = float(viewport[2]) / float(viewport[3]);
        fovy = camera.fovy;

        gluPerspective(fovy, aspect, camera.near_plane, camera.far_plane);

    def __push_camera_view_matrix(self):
        camera = self.scene.active_camera;

        glMatrixMode(GL_MODELVIEW);
        glPushMatrix();
        glLoadIdentity();
        eye    = camera.location;
        center = camera.look_at_point;
        up     = camera.up_direction;
        gluLookAt(
                eye[0], eye[1], eye[2],
                center[0], center[1], center[2],
                up[0], up[1], up[2]);

    def __push_modelview_matrix(self):
        glMatrixMode(GL_MODELVIEW);
        glPushMatrix();

        # OpenGL view transformation
        view_transform = self.__trackball.get_rotation_matrix();
        view_translation = self.__translation;
        view_4x4_transform =\
                self.__convert_to_homogeneous_matrix(view_transform);
        glTranslated(*view_translation);
        glMultMatrixd(view_4x4_transform);

        # Normalize
        view_scale = self.scene.active_view.scale;
        view_center = self.scene.active_view.center;
        glScaled(view_scale, view_scale, view_scale);
        glTranslated(*(-1 * view_center));

        # Model transformation specified by View object
        model_transform = self.scene.active_view.rotation;
        model_translation = self.scene.active_view.translation;
        model_4x4_transform =\
                self.__convert_to_homogeneous_matrix(model_transform);
        glTranslated(*model_translation);
        glMultMatrixd(model_4x4_transform);

    def __pop_matrices(self):
        self.__pop_projection_matrix();
        self.__pop_camera_view_matrix();
        self.__pop_modelview_matrix();

    def __pop_projection_matrix(self):
        glMatrixMode(GL_PROJECTION);
        glPopMatrix();

    def __pop_camera_view_matrix(self):
        glMatrixMode(GL_MODELVIEW);
        glPopMatrix();

    def __pop_modelview_matrix(self):
        glMatrixMode(GL_MODELVIEW);
        glPopMatrix();

    def __show_log(self):
        self.__timer.tik("show log");
        viewport = glGetIntegerv(GL_VIEWPORT);
        [x_pos, y_pos] = self.__log_location;
        if x_pos < 0: x_pos += viewport[2];
        if y_pos < 0: y_pos += viewport[3];

        glColor(self.__log_color);
        log = self.__logger.get_log();
        for line in log:
            self.__draw_text(line, x_pos, y_pos, self.__log_font);
            y_pos += self.__log_line_height;
        self.__timer.tok("show log");

    def __show_console(self):
        viewport = glGetIntegerv(GL_VIEWPORT);
        [x_pos, y_pos] = self.__console_location;
        if x_pos < 0: x_pos += viewport[2];
        if y_pos < 0: y_pos += viewport[3];

        glColor(self.__console_color);
        text = self.__console.get_text();
        for line in text:
            self.__draw_text(line, x_pos, y_pos, self.__console_font);
            y_pos += self.__console_line_height;

    def __show_status(self):
        self.__timer.tik("show status");
        glColor(self.__status_color);
        viewport = glGetIntegerv(GL_VIEWPORT);
        view = self.scene.active_view;
        lines = [];

        [text_pos_x, text_pos_y] = self.__status_location;
        if text_pos_x < 0: text_pos_x += viewport[2];
        if text_pos_y < 0: text_pos_y += viewport[3];

        text = "pos: <{}, {}>".format(
                self.__mouse_location[0],
                self.__mouse_location[1]);
        lines.append(text);

        #text = "fps: {}".format(self.__fps);
        #lines.append(text);

        lines.append("#V: {}".format(view.mesh.num_voxels));
        lines.append("#f: {}".format(view.mesh.num_faces));
        lines.append("#v: {}".format(view.mesh.num_vertices));

        for line in lines:
            self.__draw_text(line, text_pos_x, text_pos_y, self.__status_font);
            text_pos_y += self.__status_line_height;
        self.__timer.tok("show status");

    def __draw_text(self, text, x, y, font = GLUT_BITMAP_HELVETICA_12):
        glWindowPos2i(int(x), int(y));
        for ch in text:
            glutBitmapCharacter(font, ord(ch));

    def __draw_mesh(self):
        self.__timer.tik("draw mesh");
        self.__timer.tik("prepare draw");
        view = self.scene.active_view;

        glMatrixMode(GL_MODELVIEW);
        glPushMatrix();

        glPushAttrib(GL_ALL_ATTRIB_BITS);
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS);

        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST);

        glEnableClientState(GL_VERTEX_ARRAY);
        if self.__normals is not None:
            glEnableClientState(GL_NORMAL_ARRAY);
        if self.__vertex_colors is not None:
            glEnableClientState(GL_COLOR_ARRAY);
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE)
            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0]);
        else:
            glDisable(GL_COLOR_MATERIAL)
            glColor(*self.DEFAULT_FG_COLOR);

        glEnableClientState(GL_INDEX_ARRAY);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.__index_buffer);
        self.__timer.tok("prepare draw");

        if self.__point_cloud:
            self.__timer.tik("draw points")
            # I could draw points by setting glPolygonMode, but this way is
            # faster.
            glPointSize(1.5);
            glDrawArrays(GL_POINTS,        # draw points
                    0,                     # start from index 0
                    self.__num_vertices);              # number of points to draw
            self.__timer.tok("draw points")
        else:
            self.__timer.tik("draw");
            if self.__wire_frame:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);

            # In flat shading, normal is asigned to each vertex of each
            # face.  Thus, vertices was duplicated for each face, and
            # drawing is done with glDrawArray.
            glDrawArrays(self.primitive_type, # draw primitive
                    0,                        # start from index 0
                    self.__num_vertices);     # for this many indices
            self.__timer.tok("draw");

        glPopAttrib();
        glPopClientAttrib();
        glPopMatrix();
        self.__timer.tok("draw mesh");

    def __draw_primitives(self):
        self.__timer.tik("draw primitives");

        glPushAttrib(GL_ALL_ATTRIB_BITS);
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS);

        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST);
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0]);

        self.__draw_sphere();
        self.__draw_cylinders();
        self.__draw_cone();

        glPopAttrib();
        glPopClientAttrib();
        self.__timer.tok("draw primitives");

    def __draw_sphere(self):
        glMatrixMode(GL_MODELVIEW);

        quadric = gluNewQuadric();
        gluQuadricNormals(quadric, GLU_SMOOTH);
        for shape in self.scene.active_view.primitives:
            if not isinstance(shape, Sphere): continue;
            glPushMatrix();
            glTranslated(*shape.center);

            glColor3d(*shape.color[:3]);
            gluSphere(quadric, shape.radius, 8, 16);

            glPopMatrix();
        gluDeleteQuadric(quadric);

    def __draw_cylinders(self):
        z_dir = np.array([0.0, 0.0, 1.0]);
        glMatrixMode(GL_MODELVIEW);

        quadric = gluNewQuadric();
        gluQuadricNormals(quadric, GLU_SMOOTH);
        for shape in self.scene.active_view.primitives:
            if not isinstance(shape, Cylinder): continue;
            glPushMatrix();

            v = shape.end_points[1] - shape.end_points[0];
            height = norm(v);
            rotation = Quaternion.fromData(z_dir, v);

            glTranslated(*shape.end_points[0]);
            mat = self.__convert_to_homogeneous_matrix(rotation.to_matrix());
            glMultMatrixd(mat);

            glColor3d(*shape.color[:3]);
            gluCylinder(quadric, shape.radius, shape.radius, height, 8, 1);

            glPopMatrix();
        gluDeleteQuadric(quadric);

    def __draw_cone(self):
        z_dir = np.array([0.0, 0.0, 1.0]);
        glMatrixMode(GL_MODELVIEW);

        quadric = gluNewQuadric();
        gluQuadricNormals(quadric, GLU_SMOOTH);
        for shape in self.scene.active_view.primitives:
            if not isinstance(shape, Cone): continue;
            glPushMatrix();

            v = shape.end_points[1] - shape.end_points[0];
            height = norm(v);
            rotation = Quaternion.fromData(z_dir, v);

            glTranslated(*shape.end_points[0]);
            mat = self.__convert_to_homogeneous_matrix(rotation.to_matrix());
            glMultMatrixd(mat);

            glColor3d(*shape.color[:3]);
            gluCylinder(quadric, shape.radius, 0.0, height, 8, 1);

            glPopMatrix();
        gluDeleteQuadric(quadric);

    def __draw_axis(self):
        self.__timer.tik("draw axis");
        screen_size = self.__axis_screen_size;
        screen_spacing = self.__axis_screen_spacing;
        view_port = glGetIntegerv(GL_VIEWPORT);
        glViewport(
                view_port[2] - screen_size - screen_spacing,
                screen_spacing,
                screen_size,
                screen_size);
        inv_scale = 1.0 / self.scene.active_view.scale;

        glMatrixMode(GL_MODELVIEW);
        glPushMatrix();
        glScaled(inv_scale, inv_scale, inv_scale);
        glTranslated(*(-1 * self.__translation));

        glPushAttrib(GL_ALL_ATTRIB_BITS);

        glLineWidth(1.5);
        glBegin(GL_LINES);
        glColor3d (1.0, 0.0, 0.0)
        glVertex3d(0.0, 0.0, 0.0);
        glVertex3d(1.0, 0.0, 0.0);

        glColor3d (0.0, 1.0, 0.0)
        glVertex3d(0.0, 0.0, 0.0);
        glVertex3d(0.0, 1.0, 0.0);

        glColor3d (0.0, 0.0, 1.0)
        glVertex3d(0.0, 0.0, 0.0);
        glVertex3d(0.0, 0.0, 1.0);
        glEnd();

        glPopAttrib();
        glPopMatrix();
        glViewport(*view_port);
        self.__timer.tok("draw axis");

    def __window_to_world(self, x, y):
        """ Window coordinate to world coordinate.
        """
        (modelview_matrix, projection_matrix, view_port) = \
                self.__get_opengl_matrices(use_model_view=False);
        z = self.scene.active_camera.near_plane;
        window_height = view_port[3]
        world_coor = gluUnProject(x, window_height - y, z,
                modelview_matrix, projection_matrix, view_port);
        return list(world_coor);

    def __window_to_model(self, x, y):
        """ Window coordinate to model coordinate.
        """
        (modelview_matrix, projection_matrix, view_port) = \
                self.__get_opengl_matrices();
        z = self.scene.active_camera.near_plane;
        window_height = view_port[3]
        world_coor = gluUnProject(x, window_height - y, z,
                modelview_matrix, projection_matrix, view_port);
        return list(world_coor);

    def __world_to_window(self, x, y, z):
        """ World coordinate to window coordinate.
        """
        (modelview_matrix, projection_matrix, view_port) = \
                self.__get_opengl_matrices(use_model_view=False);
        window_coor = gluProject(x, y, z,
                modelview_matrix, projection_matrix, view_port);
        # make origin location to be top left corner in window coordinate.
        window_height = view_port[3]
        window_coor[2] = window_height - window_coor[2];
        return list(window_coor);

    def __model_to_window(self, x, y, z):
        """ Model coordinate to window coordinate.
        """
        (modelview_matrix, projection_matrix, view_port) = \
                self.__get_opengl_matrices();
        window_coor = gluProject(x, y, z,
                modelview_matrix, projection_matrix, view_port);
        # make origin location to be top left corner in window coordinate.
        window_height = view_port[3]
        window_coor[2] = window_height - window_coor[2];
        return list(window_coor);

    def __get_opengl_matrices(self,
            use_projection=True,
            use_camera_view=True,
            use_model_view=True):
        """ Retrieve projection, modelview and viewport from OpenGL
        if use_projection, retrieve the matrices after camera projection.
        if use_modelview, retrieve the matrices after camera transformation.
        if use_model, retrieve the matrices after model rotation/translation.
        """
        if use_projection : self.__push_projection_matrix();
        if use_camera_view: self.__push_camera_view_matrix();
        if use_model_view : self.__push_modelview_matrix();

        modelview_matrix  = glGetDoublev(GL_MODELVIEW_MATRIX);
        projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX);
        view_port = glGetIntegerv(GL_VIEWPORT);

        if use_model_view : self.__pop_modelview_matrix();
        if use_camera_view: self.__pop_camera_view_matrix();
        if use_projection : self.__pop_projection_matrix();

        return (modelview_matrix, projection_matrix, view_port);

    def __update_frame_count(self):
        self.__frames += 1;
        cur_tic = clock();
        prev_tic = self.__prev_tic;
        time_gap = cur_tic - prev_tic;
        if time_gap > 1.0:
            self.__fps = int(self.__frames / time_gap);
            self.__frames = 0;
            self.__prev_tic = cur_tic;

    def __convert_to_homogeneous_matrix(self, matrix):
        M = np.ravel(matrix, order="F");
        assert(len(M) == 9);

        return [M[0], M[1], M[2], 0.0,
                M[3], M[4], M[5], 0.0,
                M[6], M[7], M[8], 0.0,
                 0.0,  0.0,  0.0, 1.0];

    def __update_view_transform(self):
        normalize_translation = -self.scene.active_view.center;
        normalize_scale = self.scene.active_view.scale;

        view_rotation = self.__trackball.get_rotation_matrix();
        view_translation = self.__translation;

        model_rotation = self.scene.active_view.rotation;
        model_translation = self.scene.active_view.translation;

        net_rotation = np.dot(view_rotation, model_rotation);
        net_translation = np.dot(view_rotation,
                model_translation + normalize_translation) + \
                        view_translation / normalize_scale - \
                        normalize_translation;

        self.scene.active_view.rotation = net_rotation;
        self.scene.active_view.translation = net_translation;
        self.__trackball.reset();
        self.__translation = np.zeros(3, dtype=float);

    ### Console commands ###

    def __toggle_wire_frame(self):
        self.__wire_frame = not self.__wire_frame;

    def __toggle_flat_shading(self):
        self.__flat_shading = not self.__flat_shading;
        self.__setup_scene();

    def __show_fields(self, name=None):
        """
        usage: show name
        e.g. show views

        name must be view[s]
        """
        if name is None:
            return "usage: show [view|mesh]"

        result = [];
        if name[:4] == "view":
            for i,view in enumerate(self.scene.views):
                if view.name == self.scene.active_view.name:
                    result.append("->{:2} {}".format(i, view.name));
                else:
                    result.append("  {:2} {}".format(i, view.name));
        else:
            result.append("error: {} unknown".format(name));

        return result;

    def __set_fields(self, name=None, val=None, *args):
        """
        usage: set [name] [val]
        e.g. set view 0   # use the view at index 0
             set front -y # make -y direction face camera

        to set view:
            you can see the available views with show command.
            e.g. show views
        to set front:
            value must be X,-X,Y,-Y,Z,-Z
        """
        if name is None:
            return "usage: set [view|mesh] [0-9]";
        if name[:4] == "view":
            val = int(val);
            if val < 0 or val >= len(self.scene.views):
                return "index {} out of range".format(val);
            self.scene.activate_view(val);
            self.__setup_scene();
        elif name[:5] == "front":
            self.__trackball.set_front_direction(val);
        else:
            return "error: unknow field \"{}\"".format(name);

    def __render_scene(self, img_name=None, renderer="povray"):
        """
        usage: render [img_name] [renderer_name]
        e.g. render tmp.png         # by povray used by default
             render tmp.png povray  # or specify povray explicitly
        """
        self.__update_view_transform();
        if img_name is not None:
            self.scene.active_view.name = img_name;

        if renderer == "povray":
            from pyrender.renderer.RendererFactory import RendererFactory
            renderer = RendererFactory.create_PovRay_renderer_from_scene(self.scene);
            renderer.render();
        elif renderer == "mitsuba":
            from pyrender.renderer.RendererFactory import RendererFactory
            renderer = RendererFactory.create_Mitsuba_renderer_from_scene(self.scene);
            renderer.render();
        else:
            raise NotImplementedError("render {} is not supported yet"\
                    .format(renderer));

    def __print(self, name):
        """
        usage: print [variable_name]
        valid variable names are:
            transform, rotation, translation
        """
        if (name == "transform"):
            r = self.__print_transform();
        elif (name == "rotation"):
            r = self.__print_rotation();
        elif (name == "translation"):
            r = self.__print_translation();
        else:
            return "unknown name: {}".format(name);
        print(r);
        return r;

    def __print_transform(self):
        self.__update_view_transform();
        result = "{}".format(self.scene.active_view.transform);
        return result;

    def __print_rotation(self):
        self.__update_view_transform();
        result = "{}".format(self.scene.active_view.rotation);
        return result;

    def __print_translation(self):
        self.__update_view_transform();
        result = "{}".format(self.scene.active_view.translation);
        return result;

    def __print_timing(self):
        result = self.__timer.get_summary();
        return result;


