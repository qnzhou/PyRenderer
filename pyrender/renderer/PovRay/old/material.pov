#declare WSF = texture {
    //pigment { rgbt <241, 242, 207, 0> / 255 }
    pigment { color nylon_white }
    //pigment { rgbt <1.0, 1.0, 1.0, 0.0> }
    //normal { bumps 0.9 scale 2}
    /*
    normal {
        bump_map {
            png "bump.png"
            bump_size 0.4
        }
    }
    */
    finish {
        //roughness 0.1
        diffuse 0.7
        //crand 0.1
        ambient rgb <0.2, 0.2, 0.2>
    }
}

#declare Silver = texture {
    Silver2
    finish {
        diffuse 0.2
    }
}

#declare Reference = texture {
    // pigment { rgbt <255, 234, 149, 0> / 255 }
    // pigment { rgbt <255, 191, 47, 0> / 255 }
    pigment { rgbt <128, 128, 128, 0> / 255 }
    // 0.90: hex2rgb("#005AC3", alpha),
    finish {
        //roughness 0.1
        diffuse 0.7
        //crand 0.1
        ambient rgb <0.2, 0.2, 0.2>
        specular 0.75
    }
}
#declare Ghost = texture {
    // pigment { rgbt <1.0, 1.0, 1.0, 0> }
    pigment { rgbt <255, 234, 149, 0> / 255 }
    finish {
        diffuse 0.7
        ambient rgb <0.2, 0.2, 0.2>
        specular 0.75
    }
}
#declare Arrow = texture {
    pigment { rgb <1, 0, 0.12>}
    finish {
        diffuse 0.9
        // ambient rgb <0.2, 0.2, 0.2>
        specular 0.8
    }
}

#declare SemiTransparent = texture {
    pigment { rgbt <0.0, 0.1, 0.0, 1.0> }
}

#declare Test = texture {
    Spun_Brass
    /*
    normal {
        bozo
        scale 2
        /*
        slope_map {
            [0   <0, 1>]   // start at bottom and slope up
            [0.5 <1, 1>]   // halfway through reach top still climbing
            //[0.5 <1,-1>]   // abruptly slope down
            [1   <0,-1>]   // finish on down slope at bottom
        }
        */
        /*
        warp {
            turbulence <0.55, 0.0, 0.5>
        }
        */
    }
    */
    finish {
        diffuse 0.2
        specular 0.75
    }
}
