import numpy as np
from numpy.linalg import norm

class Camera(object):
    ## Factory methods
    @classmethod
    def create_from_setting(cls, setting):
        """ This method relies on the fact that keys in settings are consistent
        with the attribute names of this class.
        """
        instance = cls();
        instance.location = setting.get("location", instance.location);
        instance.fovy = setting.get("fovy", instance.fovy);
        instance.look_at_point = setting.get("look_at_point",
                instance.look_at_point);
        instance.up_direction = setting.get("up_direction",
                instance.up_direction);
        instance.near_plane = setting.get("near_plane", instance.near_plane);
        instance.far_plane = setting.get("far_plane", instance.far_plane);
        instance.crop_center = setting.get("crop_center", instance.crop_center);
        instance.crop_scale = setting.get("crop_scale", instance.crop_scale);
        instance.update();
        return instance;

    ## member functions
    def __init__(self):
        self.reset();

    def reset(self):
        self.location = [2.5, 1.5, 3.0];
        self.fovy = 30.37; # degrees
        #self.fovx = 38; # degrees
        self.look_at_point = [0.0, 0.0, 0.0];
        self.up_direction = [0.0, 1.0, 0.0];
        self.near_plane = 0.01
        self.far_plane = 1000000.0;
        self.crop_center = [0.5, 0.5];
        self.crop_scale = 1.0;
        self.update();

    def update(self):
        """ Compute values from set parameters.
        """
        self.focal_length = norm(
                self.location - self.look_at_point);

    def zoom(self, factor):
        camera_vector = self.location - self.look_at_point;
        self.location = self.look_at_point + camera_vector*factor;
        self.update();


    ## Getters and setters
    @property
    def location(self):
        return self.__location;

    @location.setter
    def location(self, loc):
        self.__location = np.array(loc);

    @property
    def fovy(self):
        return self.__fovy;

    @fovy.setter
    def fovy(self, val):
        self.__fovy = val;

    @property
    def look_at_point(self):
        return self.__look_at_point;

    @look_at_point.setter
    def look_at_point(self, point):
        self.__look_at_point = np.array(point);

    @property
    def up_direction(self):
        return self.__up_direction;

    @up_direction.setter
    def up_direction(self, direction):
        self.__up_direction = np.array(direction);

    @property
    def near_plane(self):
        return self.__near_plane;

    @near_plane.setter
    def near_plane(self, val):
        self.__near_plane = val;

    @property
    def far_plane(self):
        return self.__far_plane;

    @far_plane.setter
    def far_plane(self, val):
        self.__far_plane = val;

    @property
    def focal_length(self):
        return self.__focal_length;

    @focal_length.setter
    def focal_length(self, val):
        self.__focal_length = val;
