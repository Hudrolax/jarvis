from time import sleep

class Threaded_class:
    """
    Суперкласс для всех многопоточных классов
    """

    working = True
    @classmethod
    def stop(cls):
        cls.working = False

    @classmethod
    def interrupted_sleep(cls, pause):
        for k in range(10, pause*10):
            if Threaded_class.working:
                sleep(0.1)
            else:
                return