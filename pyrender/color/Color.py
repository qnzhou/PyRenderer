import numpy as np
class Color(object):

    @classmethod
    def from_hex(cls, hex_color, alpha=1.0):
        c = hex_color.lstrip("#");
        assert(len(c) == 6);
        return Color(
                int(c[0:2], 16) / 255.0,
                int(c[2:4], 16) / 255.0,
                int(c[4:6], 16) / 255.0,
                alpha);

    def __init__(self, red=0.0, green=0.0, blue=0.0, alpha=1.0):
        self.color = np.array([red, green, blue, alpha]);

    def __getitem__(self, i):
        return self.color[i];

    def __add__(self, other):
        c = self.color + other.color;
        return Color(*c);

    def __mul__(self, scale):
        c = self.color * scale;
        return Color(*c);

    def __rmul__(self, scale):
        return self.__mul__(scale);

    def __eq__(self, other):
        return np.all(self.color == other.color);

    def __ne__(self, other):
        return not(self == other);

    def __str__(self):
        return "Color [{}, {}, {}, {}]".format(
                self.color[0], self.color[1], self.color[2], self.color[3]);

    @property
    def red(self):
        return self.color[0];

    @property
    def green(self):
        return self.color[1];

    @property
    def blue(self):
        return self.color[2];

    @property
    def alpha(self):
        return self.color[3];


## Predefined colors
color_table = {
        "light_background" : Color.from_hex("FFFFFF"),
        "dark_background"  : Color.from_hex("332E30"),
        "nylon_white"      : Color.from_hex("FFFEEB"),
        "gray"             : Color.from_hex("CCCCCC"),
        "dark_gray"        : Color.from_hex("333333"),
        "black"            : Color.from_hex("000000"),
        "white"            : Color.from_hex("FFFFFF"),
        "red"              : Color.from_hex("FF0000"),
        "green"            : Color.from_hex("00FF00"),
        "#light_green"      : Color.from_hex("92C9B9"),
        "blue"             : Color.from_hex("0000FF"),
        "gold"             : Color.from_hex("AB9A10"),
        "yellow"           : Color.from_hex("EFE442"),
        "blue"             : Color.from_hex("57B4E9"),
        "orange"           : Color.from_hex("C05D23"),
        "light_orange"     : Color.from_hex("F4B25A"),
        "cheese_bubble"    : Color.from_hex("EDE695"),
        "cheese"           : Color.from_hex("FFFCCE"),
        "light_green"      : Color.from_hex("6BBE46"),
        "light_red"        : Color.from_hex("F3756D"),
        "light_blue"       : Color.from_hex("5DB4E5"),
        }


