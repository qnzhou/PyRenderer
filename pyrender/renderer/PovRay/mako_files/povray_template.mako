<%def name="header()">
#version 3.6;
#include "setting.pov"
#include "color.pov"
</%def>

<%def name="global_setting()">
#declare glob_transform = transform {
    matrix <${",".join([str(v) for v in transform])}>
}
#declare bbox_min = <${"{}, {}, {}".format(*bbox_min)}>;
#declare bbox_max = <${"{}, {}, {}".format(*bbox_max)}>;
#declare centroid = bbox_min * 0.5 + bbox_max * 0.5;
#declare floor_height = ${floor_height};
</%def>

<%def name="add_lights()">
#include "lighting.pov"
</%def>

<%def name="add_camera()">
camera {
    location <${"{}, {}, {}".format(*location)}>
    sky <0, 1, 0>
    up y
    look_at <${"{}, {}, {}".format(*look_at_point)}>
    right -x*image_width/image_height
    angle ${fovx}
}
</%def>

<%def name="add_transformations()">
#declare translate_to_origin = transform {
    translate -1 * ${"<{}, {}, {}>".format(*centroid)}
}
#declare scale_to_fit = transform {
    scale ${scale}
}
#declare normalize = transform {
    translate_to_origin
    scale_to_fit
}

#declare view_transform = transform {
    matrix <${"{},{},{},{},{},{},{},{},{},{},{},{}".format(*transform)}>
}
</%def>

<%def name="add_view()">
mesh2 {
    vertex_vectors {
        ${len(vertices)},
        % for v in vertices:
            ${"<{}, {}, {}>,".format(*v)}
        % endfor
    }
    texture_list {
        ${len(colors) * 3},
        % for corner_colors in colors:
            % for c in corner_colors:
                texture{pigment{rgbt<${"{}, {}, {}".format(*c[:3])},${1.0-c[3]}>}},
            % endfor
        % endfor
    }
    face_indices {
        ${len(triangles)}
        % for i,t in enumerate(triangles):
            ${"<{}, {}, {}>".format(*t)}, ${"{}, {}, {},".format(i*3, i*3+1, i*3+2)}
        % endfor
    }

    transform view_transform
    transform normalize
    transform glob_transform
}
</%def>

<%def name="add_cylinder()">
cone {
    ${"<{}, {}, {}>".format(*end_points[0])},
    ${radii[0]},
    ${"<{}, {}, {}>".format(*end_points[1])},
    ${radii[1]}

    texture {
        pigment { rgb ${"<{}, {}, {}>".format(*color[:3])} }
    }

    transform view_transform
    transform normalize
    transform glob_transform
}
</%def>

<%def name="add_sphere()">
sphere {
    ${"<{}, {}, {}>".format(*center)}, ${radius}
    texture {
        pigment { rgb ${"<{}, {}, {}>".format(*color[:3])} }
    }

    transform view_transform
    transform normalize
    transform glob_transform
}
</%def>

<%def name="add_quarter()">
#include "quarter.pov"
</%def>

<%def name="add_floor()">
% if background == 'l':
#declare bg_color = light_bg_color;
% elif background == 'd':
#declare bg_color = dark_bg_color;
% endif
plane {
    <0, 1, 0>, floor_height
    pigment {
        color bg_color
    }
    finish {
        ambient rgb <0.2, 0.2, 0.2>
        roughness 0.1
    }
    transform scale_to_fit
}
</%def>

<%def name="add_axis()">
#include "axis.pov"
</%def>
