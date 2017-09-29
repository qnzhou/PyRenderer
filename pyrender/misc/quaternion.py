import numpy as np
from numpy.linalg import norm
from math import pi,sin,cos,atan2

class Quaternion:
    def __init__(self, quat=[1, 0, 0, 0]):
        self.__quat = np.array(quat, dtype=np.float);
        self.normalize();

    @classmethod
    def fromAxisAngle(cls, axis, angle):
        """ Crate quaternion from axis angle representation
        angle is in radian
        axis cannot have 0 length
        """
        axis = axis / norm(axis);
        quat = np.array([
            cos(angle/2),
            sin(angle/2)*axis[0],
            sin(angle/2)*axis[1],
            sin(angle/2)*axis[2]
            ]);
        return cls(quat);

    @classmethod
    def fromData(cls, v1, v2):
        """ Create the rotation to rotate v1 to v2
        Assuming v1 and v2 are unit.
        """
        c = np.dot(v1, v2)
        axis = np.cross(v1, v2)
        s = norm(axis);
        if abs(s) < 1e-12:
            # v1 is parallel to v2
            axis = np.cross(v1, [1.0, 1.0, 1.0]);
            axis /= norm(axis)
            angle = atan2(s, c);
        else:
            axis /= s;
            angle = atan2(s, c);

        quat = np.array([
            cos(angle/2),
            sin(angle/2)*axis[0],
            sin(angle/2)*axis[1],
            sin(angle/2)*axis[2]
            ])
        return cls(quat);

    @classmethod
    def fromDataBestFit(cls, v1, v2, axis):
        axis_len = norm(axis);
        if (axis_len < 1e-12):
            raise RuntimeError("Rotation axis cannot be degenerated!");
        v1 = np.array(v1);
        v2 = np.array(v2);
        axis = np.array(axis) / axis_len;

        v1 = v1 - axis * v1.dot(axis);
        v2 = v2 - axis * v2.dot(axis);

        c = np.dot(v1, v2);
        s = axis.dot(np.cross(v1, v2));
        angle = atan2(s, c);
        
        return cls.fromAxisAngle(axis, angle);

    def norm(self):
        n = norm(self.__quat);
        return n

    def normalize(self):
        n = self.norm();
        if n == 0:
            print(self.__quat);
            raise ZeroDivisionError("quaternion cannot be 0!");

        self.__quat /= n;

    def __str__(self):
        return str(self.__quat);

    def __getitem__(self, i):
        return self.__quat[i];

    def __setitem__(self, i, val):
        self.__quat[i] = val;

    def __mul__(self, other):
        r = Quaternion();
        a = self;
        b = other;
        r[0] = a[0]*b[0] - a[1]*b[1] - a[2]*b[2] - a[3]*b[3];
        r[1] = a[0]*b[1] + a[1]*b[0] + a[2]*b[3] - a[3]*b[2];
        r[2] = a[0]*b[2] - a[1]*b[3] + a[2]*b[0] + a[3]*b[1];
        r[3] = a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + a[3]*b[0];
        return r;

    def __rmul__(self, other):
        """ Multiplication does not commute.  Thus two functions.
        """
        r = Quaternion();
        a = other;
        b = self;
        r[0] = a[0]*b[0] - a[1]*b[1] - a[2]*b[2] - a[3]*b[3];
        r[1] = a[0]*b[1] + a[1]*b[0] + a[2]*b[3] - a[3]*b[2];
        r[2] = a[0]*b[2] - a[1]*b[3] + a[2]*b[0] + a[3]*b[1];
        r[3] = a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + a[3]*b[0];
        return r;

    def to_matrix(self):
        a = self.__quat;
        return np.array([
            [1 - 2*a[2]*a[2] -2*a[3]*a[3], 2*a[1]*a[2] - 2*a[3]*a[0], 2*a[1]*a[3] + 2*a[2]*a[0]],
            [2*a[1]*a[2] + 2*a[3]*a[0], 1 - 2*a[1]*a[1] -2*a[3]*a[3], 2*a[2]*a[3] - 2*a[1]*a[0]],
            [2*a[1]*a[3] - 2*a[2]*a[0], 2*a[2]*a[3] + 2*a[1]*a[0], 1 - 2*a[1]*a[1] -2*a[2]*a[2]],
            ]);

    def conjugate(self):
        """
        returns the conjugate of this quaternion, does nothing to self.
        """
        return Quaternion([
            self.__quat[0],
            -1 * self.__quat[1],
            -1 * self.__quat[2],
            -1 * self.__quat[3]
            ]);

    def rotate(self, v):
        """
        Rotate 3D vector v by this quaternion
        """
        v = Quaternion([0, v[0], v[1], v[2]]);
        r = self * v * self.conjugate();
        return r[1:4];



def test():
    angle = pi/2
    a = Quaternion([cos(angle/2), sin(angle/2), 0, 0]);

    b = a*a*a*a;
    print("Should be identity.");
    print(b.to_matrix());

    c = Quaternion.fromData([1, 0, 0], [0, 1, 0]);
    print("Should be [0, 1, 0]");
    print(np.dot(c.to_matrix() , np.array([1, 0, 0])));

    print("Should be [0, 1, 0]");
    print(c.rotate([1, 0, 0]));


if __name__ == "__main__":
    test();
