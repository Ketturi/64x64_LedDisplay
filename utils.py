from math import sin, cos, radians

class point():
    """
    A little point class for storing xy pairs,
    + and - are overloaded for the class
    """
    x = 0
    y = 0
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return point(x, y)
    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return point(x, y)
    def __str__(self):
        return '[x:{0}, y:{1}]'.format(self.x,self.y)
    def offsetByVector(self, angle, length):
        """
        Create point from an origin and a vector
        The vector consistes of a length and an angle in radians
        """
        x = int(cos(angle) * length) + self.x
        y = int(sin(angle) * length) + self.y
        return point(x, y)

clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
hex2rgb = lambda hex: (tuple(int(hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)))