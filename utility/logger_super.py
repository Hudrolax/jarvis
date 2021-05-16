import logging


class LoggerSuper():
    """
    Cуперкласс для всех логгированных классов.
    """
    logger = logging.getLogger('LoggerMeta')
    logger.setLevel(logging.INFO)

    @classmethod
    def set_debug(cls):
        cls.logger.setLevel(logging.DEBUG)

    @classmethod
    def set_info(cls):
        cls.logger.setLevel(logging.INFO)

    @classmethod
    def set_warning(cls):
        cls.logger.setLevel(logging.WARNING)