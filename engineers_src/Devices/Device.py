from abc import ABCMeta, abstractmethod, ABC
import logging
import logging.handlers
# from engineers_src.Devices.functions import *
# from engineers_src.tools.tools import *
from engineers_src.tools.tools import Ex


old_factory = logging.getLogRecordFactory()
def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.bshv = 'БШВ: ' + str(Ex.get('ТМИ', '00.00.BSHV', 'КАЛИБР ТЕКУЩ'))
    return record
logging.setLogRecordFactory(record_factory)

LOGGER = logging.getLogger('DeviceLogger')
LOGGER.setLevel(logging.DEBUG)
# file_logger = logging.StreamHandler()
# file_logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(bshv)s  - %(message)s'))
# LOGGER.addHandler(file_logger)


class Device(ABC):
    LOGGER = LOGGER

    # def __init__(self):
    #     self.__cur = None
    #
    # @property
    # def cur(self):
    #     """геттер номера запущенного блока устройства"""
    #     print('getter')
    #     return self.__cur
    #
    # @cur.setter
    # def cur(self, value):
    #     """сеттер номера запущенного блока устройства"""
    #     print('setter')
    #     self.__cur = value

    # TODO: сделать синглтон, создавать экземпляр в __init__ и перезаписать на те же имена
    #  тогда будет работать @property
    def __init__(self):
        """Наследущии классы работают без создания обьектов"""
        raise Exception('Запрещено создавать обьект')

    @classmethod
    def log(cls, msg, msg2=None):
        if msg2 is not None:
            cls.LOGGER.info('%s - %s %s' % (cls.__name__, msg, msg2))
        else:
            cls.LOGGER.info('%s - %s' % (cls.__name__, msg))

    @classmethod
    def __unrealized__(cls):
        raise Exception('Нереализованный метод')

    @classmethod
    @abstractmethod
    def on(cls, *args, **kwargs):
        """включение блока устройства"""
        pass

    @classmethod
    @abstractmethod
    def off(cls, *args, **kwargs):
        """выключение блока устройства"""
        pass

    @classmethod
    @abstractmethod
    def get_tmi(cls, *args, **kwargs):
        """опрос ди блока устройства"""
        pass

# TODO:
#  желательно опросить КСО при выключенном КИС
#  нужно опросить ТМИ КСО и очтистить БЦК, выключить КИС
#  спустя минуту включить КИС, сбросить БЦК, подождать когда сбросится
#  опросить БД ДИ КСО в режиме интервал
#  исходя из этих значений можно оценить магнитную обстановку в БЭК
#  и сделать условия проверки для КСО
#  -----идет к тому что сделать мини рокот
#  МНИИ БД в скрипте
#  делаем словарь ключей в значения пишем словарь или класс
#  в класс пишм значения проверять ли тми
#  значение для проверки
#  при вызове обьекта, проверяем ТМИ


class DiStatus:
    pass