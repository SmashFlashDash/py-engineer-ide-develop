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

    def __init__(self):
        """Наследущии классы работают без создания обьектов"""
        raise Exception('Запрещено создавать обьект')

    @classmethod
    def log(cls, *args):
        if not LOGGER.hasHandlers():
            return
        if len(args) > 0:
            cls.LOGGER.info('%s - %s' % (cls.__name__, ' '.join(str(x) for x in args)))
        else:
            cls.LOGGER.info('%s - ...' % cls.__name__)

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
