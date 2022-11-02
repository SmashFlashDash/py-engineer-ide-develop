from abc import ABCMeta, abstractmethod, ABC
# from engineers_src.Devices.functions import *
# from engineers_src.tools.tools import *


# class Cur:
#     def __init__(self):
#         self.value = None
#
#     def __get__(self, obj, cls):
#         print('getter')
#         return self.value
#
#     def __set__(self, obj, value):
#         print('setter')
#         self.value = value


class Device(ABC):
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
