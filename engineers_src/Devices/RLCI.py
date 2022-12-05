from engineers_src.Devices.Device import Device
from engineers_src.Devices.M778 import M778
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep
from datetime import datetime


class EA332(Device):
    cur = None

    @classmethod
    def on(cls, num, stop_shd=True, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('ЭА332 включен!')
        cls.log('Включить', num)
        cls.cur = num
        if num == 1:
            # sendFromJson(SCPICMD, 0x40DB, pause=1)  # ЭА332-О
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0113010000000000'), pause=1)  # ЭА332-О
        elif num == 2:
            # sendFromJson(SCPICMD, 0x41A3, pause=1)  # ЭА332-Р
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0113020000000000'), pause=1)  # ЭА332-Р
        else:
            raise Exception('Неверный параметр')
        # sendFromJson(SCPICMD, 0xE06F, AsciiHex('0x0A01 0000 0000 0000'), describe='ВКЛ ОПР РЛЦИ-В')
        if stop_shd:
            sendFromJson(SCPICMD, 0xA018)  # Остан ШД
        if ask_TMI:
            executeTMI("{04.01.beBAEA%s1}@K==\'включен\'" % num + " and "
                       + "{04.01.beBAEA%s1}@K==\'включен\'" % num + " and "
                       + doEquation('10.01.BA_FIP1', '@K', 'off') + " and "
                       + doEquation('10.01.BA_FIP2', '@K', 'off') + " and "
                       + doEquation('10.01.BA_MOD1', '@K', 'off') + " and "
                       + doEquation('10.01.BA_MOD2', '@K', 'off') + " and "
                       + doEquation('10.01.BA_PCH1', '@K', 'off') + " and "
                       + doEquation('10.01.BA_PCH2', '@K', 'off') + " and "
                       + doEquation('10.01.BA_UM1', '@K', 'off') + " and "
                       + doEquation('10.01.BA_UM2', '@K', 'off') + " and "
                       + doEquation('10.01.BA_TEMP_CARD', '@K') + " and "
                       + doEquation('10.01.BA_TEMP_CONTR', '@K') + " and "
                       + doEquation('10.01.BA_U_Ret1', '@K') + " and "
                       + doEquation('10.01.BA_U_Ret2', '@K') + " and "
                       + doEquation('10.01.BA_Sec', '@K') + " and "
                       + doEquation('10.01.BA_NUMB_LAST_UV', '@H') + " and "
                       + doEquation('10.01.BA_FRAME_COUNTER_DI', '@K') + " and "
                       + doEquation('10.01.PRD_MOD1_U_SIT1_Temp', '@K') + " and "
                       + doEquation('10.01.PRD_MOD2_U_SIT5_Temp', '@K') + " and "
                       + doEquation('10.01.PRD_KONV_U_SIT6_Temp', '@K') + " and "
                       + doEquation('10.01.BA_AFU_IMP_OX', '@K') + " and "
                       + doEquation('10.01.BA_AFU_IMP_OZ', '@K'), count=2)

    @classmethod
    def off(cls):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0xE005, AsciiHex('0113000000000000'), pause=1)  # Снять питание ЭА332
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()


class EA331(Device):
    cur = None

    @classmethod
    def on(cls, num, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('ЭА331 включен!')
        cls.log('Включить', num)
        cls.cur = num
        if num == 1:  # ЭА331-О
            # sendFromJson(SCPICMD, 0x40D9, pause=1)  # ЭА331-О
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0111010000000000'))
        elif num == 2:
            # sendFromJson(SCPICMD, 0x41A1, pause=1)  # ЭА331-Р
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0111020000000000'))
        else:
            raise Exception('Неверный параметр')
        if ask_TMI:
            executeTMI("{04.01.beKKEA%s1}@K==\'включен\'" % num + " and "
                       + "{04.01.beKKEA%s1}@K==\'включен\'" % num)

    @classmethod
    def off(cls, ask_TMI=True):
        # sendFromJson(SCPICMD, 0x43F9, pause=1)  # Снять питание ЭА331
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0xE005, AsciiHex('0111000000000000'), pause=1)  # Снять питание ЭА331
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()


class PCH(Device):
    cur = None

    @classmethod
    def on(cls, num, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('ПЧ включен!')
        cls.log('Включить', num)
        cls.cur = num
        if num == 1:
            sendFromJson(SCPICMD, 0xA000)  # Вкл ПЧ-О
        elif num == 2:
            sendFromJson(SCPICMD, 0xA001)  # Вкл ПЧ-Р
        else:
            raise Exception('Неверный параметр')
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_PCH%s' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_PCH%s_BS' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_PCH%s_P_SYNT' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_PCH%s_F_SYNT' % num, '@K', 'on'), count=1)  # Добавить 10.01.PRD_PCH1_F как в ТЕСТ 3

    @classmethod
    def off(cls, ask_TMI=True):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0xA002)  # Откл Пч
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_PCH%s' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_PCH%s_BS' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_PCH%s_P_SYNT' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_PCH%s_F_SYNT' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_PCH%s_F' % cls.cur, '@K', 'off'), count=1)
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()


class FIP(Device):
    cur = None

    @classmethod
    def on(cls, num, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('ФИП включен!')
        cls.log('Включить', num)
        if num == 1:
            sendFromJson(SCPICMD, 0xA003)  # Вкл ФИП-О
        elif num == 2:
            sendFromJson(SCPICMD, 0xA004)  # Вкл ФИП-Р
        else:
            raise Exception('Неверный параметр')
        cls.cur = num
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_FIP%s' % num, '@K', 'on') + " and " +
                       doEquation('10.01.FIP%s_BS' % num, '@K', 'on') + " and " +
                       doEquation('10.01.FIP%s_U' % num, '@K', 'on') + " and " +
                       doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                       # если не включен M778B проверяем основной
                       doEquation('10.01.FIP_M778B%s_CONNECT' % (M778.cur if M778.cur is not None else 1), '@K', 'on')
                       + " and " + doEquation('10.01.FIP_PLL1', '@K', 'on') + " and " +
                       doEquation('10.01.FIP_PLL2', '@K', 'on') + " and " +
                       doEquation('10.01.FIP_TEMP_IP', '@K') + " and " +
                       doEquation('10.01.FIP_TEMP_PLIS', '@K'), count=1)

    @classmethod
    def off(cls, ask_TMI=True):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0xA005)  # Откл Фип
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_FIP%s' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.FIP%s_BS' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.FIP%s_U' % cls.cur, '@K', 'off') + " and " +
                       # doEquation('10.01.FIP_M778B%s_CONNECT' % MB.cur, '@K', 'off') + " and " +  # не должен приходить?
                       # doEquation('10.01.FIP_M778B_INF', '@K', 'off') + " and " +  # не должен приходить?
                       doEquation('10.01.FIP_PLL1', '@K', 'off') + " and " +
                       doEquation('10.01.FIP_PLL2', '@K', 'off'), count=1)
        cls.cur = None

    @classmethod
    def get_tmi(cls, *args, **kwargs):
        cls.__unrealized__()


class MOD(Device):
    cur = None

    @classmethod
    def on(cls, num, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('МОД включен!')
        cls.log('Включить', num)
        if num == 1:
            sendFromJson(SCPICMD, 0xA006)  # Вкл МОД-О
        elif num == 2:
            sendFromJson(SCPICMD, 0xA007)  # Вкл МОД-Р
        else:
            raise Exception('Неверный параметр')
        cls.cur = num
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_MOD%s' % num, '@K', 'on') + " and " +
                       doEquation('10.01.FIP_MOD%s_CONNECT' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_MOD%s_BS' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_MOD%s_U' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_MOD_INFO', '@K', 'cele') + " and " +
                       doEquation('10.01.PRD_MOD_M', '@K', 'M4') + " and " +
                       doEquation('10.01.PRD_MOD_FIP%s_CONNECT' % FIP.cur, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_MOD_STAT_FREQ_PLL', '@K', 'on') + " and " +
                       doEquation('10.01.PRD_MOD_TEMP_CARD', '@K') + " and " +
                       doEquation('10.01.PRD_MOD_TEMP_PLIS', '@K') + " and " +
                       doEquation('10.01.PRD_PCH%s_P' % FIP.cur, '@K', 'on'), count=1)
            executeTMI(doEquation('10.01.PRD_MOD_FIP_INF', '@K', 'on') + " and " +
                       doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=10, period=5)

    @classmethod
    def off(cls, ask_TMI=True):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0xA008)  # Откл Мод
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_MOD%s' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.FIP_MOD%s_CONNECT' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_MOD%s_BS' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_MOD%s_U' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_MOD_STAT_FREQ_PLL', '@K', 'off') + " and " +
                       doEquation('10.01.PRD_PCH%s_P' % PCH.cur, '@K', 'off'), count=1)
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()


class UM(Device):
    cur = None

    @classmethod
    def on(cls, num, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('УМ включен!')
        cls.log('Включить', num)
        if num == 1:
            sendFromJson(SCPICMD, 0xA009)  # Вкл УМ-О
        elif num == 2:
            sendFromJson(SCPICMD, 0xA00A)  # Вкл УМ-Р
        else:
            raise Exception('Неверный параметр')
        cls.cur = num
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_UM%s' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_UM%s_BS' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_UM%s_P' % num, '@K', 'on') + " and " +
                       doEquation('10.01.PRD_UM%s_P_Out' % num, '@K', 'on'), count=1)

    @classmethod
    def off(cls, ask_TMI=True):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0xA00B)  # Откл УМ
        if ask_TMI:
            executeTMI(doEquation('10.01.BA_UM%s' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_UM%s_BS' % cls.cur, '@K', 'off') + " and " +
                       doEquation('10.01.PRD_UM%s_P' % cls.cur, '@K', 'off'), count=1)
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()


class RLCI(Device):
    EA332 = EA332
    EA331 = EA331
    PCH = PCH
    MOD = MOD
    FIP = FIP
    UM = UM
    uv = {
        'M1': lambda: sendFromJson(SCPICMD, 0xA00E),
        'M2': lambda: sendFromJson(SCPICMD, 0xA00F),
        'M3': lambda: sendFromJson(SCPICMD, 0xA010),
        'M4': lambda: sendFromJson(SCPICMD, 0xA011),
        'VS1': lambda: sendFromJson(SCPICMD, 0xA01A),
        'VS2': lambda: sendFromJson(SCPICMD, 0xA01B),
        'RS485-1': lambda: sendFromJson(SCPICMD, 0xA014),
        'RS485-2': lambda: sendFromJson(SCPICMD, 0xA016),
        'on imFIP': lambda: sendFromJson(SCPICMD, 0xA00C),
        'off imFIP': lambda: sendFromJson(SCPICMD, 0xA00D),
        'on imMOD': lambda: sendFromJson(SCPICMD, 0xA012, pause=5),
        'off imMOD': lambda: sendFromJson(SCPICMD, 0xA013, pause=5),
        'stop SHD': lambda: sendFromJson(SCPICMD, 0xA018),
        'start SHD': lambda: sendFromJson(SCPICMD, 0xA017)
    }
    uv_di = {
        'M1': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M1'), count=1),
        'M2': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M2'), count=1),
        'M3': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M3'), count=1),
        'M4': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M4'), count=1),
        'VS1': lambda: executeTMI(doEquation('10.01.MOD_VS', '@K', 'VS1'), count=1),
        'VS2': lambda: executeTMI(doEquation('10.01.MOD_VS', '@K', 'VS2'), count=1),
        'RS485-1': lambda: '',
        'RS485-2': lambda: '',
        'on imFIP': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'imit') + " and " +
                                       doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5),
        'off imFIP': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                                        doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5),
        'on imMOD': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                                       doEquation('10.01.PRD_MOD_INFO', '@K', 'imit') + " and " +
                                       doEquation('10.01.PRD_MOD_FIP_INF', '@K', 'off') + " and " +
                                       doEquation('10.01.FIP_M778B_INF', '@K', 'off'), count=5, period=5),
        'off imMOD': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                                        doEquation('10.01.PRD_MOD_INFO', '@K', 'cele') + " and " +
                                        doEquation('10.01.PRD_MOD_FIP_INF', '@K', 'on') + " and " +
                                        doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5),
        'stop SHD': lambda: RLCI.waitAntennaStop(period=60, toPrint=False),
        'start SHD': lambda: RLCI.isAntennaMoving()
    }

    @classmethod
    @print_start_and_end(string='РЛЦИ: вкл все блоки')
    def on(cls, num, ask_TMI=True):
        cls.log('Включить все')
        EA332.on(num, stop_shd=True, ask_TMI=ask_TMI)
        sleep(1)
        EA331.on(num, ask_TMI=ask_TMI)
        sleep(1)
        PCH.on(num, ask_TMI=ask_TMI)
        sleep(1)
        FIP.on(num, ask_TMI=ask_TMI)
        sleep(1)
        MOD.on(num, ask_TMI=ask_TMI)
        sleep(1)
        UM.on(num, ask_TMI=ask_TMI)

    @classmethod
    @print_start_and_end(string='РЛЦИ: откл все блоки')
    def off(cls, *args, **kwargs):
        """ОТКЛ ВСЕ БЛОКИ РЛЦИ"""
        cls.log('Отключить все')
        sendFromJson(SCPICMD, 0xA00B),  # Откл УМ
        cls.UM.cur = None
        sendFromJson(SCPICMD, 0xA008),  # Откл Мод
        cls.MOD.cur = None
        sendFromJson(SCPICMD, 0xA005),  # Откл Фип
        cls.FIP.cur = None
        sendFromJson(SCPICMD, 0xA002),  # Откл Пч
        cls.PCH.cur = None
        sleep(1)
        cls.EA331.off()
        cls.EA332.off()

    @classmethod
    def get_tmi(cls, *args, **kwargs):
        cls.__unrealized__()

    @classmethod
    def isAntennaMoving(cls):
        bprint('Проверка что антенна движется...')
        executeTMI("{10.01.BA_AFU_IMP_OZ}@H==@unsame@all" + " and " +
                   "{10.01.BA_AFU_IMP_OX}@H==@unsame@all", count=2, toPrint=True)

    @classmethod
    def waitAntennaStop(cls, period=0, toPrint=False, query_period=8):
        """ Ожидаие остановки антенны
        @param int period:
        @param bool toPrint:
        @param int query_period:
        """
        bprint('Ожидание остановки антенны')
        start = datetime.now()
        while True:
            res, values = controlGetEQ("{10.01.BA_AFU_IMP_OZ}@H==@same@all" + " and " +
                                       "{10.01.BA_AFU_IMP_OX}@H==@same@all", count=2, period=query_period,
                                       toPrint=toPrint)
            if res:
                bprint('Антенна остановлена')
                break
            elif (datetime.now() - start).total_seconds() >= period:
                inputG('Антенна не остановилась')
                break

    @classmethod
    def sendArrayToAntenna(cls, *sendArgs):
        cls.log('Выдать массив на антенну')
        inputG('Выдать массива на Антенну?')
        print('ВЫДАЧА МАССИВА')
        Ex.send(*sendArgs)
        sleep(5)
        sendFromJson(SCPICMD, 0xE051, AsciiHex('0x0000 0000 0200 0000'), pause=0)

    @classmethod
    @print_start_and_end(string='РЛЦИ: режим')
    def mode(cls, mode, ask_TMI=True):
        """ЗАпустить режим M1 M2 M3 M4 имитатор МОД ИМ ФИП, MOD_VS"""
        cls.log('РЕЖИМ %s' % mode)
        cls.uv[mode]()
        if ask_TMI:
            cls.uv_di[mode]()
