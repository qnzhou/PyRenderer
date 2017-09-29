light_source {
    <3,6,4>
    //<2.5, 1.5, 3>
    color White
    //shadowless
    area_light <5, 0, 0>, <0, 0, 5>, 10, 10
    adaptive 2
    jitter
    spotlight 
    point_at <0, 0, 0>
    radius 50
    falloff 40
}

light_source {
    <4, 0, -1>
    color Grey
    shadowless
}

light_source {
    <-4, -1, -4>
    color Grey
    shadowless
}
