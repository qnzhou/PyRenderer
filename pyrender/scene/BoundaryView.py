from .ViewDecorator import ViewDecorator
from .View import View
from .WireView import WireView
import pymesh
import tempfile
import datetime
import os.path
import logging

class BoundaryView(View):
    @classmethod
    def create_from_setting(cls, setting):
        """ Syntax:
        {
            "type": "boundary",
            "mesh": mesh_file,
            "color": color_name,
            "radius": radius
        }
        """
        mesh = pymesh.load_mesh(setting["mesh"]);
        vertices = mesh.vertices;
        bd_edges = mesh.boundary_edges;
        vertices, bd_edges, __ = pymesh.remove_isolated_vertices_raw(vertices, bd_edges);
        wires = pymesh.wires.WireNetwork();
        if len(bd_edges) > 0:
            wires.load(vertices, bd_edges);
        else:
            logger = logging.getLogger(__name__);
            logger.warning("Mesh ({}) contains no boundary.".format(
                setting["mesh"]));

        tmp_dir = tempfile.gettempdir();
        stamp = datetime.datetime.now().isoformat();
        wire_file = os.path.join(tmp_dir, "{}.wire".format(stamp));
        wires.write_to_file(wire_file);

        wire_setting = {
                "type": "wire_network",
                "wire_network": wire_file,
                "color": setting.get("color", None),
                "radius": setting.get("radius", 0.1),
                "bbox": mesh.bbox,
                };
        return WireView.create_from_setting(wire_setting);

