class Light(object):
    @classmethod
    def create_from_setting(cls, setting):
        """ This method relies on the fact that keys in settings are consistent
        with the attribute names of this class.
        """
        light = cls();
        light.location = setting.get("location", light.location);
        light.ambient_color = setting.get("ambient_color", light.ambient_color);
        light.diffuse_color = setting.get("diffuse_color", light.diffuse_color);
        light.specular_color = setting.get("specular_color", light.specular_color);
        return light;

    ## Member functions
    def __init__(self):
        self.location = [0.0, 0.0, 0.0, 1.0];

        # Color in RGBA format
        self.ambient_color  = [1.0, 1.0, 1.0, 1.0];
        self.diffuse_color  = [1.0, 1.0, 1.0, 1.0];
        self.specular_color = [1.0, 1.0, 1.0, 1.0];

