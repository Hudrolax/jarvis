class Rectangle:
    def __init__(self, x_min, x_max, y_min, y_max):
        self._x_min = x_min
        self._x_max = x_max
        self._y_min = y_min
        self._y_max = y_max
        self._x = 90
        self._y = 90

    @staticmethod
    def check_values(val, min, max):
        if val > max:
            return max
        elif val < min:
            return min
        else:
            return val

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = self.check_values(val, self._x_min, self._x_max)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = self.check_values(val, self._y_min, self._y_max)