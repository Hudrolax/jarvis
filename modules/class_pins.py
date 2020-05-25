from datetime import datetime


class Pins:
    def __init__(self, output, num, bcod:int, name, description='', ct=None):
        if ct is None:
            ct = []
        elif not isinstance(ct, list):
            raise Exception(f'Pins exaption: ct unexpected {type(ct)}, expected "list"')

        self._output = output
        self._num = num
        self._name = name
        self._state = False
        self._prevstate = False
        self._description = description
        self._convertible_terms = ct
        self._binds = []
        self._blocked = False
        self._last_rev_time = datetime(2005, 7, 14, 12, 30)
        if isinstance(bcod, int):
            if bcod > 100:
                bcod = 100
            if bcod < 0:
                bcod = 0
            self._bcod = bcod # Процент разряда аккумулятора для отключения пина
        else:
            raise Exception(f'Pins exaption: bcod unexpected {type(bcod)}, expected "int"')
        self._bcod_reaction = False # флаг-отметка о том, что была реакция отключения по отключению электричества на входе

    @property
    def bcod_reaction(self):
        return self._bcod_reaction

    @bcod_reaction.setter
    def bcod_reaction(self, val):
        if isinstance(val, bool):
            self._bcod_reaction = val
        else:
            raise Exception(f'Pins exaption: bcod_reaction unexpected {type(val)}, expected "int"')

    @property
    def bcod(self):
        return self._bcod

    @bcod.setter
    def bcod(self, val):
        if isinstance(val, int):
            if val > 100:
                val = 100
            if val < 0:
                val = 0
            self._bcod = val
        else:
            raise Exception(f'Pins exaption: bcod unexpected {type(val)}, expected "int"')
    @property
    def binds(self):
        return self._binds

    @property
    def last_rev_time(self):
        return self._last_rev_time

    @last_rev_time.setter
    def last_rev_time(self, val):
        if isinstance(val, datetime):
            self._last_rev_time = val
        else:
            raise Exception(f'Pins exaption: last_rev_time unexpected {type(val)}, expected "datetime"')


    @property
    def prevstate(self):
        return self._prevstate

    @prevstate.setter
    def prevstate(self, val:bool):
        if isinstance(val, bool):
            self._prevstate = val
        else:
            raise Exception(f'Pins exaption: prevstate unexpected {type(val)}, expected "bool"')

    @property
    def output(self):
        return self._output

    @property
    def num(self):
        return self._num

    @property
    def name(self):
        return self._name

    @property
    def blocked(self):
        return self._blocked

    @blocked.setter
    def blocked(self, val:bool):
        if isinstance(val, bool):
            self._blocked = val
        else:
            raise Exception(f'Pins exaption: blocked unexpected {type(val)}, expected "bool"')

    @property
    def description(self):
        return self._description

    @property
    def convertible_terms(self):
        return self._convertible_terms


    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        self._state = val

    def __str__(self):
        return self.name
