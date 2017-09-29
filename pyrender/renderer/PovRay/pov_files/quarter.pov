#include "transforms.inc"
#macro DoubleImage ( front,back )
  radial
  pigment_map {
    [ .5 front ]
    [ .5 back rotate 180*y ]
  }
#end

#declare f=pigment { image_map{ png "head.png" once} translate -.5 }
#declare b=pigment { image_map{ png "tail.png" once} translate -.5 }

#declare d = 24.26;
#declare h = 1.75;
#declare unit = 1.0;// / 1000;
#declare coin = cylinder {
    <0, 0, -h/2> / d, <0, 0, h/2> / d, 0.5
    texture { pigment { color rgb 1 } }
    texture { pigment { DoubleImage(f,b) } }
}

#declare center_vec = bbox_min - centroid;
#declare base_radius = sqrt(center_vec.x*center_vec.x + center_vec.z*center_vec.z);

cylinder {
    coin
    scale d
    translate <0.0, floor_height, 0.0>
    translate <base_radius + 0.1, 0.5 * d + 0.1, -base_radius-0.01>
    transform scale_to_fit
}

cylinder {
    coin
    scale d
    rotate <90, 0, 0>
    translate <0.0, floor_height, 0.0>
    translate <-base_radius-d*0.5, 0.5 * h + 0.1, base_radius*0.5>
    transform scale_to_fit
}

