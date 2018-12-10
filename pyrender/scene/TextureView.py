import numpy as np
import numpy.linalg
import pymesh

from pyrender.color.Color import color_table, Color
from pyrender.color.ColorMap import ColorMap
from pyrender.primitives.Primitive import Cylinder, Cone, Sphere

from .View import View
from .ViewDecorator import ViewDecorator

class TextureView(ViewDecorator):
    @classmethod
    def create_from_setting(cls, setting):
        """ syntax:
        {
            "type": "texture",
            "uv_attribute": "corner_texture",
            "uv_scale": float,
            "uv_offset": [0.0, 0.0],
            "with_boundary": bool,
            "boundary_color": color_name,
            "boundary_radius": radius
            "view": {
                ...
            }
        }
        """
        nested_view = View.create_from_setting(setting["view"]);
        instance = TextureView(nested_view);
        instance.uv_scale = setting.get("uv_scale", 1.0);
        instance.uv_offset = setting.get("uv_offset", [0.0, 0.0]);
        instance.uv_attribute = setting.get("uv_attribute", "corner_texture");
        instance.with_boundary = setting.get("with_boundary", True);
        instance.boundary_radius = setting.get("boundary_radius", 0.002);
        instance.boundary_color = setting.get("boundary_color", None);
        if instance.with_boundary:
            instance.extract_texture_boundary();
        return instance;

    def __init__(self, nested_view):
        super(TextureView, self).__init__(nested_view);

    def extract_texture_boundary(self):
        if self.boundary_color is None:
            color = color_table["black"];
        elif self.boundary_color == "random":
            color = ColorMap("RdYlBu").get_color(
                    random.choice([0.1, 0.3, 0.5, 0.7, 0.9]));
        else:
            assert(self.boundary_color in color_table);
            color = color_table[self.boundary_color];

        radius = self.boundary_radius / self.scale;
        cutted_mesh = pymesh.cut_mesh(self.mesh);
        bd_edges = cutted_mesh.boundary_edges;
        vertices = cutted_mesh.vertices;
        for e in bd_edges:
            v0 = vertices[e[0]];
            v1 = vertices[e[1]];
            assert(np.all(np.isfinite(v0)));
            assert(np.all(np.isfinite(v1)));
            if numpy.linalg.norm(v0 - v1) <= radius:
                continue;
            cylinder = Cylinder(v0, v1, radius);
            cylinder.color = color;
            self.primitives.append(cylinder);

        bd_vertices = np.unique(bd_edges.ravel());
        for v in bd_vertices:
            ball = Sphere(vertices[v,:], radius);
            ball.color = color;
            self.primitives.append(ball);

    @property
    def with_texture_coordinates(self):
        return True;

    @property
    def texture_coordinates(self):
        assert(self.mesh.has_attribute(self.uv_attribute));
        uv = self.mesh.get_attribute(self.uv_attribute).reshape((-1, 2)).copy();
        uv += np.array(self.uv_offset);
        uv *= self.uv_scale;
        return uv;
