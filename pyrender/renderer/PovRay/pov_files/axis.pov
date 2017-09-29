cylinder {
    <0, 0, 0>, <0.2, 0, 0>, 0.01
    pigment {rgb <1, 0, 0>}
    transform view_transform
    transform glob_transform
    translate <1.25, -0.5, -0.1>
    no_shadow
}
cylinder {
    <0, 0, 0>, <0, 0.2, 0>, 0.01
    pigment {rgb <0, 1, 0>}
    transform view_transform
    transform glob_transform
    translate <1.25, -0.5, -0.1>
    no_shadow
}
cylinder {
    <0, 0, 0>, <0, 0, 0.2>, 0.01
    pigment {rgb <0, 0, 1>}
    transform view_transform
    transform glob_transform
    translate <1.25, -0.5, -0.1>
    no_shadow
}
