class AbstractRenderer(object):
    def __init__(self, scene):
        self.__scene = scene;

    def render(self):
        raise NotImplementedError(
                "This method needs to be implemented by subclass.");

    @property
    def scene(self):
        return self.__scene;

    @scene.setter
    def scene(self, scene):
        self.__scene = scene;

