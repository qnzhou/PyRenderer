import numpy as np
from numpy.linalg import norm

from .View import View
from .ViewDecorator import ViewDecorator

class ClippedView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "clipped",
            "center": [x, y, z],
            "radius": float,
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = ClippedView(nested_view,
                np.array(setting["center"]),
                setting["radius"]);
        return instance;

    def __init__(self, nested_view, center, radius):
        super(ClippedView, self).__init__(nested_view);
        self.center = center;
        self.scale = 1.0 / radius;
