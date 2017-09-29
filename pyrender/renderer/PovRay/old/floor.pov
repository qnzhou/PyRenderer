#include "transforms.inc"
#declare center_vec = bmin - centroid;
#declare center_vec = vtransform(center_vec, reorientate);
#declare center_vec = vtransform(center_vec, glob_rotation);
plane {
    /*<0, 1, 0>, (bmin.y - centroid.y) * s - 0.01*/
    <0, 1, 0>, -1 * abs(center_vec.y) * s - 0.01
    pigment {
        //checker color White, color Black
        //color White
        //color rgb <127, 126, 124>/255
        color bg_color
        //color rgb <52, 54, 76>/255
    }

    finish {
        ambient rgb <0.2, 0.2, 0.2>
        roughness 0.1
    }
}

/*
plane {
    <1, 0, 0>, -1 * abs(center_vec.x) * s - 0.01
    pigment {
        //checker color White, color Black
        //color White
        //color rgb <127, 126, 124>/255
        color bg_color
        //color rgb <52, 54, 76>/255
    }

    finish {
        ambient rgb <0.2, 0.2, 0.2>
        roughness 0.1
    }
}
*/

/*
plane {
    <0, 0, 1>, -2
    pigment {
        //checker color White, color Black
        //color White
        //color rgb <127, 126, 124>/255
        color Grey
        //color rgb <52, 54, 76>/255
    }

    finish {
        ambient rgb <0.2, 0.2, 0.2>
        roughness 0.1
    }
}
*/
