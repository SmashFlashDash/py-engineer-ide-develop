from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


class M778(Device):
    cur = None

    @classmethod
    @print_start_and_end(string='М778: включить')
    def on(cls, num):
        if cls.cur is not None:
            raise Exception('M778-%s уже включен!' % cls.cur)
        cls.log('Включить', num)
        cls.cur = num
        if num == 1:
            sendFromJson(SCPICMD, 0x40CB, describe='Вкл M778B1', pause=1)
        elif num == 2:
            sendFromJson(SCPICMD, 0x4193, describe='Вкл M778B2', pause=1)
        else:
            raise Exception('Номер блока только 1 и 2')

    @classmethod
    @print_start_and_end(string='М778: отключить')
    def off(cls):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0x43EB, describe='Отключить M778B', pause=1)
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()
