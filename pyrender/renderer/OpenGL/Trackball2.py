from math import sqrt, asin
import numpy as np
from numpy.linalg import norm

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    raise ImportError("PyOpenGL is not installed properly");

from pyrender.misc.quaternion import Quaternion
from pyrender.scene.Scene import Scene

class Trackball:
    AXIS_DIRECTION = {
            "x" : [ 1.0,  0.0,  0.0],
            "-x": [-1.0,  0.0,  0.0],
            "y" : [ 0.0,  1.0,  0.0],
            "-y": [ 0.0, -1.0,  0.0],
            "z" : [ 0.0,  0.0,  1.0],
            "-z": [ 0.0,  0.0, -1.0],
            }
    def __init__(self, scene):
        self.__radius = 0.8;
        self.__scene = scene;

        camera = self.__scene.active_camera;
        camera_location = np.array(camera.location);
        camera_location /= norm(camera_location);
        self.__camera_direction = camera_location;
        self.__front_direction = [0.0, 0.0, 1.0];
        self.__quaternion = Quaternion();

        self.__initialize_camera_to_world_matrix();
        self.__initialize_world_to_camera_matrix();

    def reset(self):
        self.__quaternion = Quaternion();

    def drag(self, old_x, old_y, new_x, new_y):
        if (old_x == new_x and old_y == new_y): return;

        viewport = glGetIntegerv(GL_VIEWPORT);
        window_width  = viewport[2];
        window_height = viewport[3];

        old_x = (old_x*2.0 - window_width)  / window_width;
        new_x = (new_x*2.0 - window_width)  / window_width;

        # Note the input x,y are in window coordinates, where origin is at the
        # upper left corner.  Thus, need to do y = height - y to make the origin
        # located at the lower left corner.
        old_y = (window_height - old_y*2.0) / window_height;
        new_y = (window_height - new_y*2.0) / window_height;

        # project onto arc ball.
        p1 = self.__project_on_sphere(old_x, old_y);
        p2 = self.__project_on_sphere(new_x, new_y);
        p1 = p1 / norm(p1);
        p2 = p2 / norm(p2);

        # Compute rotation matrix to rotate p1 to p2.
        d_quaternion = Quaternion.fromData(p1, p2);
        self.__quaternion = d_quaternion * self.__quaternion;
        self.__quaternion.normalize();

    def get_rotation_matrix(self):
        rotation = self.__camera_to_world*\
                self.__quaternion *\
                self.__world_to_camera;
        R = rotation.to_matrix();
        return R;
        #return [R[0,0], R[1,0], R[2,0], 0.0,
        #        R[0,1], R[1,1], R[2,1], 0.0,
        #        R[0,2], R[1,2], R[2,2], 0.0,
        #           0.0,    0.0,    0.0, 1.0 ];

    def set_front_direction(self, direction, face_on=False):
        direction = direction.lower();
        from_dir = self.__front_direction;
        to_dir = self.__camera_direction;
        camera_up_dir = self.__scene.active_camera.up_direction;

        if direction in self.AXIS_DIRECTION:
            from_dir = self.AXIS_DIRECTION[direction];
        else:
            return;

        # Look for the direction closest to camera's up dir.
        guessed_up_dir = None;
        guessed_up_projection = -1.0;
        base_direction = direction.replace("-", "");
        for name,d in self.AXIS_DIRECTION.items():
            if base_direction == name or "-" + base_direction == name:
                continue;
            cur_dir = self.__quaternion.rotate(d);
            proj = np.dot(camera_up_dir, cur_dir);
            if proj > guessed_up_projection:
                guessed_up_dir = d;
                guessed_up_projection = proj;

        # Note to self:
        # self.__quaternion tracks rotation in camera coordinates. Thus global
        # coordinates such as the ones in self.AXIS_DIRECTION needs to be
        # transformed by self.__world_to_camera.rotate(...) before using them to
        # compute rotations.
        guessed_up_dir = self.__world_to_camera.rotate(guessed_up_dir);
        camera_up_dir = self.__world_to_camera.rotate(camera_up_dir);
        up_rot = Quaternion.fromData(guessed_up_dir, camera_up_dir);

        from_dir = self.__world_to_camera.rotate(from_dir);
        from_dir = up_rot.rotate(from_dir);
        to_dir = self.__world_to_camera.rotate(to_dir);

        if not face_on:
            to_dir = to_dir - np.dot(to_dir, camera_up_dir) * np.array(camera_up_dir);
            to_dir = to_dir / norm(to_dir)

        front_rot = Quaternion.fromData(from_dir, to_dir);
        self.__quaternion = front_rot * up_rot;


    def __initialize_world_to_camera_matrix(self):
        self.__world_to_camera = Quaternion.fromData(
                self.__camera_direction,
                self.__front_direction);
        self.__world_to_camera.normalize();

    def __initialize_camera_to_world_matrix(self):
        self.__camera_to_world = Quaternion.fromData(
                self.__front_direction,
                self.__camera_direction);
        self.__camera_to_world.normalize();

    def __project_on_sphere(self, x, y):
        d = sqrt(x*x + y*y);
        r = self.__radius;
        if (d < r * 0.70710678118654752440):    # Inside sphere
            z = sqrt(r*r - d*d)
        else:                                   # On hyperbola
            t = r / 1.41421356237309504880
            z = t*t / d
        return np.array([x, y, z]);

