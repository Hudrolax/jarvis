from datetime import datetime


class Pins:
    def __init__(self, output, num, _bcod, name, description='', ct=None):
        if ct is None:
            ct = []
        self.output = output
        self.num = num
        self.name = name
        self.state = False
        self.prevstate = False
        self.description = description
        self.ConvertibleTerms = ct
        self.binds = []
        self.blocked = False
        self.LastRevTime = datetime(2005, 7, 14, 12, 30)
        self.bcod = _bcod
        self.bcod_reaction = False

    def __str__(self):
        return self.name