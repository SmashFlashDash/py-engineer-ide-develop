from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


class BCK(Device):
    cur = None

    @classmethod
    def on(cls):
        cls.__unrealized__()

    @classmethod
    def off(cls):
        cls.__unrealized__()

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()

    @staticmethod
    @print_start_and_end(string='БЦК: очистить накопитель')
    def clc_BCK():
        """Очистить весь накопитель БЦК"""
        sendFromJson(SCPICMD, 0xE107, describe='Ждать 10 сек', pause=10)

    @staticmethod
    @print_start_and_end(string='БЦК: сбросить накопитель')
    def downBCK():
        """Сброс ДИ с БЦК в БА КИС-Р всего накопителя"""
        sendFromJson(SCPICMD, 0xE060, describe='Ждать 30 сек', pause=20)
