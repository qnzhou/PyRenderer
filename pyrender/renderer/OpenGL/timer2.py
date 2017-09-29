#!/usr/bin/env python

from time import clock;
from time import time;

class Timer:
    def __init__(self, name=""):
        t = time();
        self.__name = name;
        self.__start_time = t;
        self.__tiks = {};
        self.__hist = {};
        self.__count = {};

    def tik(self, label=""):
        t = time();
        if (label in self.__tiks):
            print("WARNING: tik() overrides previous tik() on %s. Leaking time." % label)
        elif (len(self.__tiks) != 0):
            parents = ", ".join(self.__tiks.keys())
            #print(("WARNING: nested tik(). %s will also be counted in " % label)
            #        + parents)
        self.__tiks[label] = t;

    def tok(self, label="", show=False):
        finish = time();
        start = self.__tiks.pop(label, None);
        if start is None:
            print("Error: no tik before tok for label (%s)" % label);
            return;

        period = finish - start;
        if label in self.__hist:
            self.__hist[label] += period;
            self.__count[label] += 1;
        else:
            self.__hist[label] = period;
            self.__count[label] = 1;

        if show:
            print("time(%s): %f" % (label, period));
        return period;
    
    def get_summary(self):
        if (len(self.__hist) == 0): return "";

        # Check if any part of this class uses significant amount of time.
        tol = 0.0;
        significant = [];
        for k,t in self.__hist.iteritems():
            assert(k != "");
            if t >= tol:
                significant.append(k);
        if len(significant) == 0: return;

        separator = "-"*67;
        format_string = "| {0:40.39} | {1:12.7} | {2:5} |";

        result = [];
        result.append("%s Timer summary:" % self.__name);
        result.append(separator);
        result.append(format_string.format("Label", "Time", "Count"));
        result.append(separator);

        for k in significant:
            v = self.__hist[k];
            c = self.__count[k];
            result.append(format_string.format(k, v, c));
        result.append(separator);

        if len(self.__tiks) != 0:
            result.append("======= orphans ========");
            result.append(self.__tiks.keys());

        return result;

    def summary(self):
        if (Timer.mute): return;
        if (len(self.__hist) == 0): return;
        result = self.get_summary();
        print("\n".join(result));


    ### Global variables ###
    mute = False;
