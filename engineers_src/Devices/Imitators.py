from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, ICCELL, AsciiHex, KPA, SOTC, SKPA, Ex, sleep
from engineers_src.Devices.Device import LOGGER

class Imitators:
    is_im_DS_on = False
    is_im_ZD_on = False

    @staticmethod
    @print_start_and_end(string='ЗД ИМИТАТОР ВКЛ')
    def on_imitators_ZD():
        LOGGER.info('%s - Включить Иммитаторы ЗД')
        is_im_ZD_on = True
        Ex.send('Ячейка ПИ', ICCELL('ВыходЗД', out=0x0F))  # Включение имитаторов ЗД
        sleep(3)

    @staticmethod
    @print_start_and_end(string='ЗД ИМИТАТОР ОТКЛ')
    def off_imitators_ZD():
        LOGGER.info('%s - Отключить Иммитаторы ЗД')
        is_im_ZD_on = False
        Ex.send('Ячейка ПИ', ICCELL('ВыходЗД', out=0x00))  # Имитаторы ЗД отключены

    @staticmethod
    @print_start_and_end(string='ДС ИМИТАТОР ВКЛ')
    def on_imitators_DS():
        LOGGER.info('%s - Включить Иммитаторы ДС')
        is_im_DS_on = True
        Ex.send('Ячейка ПИ', ICCELL('ВыходДС', out=0xFF))  # Включение имитаторов ДС
        sleep(3)

    @staticmethod
    @print_start_and_end(string='ДС ИМИТАТОР ОТКЛ')
    def off_imitators_DS():
        LOGGER.info('%s - Отключить Иммитаторы ДС')
        is_im_DS_on = False
        Ex.send('Ячейка ПИ', ICCELL('ВыходДС', out=0x00))  # Включение имитаторов ДС
