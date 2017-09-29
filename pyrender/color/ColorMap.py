from bisect import bisect

from .Color import Color
from .PredefinedColorMaps import color_maps

class ColorMap:
    def __init__(self, color_map_name):
        self.color_map_name = color_map_name;
        assert(color_map_name in color_maps);
        colors = color_maps[color_map_name];
        self.colors = {};
        for key,val in colors.items():
            self.add_color(key, Color(*val));

    def add_color(self, value, color):
        self.colors[value] = color;

    def get_color(self, value):
        values = sorted(self.colors.keys());

        location = bisect(values, value);
        if location <= 0:
            return self.colors[values[0]];
        if location > len(values) - 1:
            return self.colors[values[-1]];

        prev_val = values[location-1];
        next_val = values[location];
        return self.__interpolate_color(value, prev_val, next_val)

    def __interpolate_color(self, val, prev_val, next_val):
        frac = (val - prev_val) / (next_val - prev_val);
        return self.colors[prev_val] * (1.0 -frac) +\
                self.colors[next_val] * frac;

    @property
    def num_key_colors(self):
        return len(self.colors);
