#!/usr/bin/env python

import argparse
import os
import os.path
import sys

from pyrender.scene.Scene import Scene
from pyrender.scene.ClippedView import ClippedView

def render_with_opengl(scene):
    from pyrender.renderer.OpenGL.GUIFrontEnd import GUIFrontEnd
    win = GUIFrontEnd(scene);

def render_with_povray(scene):
    from pyrender.renderer.RendererFactory import RendererFactory
    renderer = RendererFactory.create_PovRay_renderer_from_scene(scene);
    renderer.render();

def render_with_mitsuba(scene):
    from pyrender.renderer.RendererFactory import RendererFactory
    renderer = RendererFactory.create_Mitsuba_renderer_from_scene(scene);
    renderer.render();

def create_scene_from_arguments(args):
    assert(args.mesh is not None);
    path, name = os.path.split(args.mesh);
    if args.scalar_field is None:
        scene = Scene.create_basic_scene(args.mesh);
    else:
        scene = Scene.create_basic_scalar_scene(
                args.mesh, args.scalar_field, args.color_map,
                args.bounds, args.discrete, args.normalize);
    view = scene.views[0];
    view.name = name;
    return scene;

def update_scene_with_arguments(scene, args):
    for view in scene.views:
        if args.background is not None:
            view.background = args.background;
        if args.transparent_bg is not None:
            view.transparent_bg = args.transparent_bg;
        if args.width is not None:
            view.width = args.width;
        if args.height is not None:
            view.height = args.height;
        if args.color is not None:
            view.color_name = args.color;
        if args.with_wire_frame:
            view.with_wire_frame = True;
        view.with_quarter = args.with_quarter;
        view.with_axis = args.with_axis;

    if args.clip is not None:
        scene.views[0] = ClippedView(scene.views[0], args.clip);
    scene.set_orientation(
            up_dir = args.up_direction,
            front_dir = args.front_direction,
            facing_camera = args.facing_camera,
            head_on = args.head_on);
    return scene;

def parse_arguments():
    parser = argparse.ArgumentParser(description="basic viewer for mesh");
    parser.add_argument("mesh", nargs='?', help="input mesh", default=None);
    parser.add_argument("-S", "--scene", "-S", help="scene file");
    parser.add_argument("--output", "-o", help="output directory", default=None);
    parser.add_argument("--renderer", choices=["opengl", "povray", "mitsuba"],
            default="povray");
    parser.add_argument("--with-quarter", "-q", help="draw reference quarters",
            action="store_true");
    parser.add_argument("--with-axis", help="draw reference axis",
            action="store_true");
    parser.add_argument("--with-wire-frame", "-w", help="draw wire frame",
            action="store_true");
    parser.add_argument("--background", "-B", help="background color",
            choices=["d", "l", "n"], default=None);
    parser.add_argument("--transparent-bg", help="use transparent background",
            action="store_true", default=None);
    parser.add_argument("--up-direction", help="Upward direction",
            choices=["X", "-X", "Y", "-Y", "Z", "-Z"], default=None);
    parser.add_argument("--front-direction", help="Front direction",
            choices=["X", "-X", "Y", "-Y", "Z", "-Z"], default=None);
    parser.add_argument("--facing-camera", action="store_true",
            help="front direction should face camera");
    parser.add_argument("--head-on", action="store_true",
            help="front direction face camera head on (mainly for 2D shapes)");
    parser.add_argument("--width", type=int, help="image width in pixels",
            default=None);
    parser.add_argument("--height", type=int, help="image height in pixels",
            default=None);
    parser.add_argument("--scalar-field", help="scalar field", default=None);
    parser.add_argument("--color-map", help="color map", default="jet");
    parser.add_argument("--color", help="uniform color name", default=None);
    parser.add_argument("--discrete", action="store_true",
            help="if scalare field is discrete");
    parser.add_argument("--bounds", nargs=2, type=float,
            help="min and max bound for scalar field", default=None);
    parser.add_argument("--normalize", action="store_true",
            help="normalize scalar field by area/volume");
    parser.add_argument("--clip", default=None,
            help="clip mesh", choices=["+X", "+Y", "+Z", "-X", "-Y", "-Z"]);
    args = parser.parse_args();
    return args;

def main():
    args = parse_arguments();
    if args.scene is not None:
        scene = Scene.create_from_file(args.scene);
    else:
        scene = create_scene_from_arguments(args);
    scene = update_scene_with_arguments(scene, args);

    if args.output is not None:
        scene.output_dir = args.output;
    for i in range(len(scene.views)):
        scene.activate_view(i);
        assert(scene.active_view == scene.views[i]);

        if args.renderer == "opengl":
            render_with_opengl(scene);
        elif args.renderer == "povray":
            render_with_povray(scene);
        elif args.renderer == "mitsuba":
            render_with_mitsuba(scene);

if __name__ == "__main__":
    main();
