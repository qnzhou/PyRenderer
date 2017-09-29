from math import pi
import numpy as np
import os.path

from .View import View
from .ViewDecorator import ViewDecorator
from pyrender.misc.quaternion import Quaternion

class CircumView(View):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "circum",
            "num_frames": number of frames,
            "view": {
                # view setting
            }
        }
        """
        view = View.create_from_setting(setting["view"]);
        if not isinstance(view, View):
            raise RuntimeError(
                    "Subview of circum view must be a simple view" +
                    " (i.e. it cannot be a circum view again)");

        name, ext = os.path.splitext(view.name);
        ori_rotation = np.copy(view.rotation);
        axis = np.array([0.0, 1.0, 0.0]);

        circum_views = [];
        num_frames = setting.get("num_frames");
        for i in range(num_frames):
            angle = float(i) / float(num_frames) * 2.0 * pi;
            rot_quaternion = Quaternion.fromAxisAngle(axis, angle);
            rot_matrix = rot_quaternion.to_matrix();

            cur_view = ViewDecorator(view);
            cur_view.rotation = np.dot(ori_rotation, rot_matrix);
            cur_view.name = "{}_{:06}{}".format(name, i, ext);
            circum_views.append(cur_view);

        return circum_views;

