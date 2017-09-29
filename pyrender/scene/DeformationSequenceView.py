import copy
from math import pi
import numpy as np
import os.path

from .View import View
from .ViewDecorator import ViewDecorator
from pyrender.misc.quaternion import Quaternion

class DeformationSequenceView(View):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "deformation_sequence",
            "num_frames": number of frames,
            "vector": vector_field,
            "deform_magnitude": scalar,
            "deform_factor": [min_factor, max_factor],
            "name": base_file_name,
            "view": {
                # view setting
            }
        }
        """
        deformation_setting = {
                "type": "deformation",
                "vector": setting["vector"],
                "deform_magnitude": setting.get("deform_magnitude", None),
                "view": setting["view"]
                }
        num_frames = setting["num_frames"];
        name = setting.get("name", "deformation_sequence.png");
        basename,ext = os.path.splitext(name);
        factor_range = setting.get("deform_factor", [-1.0, 1.0]);

        views = [];
        factors = np.linspace(factor_range[0], factor_range[1], num_frames);
        for i,factor in enumerate(factors):
            cur_setting = copy.deepcopy(deformation_setting);
            cur_setting["name"] = "{}_{:06}{}".format(basename, i, ext);
            cur_setting["deform_factor"] = factor;
            views.append(View.create_from_setting(cur_setting));

        return views;
