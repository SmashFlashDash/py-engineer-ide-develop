from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


class BCK(Device):
    cur = None
    clc_pause = 10
    down_pause = 20

    @classmethod
    def on(cls):
        cls.__unrealized__()

    @classmethod
    def off(cls):
        cls.__unrealized__()

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()

    @classmethod
    @print_start_and_end(string='БЦК: очистить накопитель')
    def clc_BCK(cls):
        """Очистить весь накопитель БЦК"""
        sendFromJson(SCPICMD, 0xE107, describe='Ждать %s сек' % cls.clc_pause, pause=cls.clc_pause)

    @classmethod
    @print_start_and_end(string='БЦК: сбросить накопитель')
    def downBCK(cls):
        """Сброс ДИ с БЦК в БА КИС-Р всего накопителя"""
        sendFromJson(SCPICMD, 0xE060, describe='Ждать %s сек' % cls.down_pause, pause=cls.down_pause)
