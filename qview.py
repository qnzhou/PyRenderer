#!/usr/bin/env python

import argparse
import os
import os.path
import sys

from pyrender.renderer.OpenGL.GUIFrontEnd import GUIFrontEnd
from pyrender.scene.Scene import Scene

def parse_arguments():
    parser = argparse.ArgumentParser(description="basic viewer for mesh");
    parser.add_argument("mesh", nargs='?', help="input mesh");
    parser.add_argument("-S", "--scene", "-S", help="scene file");
    args = parser.parse_args();
    return args;

def main():
    args = parse_arguments();
    if args.scene is not None:
        scene = Scene.create_from_file(args.scene);
    elif args.mesh is not None:
        scene = Scene.create_basic_scene(args.mesh);
    else:
        raise RuntimeError("Please specify either a mesh or a scene.");
    win = GUIFrontEnd(scene);

if __name__ == "__main__":
    main();
