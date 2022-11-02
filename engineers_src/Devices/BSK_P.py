from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


class BSK_P(Device):
    cur = None

    @classmethod
    @print_start_and_end(string='БСК P: включить')
    def on(cls, num):
        cls.__unrealized__()

    @classmethod
    @print_start_and_end(string='БСК P: отключить')
    def off(cls):
        cls.__unrealized__()

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()
