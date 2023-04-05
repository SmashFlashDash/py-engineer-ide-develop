from ui.commandsSearcherCMD import DataListUV
from time import sleep
from abc import abstractmethod, ABC
import logging
import logging.handlers
from collections import OrderedDict
from datetime import datetime, timedelta
import traceback
from lib.tabulate.tabulate import tabulate
# # DEBUG
# from time import sleep as sleep2
# import time
# time.sleep = lambda *args: sleep2(0)
# sleep = lambda *args: sleep2(0)


def DI_CYPHER(syst_num, pa, di_name):
    """сгенерировать шифр ДИ"""
    return '%02d' % int(syst_num) + '.' + '%02d' % int(pa) + '.' + di_name


def UV_CYPHER(uv_number, numdev):
    """сгенерировать номер УВ"""
    return uv_number + 0x1000 * numdev


# Упорядоченный словарь УВ АСН (и КСО)
UV = {
    # КСО
    "ON_KSO": 0x5009, "OFF_KSO": 0x53F1, "STOP_OF_START_CYCLE": 0x0081, "ON_FKP1_ASN1": 0x4005,
    "ON_FKP1_ASN2": 0x4195, "OFF_FKP1_ASN": 0x43ED,
    # АСН
    "DI_2_FKP_1": UV_CYPHER(0x0A0, 14), "CLEAR_ALL": UV_CYPHER(0x107, 14),
    "OBTS_SYNC": UV_CYPHER(0x10, 14), "DOWN_ALL": UV_CYPHER(0x60, 14), "DOWN_SS": UV_CYPHER(0x61, 14), "DOWN_DI": UV_CYPHER(0x62, 14),
    "DOWN_STOP": UV_CYPHER(0x6E, 14),
    "TLM2_ASN1": UV_CYPHER(0x150, 14), "TLM3_ASN1": UV_CYPHER(0x151, 14), "TLM4_ASN1": UV_CYPHER(0x152, 14),
    "TLM5_ASN1": UV_CYPHER(0x153, 14), "TLM6_ASN1": UV_CYPHER(0x154, 14), "TLM7_ASN1": UV_CYPHER(0x155, 14),
    "TLM8_ASN1": UV_CYPHER(0x156, 14), "TLM9_ASN1": UV_CYPHER(0x157, 14), "TLM10_ASN1": UV_CYPHER(0x158, 14),
    "TLM11_ASN1": UV_CYPHER(0x159, 14), "TLM12_ASN1": UV_CYPHER(0x15A, 14), "TLM13_ASN1": UV_CYPHER(0x15B, 14),
    "TLM2_ASN2": UV_CYPHER(0x160, 14), "TLM3_ASN2": UV_CYPHER(0x161, 14), "TLM4_ASN2": UV_CYPHER(0x162, 14),
    "TLM5_ASN2": UV_CYPHER(0x163, 14), "TLM6_ASN2": UV_CYPHER(0x164, 14), "TLM7_ASN2": UV_CYPHER(0x165, 14),
    "TLM8_ASN2": UV_CYPHER(0x166, 14), "TLM9_ASN2": UV_CYPHER(0x167, 14), "TLM10_ASN2": UV_CYPHER(0x168, 14),
    "TLM11_ASN2": UV_CYPHER(0x169, 14), "TLM12_ASN2": UV_CYPHER(0x16A, 14), "TLM13_ASN2": UV_CYPHER(0x16B, 14),
    "CLEAR_ABS_SCHD": UV_CYPHER(0x207, 14), "CLEAR_REL_SCHD": UV_CYPHER(0x208, 14), "EXCH_ON_ASN1": UV_CYPHER(0x219, 14),
    "EXCH_OFF_ASN1": UV_CYPHER(0x21A, 14), "POWER_ON_ASN1": UV_CYPHER(0x21B, 14), "POWER_OFF_ASN1": UV_CYPHER(0x21C, 14),
    "POWER_EXCH_ON_ASN1": UV_CYPHER(0x21D, 14), "POWER_EXCH_OFF_ASN1": UV_CYPHER(0x21E, 14), "MODE_ASN1": UV_CYPHER(0x21F, 14),
    "SET_TASKS_ASN1": UV_CYPHER(0x220, 14), "STORAGE_ASN1": UV_CYPHER(0x221, 14), "OUT_SINGLE_ASN1": UV_CYPHER(0x222, 14),
    "OUT_PERIOD_ASN1": UV_CYPHER(0x223, 14), "OUT_ALM_ASN1": UV_CYPHER(0x224, 14), "OUT_MV_ASN1": UV_CYPHER(0x225, 14),
    "MV_OFFS_ASN1": UV_CYPHER(0x226, 14), "TS_OFFS_ASN1": UV_CYPHER(0x227, 14), "MV_PERIOD_ASN1": UV_CYPHER(0x228, 14),
    "RESTART_MON_ASN1": UV_CYPHER(0x229, 14), "RESTART_SPO_ASN1": UV_CYPHER(0x22A, 14), "NAV_CONFIG_ASN1": UV_CYPHER(0x22B, 14),
    "OBTS_SET_FLAG_ASN1": UV_CYPHER(0x22C, 14), "OBTS_CLEAR_FLAG_ASN1": UV_CYPHER(0x22D, 14), "DUMP_ASN1": UV_CYPHER(0x22E, 14),
    "SET_MASK_ASN1": UV_CYPHER(0x22F, 14), "EXCH_ON_ASN2": UV_CYPHER(0x230, 14), "EXCH_OFF_ASN2": UV_CYPHER(0x231, 14),
    "POWER_ON_ASN2": UV_CYPHER(0x232, 14), "POWER_OFF_ASN2": UV_CYPHER(0x233, 14), "POWER_EXCH_ON_ASN2": UV_CYPHER(0x234, 14),
    "POWER_EXCH_OFF_ASN2": UV_CYPHER(0x235, 14), "MODE_ASN2": UV_CYPHER(0x236, 14), "SET_TASKS_ASN2": UV_CYPHER(0x237, 14),
    "STORAGE_ASN2": UV_CYPHER(0x239, 14), "OUT_SINGLE_ASN2": UV_CYPHER(0x239, 14), "OUT_PERIOD_ASN2": UV_CYPHER(0x23A, 14),
    "OUT_ALM_ASN2": UV_CYPHER(0x23B, 14), "OUT_MV_ASN2": UV_CYPHER(0x23C, 14), "MV_OFFS_ASN2": UV_CYPHER(0x23D, 14),
    "TS_OFFS_ASN2": UV_CYPHER(0x23E, 14), "MV_PERIOD_ASN2": UV_CYPHER(0x23F, 14), "RESTART_MON_ASN2": UV_CYPHER(0x240, 14),
    "RESTART_SPO_ASN2": UV_CYPHER(0x241, 14), "NAV_CONFIG_ASN2": UV_CYPHER(0x242, 14), "OBTS_SET_FLAG_ASN2": UV_CYPHER(0x243, 14),
    "OBTS_CLEAR_FLAG_ASN2": UV_CYPHER(0x244, 14), "DUMP_ASN2": UV_CYPHER(0x245, 14), "SET_MASK_ASN2": UV_CYPHER(0x246, 14),
    # РЛЦИ
    "": ""
}

# Упорядоченный словарь номеров БА на шине МКПД1
BA_num = OrderedDict(
    [("KSO", '00'), ("KPDU", '01'), ("KIR", '02'), ("KSP", '03'), ("FKP1", '04'), ("FKP2", '05'), ("MROD1", '06'),
     ("MROD2", '07'), ("RLTSIv", '10'), ("ASN1", '11'), ("ASN2", '12'), ("BTSK", '14')])


class DIstorage:
    """
    Класс содержащий параметры телеметрии с коммутацией устрйоств
    используется в АИП в функции doEquation для составлния выражения для controlGetEq
    :param commutations: содержит значения комутируемых блоков, и шифры на которые влияют
    """
    commutations = {
        'M778B': [False, ('10.01.FIP_M778B1_CONNECT',
                          '10.01.FIP_M778B2_CONNECT', '10.01.FIP_M778B_INF')]}
    DI = None

    @staticmethod
    def reset():
        """DI в исходный вариант если DI был изменен извне"""
        DIstorage.DI = DIstorage._reset()

    @staticmethod
    def _reset():
        """Содержит исходный словарь телеметрии"""
        return {
        # KIS
        '15.00.NBARL': {'@K': None, '@H': None},  # ПРОВЕРКА НОМЕРА АКТИВНОГО КОМПЛЕКТА БАРЛ
        '15.00.NRK1\\2': {'@K': None, '@H': None},  # последний РК выданный на БРАЛ
        '15.00.NRK2\\2': {'@K': None, '@H': None},  # последний РК выданный на БРАЛ
        '15.00.NRK3\\4': {'@K': None, '@H': None},  # последний РК выданный на БРАЛ
        '15.00.NRK4\\4': {'@K': None, '@H': None},  # последний РК выданный на БРАЛ
        '15.00.TOTKLPRD1\\2': {'@K': None, '@H': None},  # ТАЙМЕРА ОТКЛ ПРД (0 – ВЫКЛ)
        '15.00.TOTKLPRD2\\2': {'@K': None, '@H': None},  # ТАЙМЕРА ОТКЛ ПРД (0 – ВЫКЛ)
        '15.00.TOTKLPRD3\\4': {'@K': None, '@H': None},  # ТАЙМЕРА ОТКЛ ПРД (0 – ВЫКЛ)
        '15.00.TOTKLPRD4\\4': {'@K': None, '@H': None},  # ТАЙМЕРА ОТКЛ ПРД (0 – ВЫКЛ)
        '15.00.MKPD1\\2': {'@K': None, '@H': None},  # ОБМЕНА ПО МКПД. ДИ = 1 - РАБОТАЕТ
        '15.00.MKPD2\\2': {'@K': None, '@H': None},  # ОБМЕНА ПО МКПД. ДИ = 1 - РАБОТАЕТ
        '15.00.MKPD3\\4': {'@K': None, '@H': None},  # ОБМЕНА ПО МКПД. ДИ = 1 - РАБОТАЕТ
        '15.00.MKPD4\\4': {'@K': None, '@H': None},  # ОБМЕНА ПО МКПД. ДИ = 1 - РАБОТАЕТ
        '15.00.UPRM1\\2': {'@K': None, '@H': None},  # УРОВНЯ ПРИНИМАЕМОГО СИГНАЛА (норма 90-210)
        '15.00.UPRML2\\2': {'@K': None, '@H': None},  # УРОВНЯ ПРИНИМАЕМОГО СИГНАЛА (норма 90-210)
        '15.00.UPRM3\\4': {'@K': None, '@H': None},  # УРОВНЯ ПРИНИМАЕМОГО СИГНАЛА (норма 90-210)
        '15.00.UPRM4\\4': {'@K': None, '@H': None},  # УРОВНЯ ПРИНИМАЕМОГО СИГНАЛА (норма 90-210)
        # ЗД
        '05.01.beBOD1OG11': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                             '@H': {'on': '0', 'off': '1'}},  # ключ ЗД1
        '05.02.CBOD1OG12': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                            '@H': {'on': '0', 'off': '1'}},  # ток ЗД1
        '05.01.beBOD1OG21': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                             '@H': {'on': '0', 'off': '1'}},  # ключ ЗД2
        '05.02.CBOD1OG22': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                            '@H': {'on': '0', 'off': '1'}},  # ток ЗД2
        '05.01.beBOD2OG11': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                             '@H': {'on': '0', 'off': '1'}},  # ключ ЗД3
        '05.02.CBOD2OG12': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                            '@H': {'on': '0', 'off': '1'}},  # ток ЗД3
        '05.01.beBOD2OG21': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                             '@H': {'on': '0', 'off': '1'}},  # ключ ЗД4
        '05.02.CBOD2OG22': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                            '@H': {'on': '0', 'off': '1'}},  # ток ЗД4
        '00.08.OrientReady_ST1': {'@K': {'yes': '\'узнать\'', 'no': '\'узнать\''},
                                  '@H': {'yes': '0', 'no': '1'}},  # ориентация ЗД1
        '00.08.OrientReady_ST2': {'@K': {'yes': '\'узнать\'', 'no': '\'узнать\''},
                                  '@H': {'yes': '0', 'no': '1'}},  # ориентация ЗД2
        '00.08.OrientReady_ST3': {'@K': {'yes': '\'узнать\'', 'no': '\'узнать\''},
                                  '@H': {'yes': '0', 'no': '1'}},  # ориентация ЗД3
        '00.08.OrientReady_ST4': {'@K': {'yes': '\'узнать\'', 'no': '\'узнать\''},
                                  '@H': {'yes': '0', 'no': '1'}},  # ориентация ЗД4
        '00.08.Q_ST1_0': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД1 датчик 0
        '00.08.Q_ST1_1': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД1 датчик 1
        '00.08.Q_ST1_2': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД1 датчик 2
        '00.08.Q_ST1_3': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД1 датчик 3
        '00.08.Q_ST2_0': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД2 датчик 0
        '00.08.Q_ST2_1': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД2 датчик 1
        '00.08.Q_ST2_2': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД2 датчик 2
        '00.08.Q_ST2_3': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД2 датчик 3
        '00.08.Q_ST3_0': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД3 датчик 0
        '00.08.Q_ST3_1': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД3 датчик 1
        '00.08.Q_ST3_2': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД3 датчик 2
        '00.08.Q_ST3_3': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД3 датчик 3
        '00.08.Q_ST4_0': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД4 датчик 0
        '00.08.Q_ST4_1': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД4 датчик 1
        '00.08.Q_ST4_2': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД4 датчик 2
        '00.08.Q_ST4_3': {'@K': {'on': '\'узнать\'', 'off': '\'узнать\''},
                          '@H': {'on': '0', 'off': '1'}},  # ЗД4 датчик 3


        # РЛЦИ
        # Телеметрия БА (ЭА332)
        '10.01.BA_FIP1': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},   # ФИП-О включен («0») / выключен («1»)
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_FIP2': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},   # ФИП-Р включен («0») / выключен («1»)
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_MOD1': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},   # МОД-О включен («0») / выключен («1»)
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_MOD2': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},   # МОД-Р включен («0») / выключен («1»)
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_PCH1': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},   # ПЧ-О включен («0») / выключен («1»)
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_PCH2': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},   # ПЧ-Р включен («0») / выключен («1»)
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_UM1': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},     # УМ-О включен («0») / выключен («1»)
                         '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_UM2': {'@K': {'on': '\'включен\'', 'off': '\'отключен\''},     # УМ-Р включен («0») / выключен («1»)
                         '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_TEMP_CARD': {'@K': '[-20, 60]',   # Температура платы работающего комплекта БА: (-20°С...+60°С)
                               '@H': '[-20, 60]'},
        '10.01.BA_TEMP_CONTR': {'@K': '[-20, 60]',  # Температура контроллера работающего комплекта БА: (-20°С...+60°С)
                                '@H': '[-20, 60]'},
        '10.01.BA_U_Ret1': {'@K': '[0.42, 0.52]',   # Напряжение на резисторах Rэт1 (47 Ом) + Rк : (0,42..0,52) В
                            '@H': '[0.42, 0.52]'},
        '10.01.BA_U_Ret2': {'@K': '[0.67, 0.81]',   # Напряжение на резисторах Rэт2 (74,1 Ом) + Rк : (0,67..0,81) В
                            '@H': '[0.67, 0.81]'},
        '10.01.BA_Sec': {'@K': '@unsame@all',       # Секунды (разряды 15…0)
                         '@H': '@unsame@all'},
        '10.01.BA_NUMB_LAST_UV': {'@K': '[0, 27]',    # Номер последнего принятого УВ: (0..27)
                                  '@H': '[0, 27]'},
        '10.01.BA_FRAME_COUNTER_DI': {'@K': '[0, 255]',     # Счетчик кадров ДИ: (0..255)
                                      '@H': '[0, 255]'},
        # Телеметрия ФИП (ЭА330)
        '10.01.FIP1_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие питание бортсети ФИП-О: «0» – есть, «1» – нет
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.FIP2_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие питание бортсети ФИП-Р: «0» – есть, «1» – нет
                          '@H': {'on': '0', 'off': '1'}},
        '10.01.FIP1_U': {'@K': {'on': '\'норма\'', 'off': '\'отключен\''},  # Уровень напряжения вторичного питания ФИП-О: (0..0,6) В – откл./ (1,5..3,0) В – норма
                         '@H': {'on': '[1.5, 3.0]', 'off': '[0, 0.6]'}},
        '10.01.FIP2_U': {'@K': {'on': '\'норма\'', 'off': '\'отключен\''},  # Уровень напряжения вторичного питания ФИП-Р: (0..0,6) В – откл./ (1,5..3,0) В – норма
                         '@H': {'on': '[1.5, 3.0]', 'off': '[0, 0.6]'}},
        '10.01.FIP_INFO': {'@K': {'cele': '\'целевая - от м778б\'', 'imit': '\'тестовая - внутренняя\''},  # Целевая («0») / тестовая («1») информация ФИП
                            '@H': {'cele': '0', 'imit': '1'}},
        '10.01.FIP_MOD1_CONNECT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},  # Признак установки связи МОД-О: «0» - есть/ «1» - нет
                                   '@H': {'on': '0', 'off': '1'}},
        '10.01.FIP_MOD2_CONNECT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},  # Признак установки связи МОД-Р: «0» - есть / «1» - нет
                                   '@H': {'on': '0', 'off': '1'}},
        '10.01.FIP_M778B1_CONNECT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Признак установки связи ЦА-О: «0» - есть/ «1» - нет
                                        '@H': {'on': '0', 'off': '1'}} if DIstorage.commutations['M778B'][0] else {
                                        '@K': {'on': '\'нет\'', 'off': '\'нет\''},
                                        '@H': {'on': '1', 'off': '1'}},
        '10.01.FIP_M778B2_CONNECT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Признак установки связи ЦА-Р: «0» - есть/ «1» - нет
                                        '@H': {'on': '0', 'off': '1'}} if DIstorage.commutations['M778B'][0] else {
                                        '@K': {'on': '\'нет\'', 'off': '\'нет\''},
                                        '@H': {'on': '1', 'off': '1'}},
        '10.01.FIP_M778B_INF': {'@K': {'on': '\'есть\' @any', 'off': '\'нет\' @all'},         # Наличие данных от ЦА: «0» – есть, «1» – нет
                                '@H': {'on': '0 @any', 'off': '1 @all'}} if DIstorage.commutations['M778B'][0] else {
                                '@K': {'on': '\'нет\'', 'off': '\'нет\''},
                                '@H': {'on': '1', 'off': '1'}},
        '10.01.FIP_PLL1': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},  # Признак наличия частоты PLL1: «0» - есть/ «1» - нет
                           '@H': {'on': '0', 'off': '1'}},
        '10.01.FIP_PLL2': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},  # Признак наличия частоты PLL2: «0» - есть/ «1» - нет
                           '@H': {'on': '0', 'off': '1'}},
        '10.01.FIP_TEMP_IP': {'@K': '[-20, 60]',    # Температура источника питания работающего комплекта ФИП: (-20°С...+60°С)
                              '@H': '[-20, 60]'},
        '10.01.FIP_TEMP_PLIS': {'@K': '[-20, 70]',  # Температура ПЛИС работающего комплекта ФИП: (-20°С...+70°С)
                                '@H': '[-20, 70]'},
        # Телеметрия МОД (ЭА331)
        '10.01.PRD_MOD1_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие питание бортсети МОД-О: «0» – есть, «1» – нет
                              '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_MOD2_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие питание бортсети МОД-Р: «0» – есть, «1» – нет
                              '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_MOD1_U': {'@K': {'on': '\'норма\'', 'off': '\'отключен\''},  # Уровень напряжения вторичного питания МОД-О: (0..0,6) В – откл./ (3..5) В – норма
                             '@H': {'on': '[3, 5]', 'off': '[0, 0.6]'}},
        '10.01.PRD_MOD2_U': {'@K': {'on': '\'норма\'', 'off': '\'отключен\''},  # Уровень напряжения вторичного питания МОД-Р: (0..0,6) В – откл./ (3..5) В – норма
                             '@H': {'on': '[3, 5]', 'off': '[0, 0.6]'}},
        '10.01.PRD_MOD_INFO': {'@K': {'cele': '\'целевая\'', 'imit': '\'тестовая\''},   # Целевая («0») / тестовая («1») информация МОД
                               '@H': {'cele': '0', 'imit': '1'}},
        '10.01.MOD_VS': {'@K': {'VS1': '\'VS1 - 278 мбит/с\'', 'VS2': '\'vs2 - 300 мбит/с\''},    # Код символьной скорости: «00» – VS1, «01» – VS2
                         '@H': {'VS1': '0', 'VS2': '1'}},
        '10.01.PRD_MOD_M': {'@K': {'M1': '\'M1 - QPSK\'', 'M2': '\'M2 - 8PSK\'', 'M3': '\'M3 - 16APSK\'', 'M4': '\'M4 - 32APSK\''}, # Режим работы МОД: «00» – M1, «01» – M2, «10» – M3, «11» – M4
                            '@H': {'M1': '0', 'M2': '1', 'M3': '2', 'M4': '3'}},
        '10.01.PRD_MOD_FIP1_CONNECT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},  # Признак установки связи ФИП-О: «0» - есть / «1» - нет
                                       '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_MOD_FIP2_CONNECT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},  # Признак установки связи ФИП-Р: «0» - есть / «1» - нет
                                       '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_MOD_FIP_INF': {'@K': {'on': '\'есть\' @any', 'off': '\'нет\' @all'},   # Наличие данных от ФИП: «0» – есть / «1» – нет
                                  '@H': {'on': '0 @any', 'off': '1 @all'}},
        '10.01.PRD_MOD_STAT_FREQ_PLL': {'@K': {'on': '\'есть\'', 'off': '\'нет\''}, # Признак наличия частоты PLL MGT МОД: «0» – есть / «1» – нет
                                        '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_MOD_TEMP_CARD': {'@K': '[-20, 60]',  # Температура платы работающего комплекта МОД: (-20°С...+60°С)
                                    '@H': '[-20, 60]'},
        '10.01.PRD_MOD_TEMP_PLIS': {'@K': '[0, 80]',    # Температура ПЛИС работающего комплекта МОД: (0°С...+80°С)
                                    '@H': '[0, 80]'},
        '10.01.PRD_MOD1_U_SIT1_Temp': {'@K': '[0, 40]',  # Напряжение на датчике СИТ1 МОД-О + Rк : (0,5..0,8) В
                                       '@H': '[0.5, 0.8]'},
        '10.01.PRD_MOD2_U_SIT5_Temp': {'@K': '[0, 40]',  # Напряжение на датчике СИТ5 МОД-Р + Rк : (0,5..0,8) В
                                       '@H': '[0.5, 0.8]'},
        # Телеметрия ПЧ (ЭА331)
        '10.01.PRD_PCH1_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие питание бортсети ПЧ-О: «0» – есть, «1» – нет
                              '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH2_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие питание бортсети ПЧ-Р: «0» – есть, «1» – нет
                              '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH1_P_SYNT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие мощности синтезатора ПЧ-О: «0» – есть, «1» – нет
                                  '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH2_P_SYNT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие мощности синтезатора ПЧ-Р: «0» – есть, «1» – нет
                                  '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH1_F_SYNT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие частоты синтезатора ПЧ-О: «0» – есть, «1» – нет
                                  '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH2_F_SYNT': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},   # Наличие частоты синтезатора ПЧ-Р: «0» – есть, «1» – нет
                                  '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH1_P': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Наличие мощности на выходе ПЧ-О: «0» – есть, «1» – нет
                             '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH2_P': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Наличие мощности на выходе ПЧ-Р: «0» – есть, «1» – нет
                             '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH1_F': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Наличие частоты на выходе ПЧ-О: «0» – есть, «1» – нет
                             '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_PCH2_F': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Наличие мощности на выходе ПЧ-Р: «0» – есть, «1» – нет
                             '@H': {'on': '0', 'off': '1'}},
        # Телеметрия УМ (ЭА331)
        '10.01.PRD_UM1_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Наличие питание бортсети УМ-О: «0» – есть, «1» – нет
                             '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_UM2_BS': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},    # Наличие питание бортсети УМ-Р: «0» – есть, «1» – нет
                             '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_UM1_P': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},     # Наличие мощности внутри УМ-О: «0» – есть, «1» – нет
                            '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_UM2_P': {'@K': {'on': '\'есть\'', 'off': '\'нет\''},     # Наличие мощности внутри УМ-Р: «0» – есть, «1» – нет
                            '@H': {'on': '0', 'off': '1'}},
        '10.01.PRD_UM1_P_Out': {'@K': {'on': '\'норма\'', 'off': '\'отключен\''},   # Уровень выходной мощности УМ-О: (0..0,3) В – откл./ (1..3,0) В – норма
                                '@H': {'on': '[1, 3.0]', 'off': '[0, 0.3]'}},
        '10.01.PRD_UM2_P_Out': {'@K': {'on': '\'норма\'', 'off': '\'отключен\''},   # Уровень выходной мощности УМ-Р: (0..0,3) В – откл./ (1..3,0) В – норма
                                '@H': {'on': '[1, 3.0]', 'off': '[0, 0.3]'}},
        '10.01.PRD_KONV_U_SIT6_Temp': {'@K': '[0, 40]',  # Напряжение на датчике СИТ6 КОНВ + Rк : (0,5..0,75) В
                                       '@H': '[0.5, 0.75]'},
        # Телеметрия антенны
        '10.01.BA_AFU_NP_OX': {'@K': {'on': '\'да\'', 'off': '\'нет\''},    # Антенна достигала начального положения (НП) по оси OХ: «0» - да/ «1» - нет
                               '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_AFU_NP_OZ': {'@K': {'on': '\'да\'', 'off': '\'нет\''},    # Антенна достигала начального положения (НП) по оси OZ: «0» - да/ «1» - нет
                               '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_AFU_DNP_OX': {'@K': {'on': '\'да\'', 'off': '\'нет\''},   # Антенна в начальном положении по оси OX: «0» - да/ «1» - нет
                                '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_AFU_DNP_OZ': {'@K': {'on': '\'да\'', 'off': '\'нет\''},   # Антенна в начальном положении по оси OZ: «0» - да/ «1» - нет
                                '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_AFU_DKP_OX': {'@K': {'on': '\'да\'', 'off': '\'нет\''},   # Антенна в конечном положении по оси ОХ: «0» - да/ «1» - нет
                                '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_AFU_DKP_OZ': {'@K': {'on': '\'да\'', 'off': '\'нет\''},   # Антенна в конечном положении по оси OZ: «0» - да/ «1» - нет
                                '@H': {'on': '0', 'off': '1'}},
        '10.01.BA_AFU_IMP_OX': {'@K': '[0, 16383]',     # Количество импульсов, переданных на двигатель по оси OХ: (0…16383)
                                '@H': '[0, 16383]'},
        '10.01.BA_AFU_IMP_OZ': {'@K': '[0, 16383]',     # Количество импульсов, переданных на двигатель по оси OZ: (0…16383)
                                '@H': '[0, 16383]'}
    }

    @staticmethod
    def get(key):
        """Взять ключ из DI"""
        return DIstorage.DI[key]

    @staticmethod
    def commute(attr, val):
        """Изменить коммутацию и обновить поля в DI"""
        DIstorage.commutations[attr][0] = val
        changed = DIstorage._reset()
        for cypher in DIstorage.commutations[attr][1]:
            DIstorage.DI[cypher] = changed[cypher]
DIstorage.reset()

class DB:
    pause = 8


class DataJson:
    sotc_dict = {}
    uv_dict = {'all': {'list_uv': {}}}


"""открыть json с SCPICMD и SOTC"""
try:
    dataJSON = DataListUV(path=['engineers_src', 'list_uv.json'])
except Exception as ex:
    try:
        dataJSON = DataListUV(path=['..', 'list_uv.json'])  # для запуска без ИВК
    except Exception as ex:
        # raise Exception('Нифига не прочитался json')
        dataJSON = DataJson()


def print_start_and_end(string):
    """Декоратор вывод в консоль начала и конца работы функции"""
    def decorator(function):
        def wrapper(*args, **kwargs):
            replace_count = string.count('%s')
            text = string
            if replace_count > 1:
                raise Exception('В print_start_and_end максимум 1 вхождение %s')
            elif replace_count == 1:
                text = text % args[0]
            yprint('ВЫПОЛНИТЬ: ' + text)
            res = function(*args, **kwargs)
            yprint('ЗАВЕРШЕНО: ' + text)
            return res
        return wrapper
    return decorator


###################### FUNCTIONS ##############################
def windowChooser(btnsText, fooDict, labels=None, title=None, ret_btn=None):
    """Cоздает форму с кнопками выбора функции и запускает функцию"""
    btn_name = inputGG(btnsText, labels=labels, title=title, ret_btn=ret_btn)  # получить номер кнопки
    if btn_name is None:
        return
    fooDict[btn_name]()  # вызвать функцию
    return btn_name


def sendFromJson(fun, *args, toPrint=True, describe=None, pause=1):
    """отправить SOTC или РК и вывести в консоль описание JSON"""
    if toPrint:
        obj = None
        if fun.__name__ == 'SOTC':
            obj = dataJSON.sotc_dict.get(str(args[0]))
        elif fun.__name__ == 'SCPICMD':
            obj = dataJSON.uv_dict['all']['list_uv'].get('0x' + hex(args[0])[2:].upper())
        # if obj is None:
        #     yprint('В json нет обьекта: %s %s' % (fun.__name__, args[0]))
        # описание из json
        if obj is None:
            obj_describe = None
        else:
            obj_describe = obj.description
            # доп описание
            ascihex = [x for x in args if isinstance(x, AsciiHex)]
            if len(ascihex) > 0:
                try:
                    dop_descripton = obj.args.get('AsciiHex(\'' + str(ascihex[0]) + '\')')
                    obj_describe = obj_describe if dop_descripton is None else obj_describe + ' :::' + dop_descripton
                except Exception as ex:
                    obj_describe = None
        # переданное описание
        describe = obj_describe if describe is None else (
            describe if obj_describe is None else obj_describe + "; \n:::" + describe)
    send(fun, *args, toPrint=True, describe=describe)
    sleep(pause)
    # inputG('УВ:  ' + describe)  # пауза после каждого УВ


def doEquation(cyph, calib, status=None, ref_val=None, all_any=None):
    """Для составления выражения из словаря для executeTMI"""
    if all_any is not None and all_any not in ('all', 'any'):
        raise Exception('Параметр all_any принимает значения только: all, any')
    cyph = cyph.strip()
    calib = calib.strip()
    if ref_val is None:
        ref_val = DIstorage.get(cyph)[calib].strip() if status is None else DIstorage.get(cyph)[calib][status].strip()
    equaton = '{%s}%s==%s' % (cyph, calib, str(ref_val).strip())
    if not all_any:
        return equaton
    equaton = equaton.replace('@all', '')
    equaton = equaton.replace('@any', '')
    return equaton + '@' + all_any


def executeTMI(*args, pause=None, stopFalse=True, **kwargs):
    """Вычислить выражние ТМИ с паузой перед опросом"""
    if 'period' not in kwargs:
        kwargs['period'] = DB.pause
    if pause is None:
        pause = DB.pause
    sleep(pause)
    result, dict_cpyphers = controlGetEQ(*args, **kwargs)
    # if not result:
    #     rprint('НЕ НОРМА: проверь ДИ')
    if stopFalse and not result:
        rprint('НЕ НОРМА: проверь ДИ')
        inputG('Проверь ТМИ')
    return result, dict_cpyphers


def executeWaitTMI(*args, pause=None, stopFalse=True, **kwargs):
    """Вычислить выражние ТМИ с паузой перед опросом"""
    if 'period' not in kwargs:
        kwargs['period'] = DB.pause
    # пауза чтобы в бд изменились зачения
    # if pause is None:
    #     pause = DB.pause
    # sleep(pause)
    result, dict_cpyphers = controlWaitEQ(*args, **kwargs)
    # if not result:
    #     rprint('НЕ НОРМА: проверь ДИ')
    if stopFalse and not result:
        rprint('НЕ НОРМА: проверь ДИ')
        inputG('Проверь ТМИ')
    return result, dict_cpyphers


def getAndSleep(*args, pause=None, **kwargs):
    """Получить значение ДИ с паузой перед опросом чтобы обновилась БД"""
    if pause is None:
        pause = DB.pause
    sleep(pause)  # пауза перед опросм ДИ чтобы записалось в БД
    return Ex.get(*args, **kwargs)


def executeDI(*args, stopFalse=True, **kwargs):
    """
    Проверка ДИ, здесь без паузы, т.к передается значение ДИ
    используется вместе с getAndSleep для получения значения из базы
    :param stopFalse: bool Пауза выполения если возвращает False
    """
    result = controlGet(*args, **kwargs)
    if stopFalse and not result:
        inputG('Проверь ТМИ')
    return result





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
    def clcBCK(cls, pause=None):
        """Очистить весь накопитель БЦК"""
        if pause is None:
            return sendFromJson(SCPICMD, 0xE107, describe='Ждать %s сек' % cls.clc_pause, pause=cls.clc_pause)
        sendFromJson(SCPICMD, 0xE107, describe='Ждать %s сек' % cls.clc_pause, pause=pause)

    @classmethod
    @print_start_and_end(string='БЦК: сбросить накопитель')
    def downBCK(cls, pause=None):
        """Сброс ДИ с БЦК в БА КИС-Р всего накопителя"""
        if pause is None:
            return sendFromJson(SCPICMD, 0xE060, describe='Ждать %s сек' % cls.down_pause, pause=cls.down_pause)
        sendFromJson(SCPICMD, 0xE060, describe='Ждать %s сек' % cls.down_pause, pause=pause)



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
    def off(cls, ask_TMI=True):
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
    def on(cls, num, stop_shd=True, ask_TMI=True):
        cls.log('Включить все')
        EA332.on(num, stop_shd=stop_shd, ask_TMI=ask_TMI)
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


##################### COMMUTATIONS ############################
DIstorage.commute('M778B', False)
# Кнопки опрос ДИ
btn_ask_di = False
# пауза на опросБД
DB.pause = 10
# паузы БЦК
BCK.clc_pause = 10
BCK.down_pause = 20
# Включенные блоки
M778.cur = None
RLCI.EA332.cur = None
RLCI.EA331.cur = None
RLCI.PCH.cur = None
RLCI.FIP.cur = None
RLCI.MOD.cur = None
RLCI.UM.cur = None


############################### FUNCTIONS ####################################
def ACDC():
    """ДИ ФКП"""
    BCK.clcBCK()
    BCK.downBCK()
    res = Ex.get('ТМИ', {'04.02.VKKEA1': 'КАЛИБР',
                         '04.02.VKKEA2': 'КАЛИБР',
                         '04.02.VBAEA1': 'КАЛИБР',
                         '04.02.VBAEA2': 'КАЛИБР',
                         '04.02.CKKEA1': 'КАЛИБР',
                         '04.02.CKKEA2': 'КАЛИБР',
                         '04.02.CBAEA1': 'КАЛИБР',
                         '04.02.CBAEA2': 'КАЛИБР'}, 'ТЕКУЩ')
    strings = []
    for key in sorted(res.keys()):
        row = [key]
        val = res[key]
        row.extend([str(x) for x in val]) if isinstance(val, list) else row.append(str(val))
        strings.append(row)
    print(tabulate(strings, tablefmt='simple'))


def FKP_RLCI_DR():
    """ДИ ФКП дежурный режим РЛЦИ"""
    if RLCI.EA332.cur is None or RLCI.EA331.cur is None:
        raise Exception('Нет данных о включенных блоках')
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.24]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.1, 1.24]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))


def FKP_RLCI_SR():
    """ДИ ФКП сеансный режим РЛЦИ"""
    if RLCI.EA332.cur is None or RLCI.EA331.cur is None:
        raise Exception('Нет данных о включенных блоках')
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[1.0, 2.93]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[1.0, 3.45]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))


############################## ANTENNA TEST ###############################
def TEST_1():
    yprint('ТЕСТ 1 АФУ-Х БА-О: Остан ШД, ДКП')
    num = 1
    arrayDescriprion = 'Отправка массива НЗ 0x=4500, 0z=9500'
    array = '0x' \
            '805004509411E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            'A05005501C25E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            '000000000000000000000000000000000000000000000000000000000000000000000000'
    arrayDescriprion2 = 'Отправка массива НЗ 0x=9500, 0z=4500'
    array2 = '0x' \
             '805004501C25E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000' \
             'A05005509411E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
             '000000000000000000000000000000000000000000000000000000000000000000000000'

    yprint('ПРОВЕРКА УВ ОСТАН ШД')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    sleep(10)
    RLCI.mode('stop SHD', ask_TMI=False)
    RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
    RLCI.EA332.off()

    yprint('ПРОВЕРКА ДКП 0x')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    RLCI.isAntennaMoving()  # проверка что антенна движется
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint(arrayDescriprion)
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array), std=2))  # Отправка массива првоерка АФУ в НП
    yprint('Ждать АФУ в НЗ')
    sleep(5)
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ждем когда АФУ в 0гр зоне
    yprint('Проверка координат 0гр зоны, ДИ ДКП')
    executeTMI("{10.01.BA_AFU_IMP_OX}@H==[4200, 4800]" + " and " +
               "{10.01.BA_AFU_IMP_OZ}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
               "{10.01.BA_AFU_DKP_OX}@H==1" + " and " +
               "{10.01.BA_AFU_DKP_OZ}@H==0", count=2, period=8)
    RLCI.EA332.off()

    yprint('ПРОВЕРКА ДКП 0z')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    RLCI.isAntennaMoving()  # проверка что антенна движется
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint(arrayDescriprion2)
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array2), std=2))  # Отправка массива првоерка АФУ в НП
    yprint('Ждать АФУ в НЗ')
    sleep(5)
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ждем когда АФУ в 0гр зоне
    yprint('Проверка координат 0гр зоны, ДИ ДКП')
    executeTMI("{10.01.BA_AFU_IMP_OX}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
               "{10.01.BA_AFU_IMP_OZ}@H==[4200, 4800]" + " and " +
               "{10.01.BA_AFU_DKP_OX}@H==0" + " and " +
               "{10.01.BA_AFU_DKP_OZ}@H==1", count=2, period=8)
    RLCI.EA332.off()
    yprint('ТЕСТ 1 ЗАВЕРШЕН', tab=1)


def TEST_2():
    yprint('ТЕСТ 2 АФУ-Х БА-Р: Отработка массива')
    num = 1
    arrayDescriprion = 'Отправка массива НЗ 0x=500, 0z=500'
    array = '0x' \
            '80500450F401F401640064803200C8000A002C01140084830A0000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            'A0500550F40158026400C88032002C01140064001E008483140000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            '000000000000000000000000000000000000000000000000000000000000000000000000'

    yprint('ПРОВЕРКА ОТРАБОТКА МАССИВ')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint(arrayDescriprion)
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array), std=2))  # Отправка массива првоерка АФУ в НП
    yprint('Ждать АФУ в НЗ')
    sleep(5)
    RLCI.waitAntennaStop(period=60 + 40, toPrint=False)  # ожидание когда антенна остановится в 0 градусной зоне
    executeTMI("{10.01.BA_AFU_IMP_OZ}@H==500" + " and " +  # проверка координат 0 градуснйо зоны
               "{10.01.BA_AFU_IMP_OX}@H==500" + " and " +
               "{10.01.BA_AFU_NP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_NP_OX}@H==0")
    # Запустить отработку массива
    RLCI.mode('start SHD')
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание когда антенна остановится, или sleep(посчитать время)
    executeTMI("{10.01.BA_AFU_IMP_OZ}@H==@same@all" + " and " +  # Проверка НП и ДНП после остановки
               "{10.01.BA_AFU_IMP_OX}@H==@same@all" + " and " +
               "{10.01.BA_AFU_NP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_NP_OX}@H==0" + " and " +
               "{10.01.BA_AFU_DNP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_DNP_OX}@H==0", count=2, period=8)
    RLCI.EA332.off()
    yprint('ТЕСТ 2 ЗАВЕРШЕН', tab=1)


############################### RLCIV ########################################
def TEST_3():
    yprint('ТЕСТ 3 РЛЦИ-В БА-О: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление')
    num = 1

    RLCI.EA332.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur]
    executeTMI(" and ".join(di))
    RLCI.EA331.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 0.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.mode('RS485-1')  # RS485-0
    RLCI.PCH.on(num)  # Вкл ПЧ-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 0.9]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.FIP.on(num)  # Вкл ФИП-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.7]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.MOD.on(num)  # Вкл МОД-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 2.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.UM.on(num)  # Вкл УМ-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 3.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    stopTime = datetime.now() + timedelta(minutes=12, seconds=30)

    RLCI.mode('VS1')  # Уст Симв Скор VS1
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1')

    RLCI.mode('RS485-2')  # RS485-Р
    RLCI.mode('VS2')  # Уст Симв Скор VS2
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2 включен ИМ-ФИП')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2 включен ИМ-ФИП')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2 включен ИМ-ФИП')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2 включен ИМ-ФИП')

    RLCI.mode('on imFIP')  # Вкл ИМ-ФИП
    RLCI.mode('off imFIP')  # Откл ИМ-ФИП

    RLCI.mode('on imMOD')  # Вкл ИМ-Мод
    RLCI.mode('off imMOD')  # Откл ИМ-Мод

    # ждать 12 минут
    yprint('Ждать 12 минут отключения по таймеру аппаратуры РЛЦИ')
    while datetime.now() < stopTime:
        sleep(1)
    yprint('Проверка ДИ что РЛЦИ отключен')
    sleep(10)
    executeTMI(doEquation('10.01.BA_FIP1', '@K', 'off') + " and " +
               doEquation('10.01.BA_MOD1', '@K', 'off') + " and " +
               doEquation('10.01.BA_PCH1', '@K', 'off') + " and " +
               doEquation('10.01.BA_UM1', '@K', 'off') + " and " +
               doEquation('10.01.FIP1_BS', '@K', 'off') + " and " +
               doEquation('10.01.FIP_MOD1_CONNECT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_MOD1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_P_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_F_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_F', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_P_Out', '@K', 'off'), count=1)
    RLCI.PCH.cur = None
    RLCI.FIP.cur = None
    RLCI.MOD.cur = None
    RLCI.UM.cur = None
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 3 ЗАВЕРШЕН', tab=1)


def TEST_4():
    yprint('ТЕСТ 4 РЛЦИ-В БА-Р: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление')
    num = 2

    RLCI.EA332.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur]
    executeTMI(" and ".join(di))
    RLCI.EA331.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 0.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.mode('RS485-1')  # RS485-0
    RLCI.PCH.on(num)  # Вкл ПЧ-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 0.9]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.FIP.on(num)  # Вкл ФИП-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.7]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.MOD.on(num)  # Вкл МОД-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 2.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.UM.on(num)  # Вкл УМ-О
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 3.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    stopTime = datetime.now() + timedelta(minutes=12, seconds=30)

    RLCI.mode('VS1')  # Уст Симв Скор VS1
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1')

    RLCI.mode('RS485-2')  # RS485-Р
    RLCI.mode('VS2')  # Уст Симв Скор VS2
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2 включен ИМ-ФИП')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2 включен ИМ-ФИП')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2 включен ИМ-ФИП')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2 включен ИМ-ФИП')

    RLCI.mode('on imFIP')  # Вкл ИМ-ФИП
    RLCI.mode('off imFIP')  # Откл ИМ-ФИП

    RLCI.mode('on imMOD')  # Вкл ИМ-Мод
    RLCI.mode('off imMOD')  # Откл ИМ-Мод

    # ждать 12 минут
    yprint('Ждать 12 минут отключения по таймеру аппаратуры РЛЦИ')
    while datetime.now() < stopTime:
        sleep(1)
    yprint('Проверка ДИ что РЛЦИ отключен')
    sleep(10)
    executeTMI(doEquation('10.01.BA_FIP1', '@K', 'off') + " and " +
               doEquation('10.01.BA_MOD1', '@K', 'off') + " and " +
               doEquation('10.01.BA_PCH1', '@K', 'off') + " and " +
               doEquation('10.01.BA_UM1', '@K', 'off') + " and " +
               doEquation('10.01.FIP1_BS', '@K', 'off') + " and " +
               doEquation('10.01.FIP_MOD1_CONNECT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_MOD1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_P_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_F_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_F', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_P_Out', '@K', 'off'), count=1)
    RLCI.PCH.cur = None
    RLCI.FIP.cur = None
    RLCI.MOD.cur = None
    RLCI.UM.cur = None
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 4 ЗАВЕРШЕН', tab=1)


############################## DESCRIPTION ###############################
def TEST_DESCRIPTION():
    # АФУ
    print(Text.yellow + "ТЕСТ 1" + Text.default + ": АФУ-Х БА-О: Остан ШД, ДКП;")
    print(Text.yellow + "ТЕСТ 2" + Text.default + ": АФУ-Х БА-Р: Отработка массива;")
    # РЛЦИ
    print(
        Text.yellow + "ТЕСТ 3" + Text.default + ": РЛЦИ-В БА-О: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление;")
    print(
        Text.yellow + "ТЕСТ 4" + Text.default + ": РЛЦИ-В БА-Р: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление;")


####################################################
################### MAIN ###########################
####################################################
foo = {
    'M778': lambda: windowChooser(
        btnsText=(('ВКЛ А', 'ВКЛ Б'), 'ОТКЛ'),
        title='ПИТАНИЕ М778',
        fooDict={'ВКЛ А': lambda: M778.on(1),
                 'ВКЛ Б': lambda: M778.on(2),
                 'ОТКЛ': lambda: M778.off()},
        ret_btn=True),
    'РЛЦИ ЭА': lambda: windowChooser(
        btnsText=(('ВКЛ ЭА332-1', 'ВКЛ ЭА332-2', 'ОТКЛ ЭА332'), ('ВКЛ ЭА331-1', 'ВКЛ ЭА331-2', 'ОТКЛ ЭА331')),
        title='РЛЦИ ПОД ПИТАНИЕ',
        fooDict={
            'ВКЛ ЭА332-1': lambda: RLCI.EA332.on(1, stop_shd=True, ask_TMI=btn_ask_di),
            'ВКЛ ЭА332-2': lambda: RLCI.EA332.on(2, stop_shd=True, ask_TMI=btn_ask_di),
            'ОТКЛ ЭА332': lambda: RLCI.EA332.off(ask_TMI=btn_ask_di),
            'ВКЛ ЭА331-1': lambda: RLCI.EA331.on(1, ask_TMI=btn_ask_di),
            'ВКЛ ЭА331-2': lambda: RLCI.EA331.on(2, ask_TMI=btn_ask_di),
            'ОТКЛ ЭА331': lambda: RLCI.EA331.off(ask_TMI=btn_ask_di)},
        labels=['ЭА332', 'ЭА331'],
        ret_btn=True),
    'РЛЦИ ПЧ': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ ПЧ',
        fooDict={
            'ОСН': lambda: RLCI.PCH.on(1, ask_TMI=btn_ask_di),
            'РЕЗ': lambda: RLCI.PCH.on(2, ask_TMI=btn_ask_di),
            'ОТКЛ': lambda: RLCI.PCH.off(ask_TMI=btn_ask_di)},
        ret_btn=True),
    'РЛЦИ ФИП': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ ФИП',
        fooDict={
            'ОСН': lambda: RLCI.FIP.on(1, ask_TMI=btn_ask_di),
            'РЕЗ': lambda: RLCI.FIP.on(2, ask_TMI=btn_ask_di),
            'ОТКЛ': lambda: RLCI.FIP.off(ask_TMI=btn_ask_di)},
        ret_btn=True),
    'РЛЦИ МОД': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ МОД',
        fooDict={
            'ОСН': lambda: RLCI.MOD.on(1, ask_TMI=btn_ask_di),
            'РЕЗ': lambda: RLCI.MOD.on(2, ask_TMI=btn_ask_di),
            'ОТКЛ': lambda: RLCI.MOD.off(ask_TMI=btn_ask_di)},
        ret_btn=True),
    'РЛЦИ УМ': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ УМ',
        fooDict={
            'ОСН': lambda: RLCI.UM.on(1, ask_TMI=btn_ask_di),
            'РЕЗ': lambda: RLCI.UM.on(2, ask_TMI=btn_ask_di),
            'ОТКЛ': lambda: RLCI.UM.off(ask_TMI=btn_ask_di)},
        ret_btn=True),
    'РЛЦИ РЕЖИМ': lambda: windowChooser(
        btnsText=(('M1', 'M2', 'M3', 'M4'), ('VS1', 'VS2'), ('RS485-1', 'RS485-2'), ('ИМ-МОД ВКЛ', 'ИМ-МОД ОТКЛ'),
                  ('ИМ-ФИП ВКЛ', 'ИМ-ФИП ОТКЛ'), ('СТОП ШД', 'ПУСК ШД')),
        title='РЛЦИ РЕЖИМ',
        fooDict={'M1': lambda: RLCI.mode('M1', ask_TMI=btn_ask_di),
                 'M2': lambda: RLCI.mode('M2', ask_TMI=btn_ask_di),
                 'M3': lambda: RLCI.mode('M3', ask_TMI=btn_ask_di),
                 'M4': lambda: RLCI.mode('M4', ask_TMI=btn_ask_di),
                 'VS1': lambda: RLCI.mode('VS1', ask_TMI=btn_ask_di),
                 'VS2': lambda: RLCI.mode('VS2', ask_TMI=btn_ask_di),
                 'RS485-1': lambda: RLCI.mode('RS485-1', ask_TMI=btn_ask_di),
                 'RS485-2': lambda: RLCI.mode('RS485-2', ask_TMI=btn_ask_di),
                 'ИМ-МОД ВКЛ': lambda: RLCI.mode('on imMOD', ask_TMI=btn_ask_di),
                 'ИМ-МОД ОТКЛ': lambda: RLCI.mode('off imMOD', ask_TMI=btn_ask_di),
                 'ИМ-ФИП ВКЛ': lambda: RLCI.mode('on imFIP', ask_TMI=btn_ask_di),
                 'ИМ-ФИП ОТКЛ': lambda: RLCI.mode('off imFIP', ask_TMI=btn_ask_di),
                 'СТОП ШД': lambda: RLCI.mode('stop SHD', ask_TMI=btn_ask_di),
                 'ПУСК ШД': lambda: RLCI.mode('start SHD', ask_TMI=btn_ask_di)},
        ret_btn=True),
    'РЛЦИ ВСЕ БЛОКИ': lambda: windowChooser(
        btnsText=('ВКЛ-1', 'ВКЛ-2', 'ОТКЛ'),
        title='РЛЦИ ВКЛ ОТКЛ',
        fooDict={'ВКЛ-1': lambda: RLCI.on(1),
                 'ВКЛ-2': lambda: RLCI.on(2),
                 'ОТКЛ': lambda: RLCI.off()},
        ret_btn=True),
    'ФКП ОПРОС KV': ACDC,
    'ФКП УСТ ДИ1с': lambda: sendFromJson(SCPICMD, 0x4258, AsciiHex('0x0100 0000')),  # уставка на опрос ДИ
    'ФКП УСТ ДИ10с': lambda: sendFromJson(SCPICMD, 0x4258, AsciiHex('0x0A00 0000')),  # уставка на опрос ДИ
    'ФКП РЛЦИ ДР': FKP_RLCI_DR,
    'ФКП РЛЦИ СР': FKP_RLCI_SR,
    'ТЕСТ 1': lambda: TEST_1(),
    'ТЕСТ 2': lambda: TEST_2(),
    'ТЕСТ 3': lambda: TEST_3(),
    'ТЕСТ 4': lambda: TEST_4(),
    'ОПИСАНИЕ ТЕСТОВ': lambda: TEST_DESCRIPTION()
}
# кнопки
btns = (('ТЕСТ 1', 'ТЕСТ 2'),  # афу
        ('ТЕСТ 3', 'ТЕСТ 4'),  # рлци
        # 'M778',
        ('РЛЦИ ЭА', 'РЛЦИ ПЧ', 'РЛЦИ ФИП', 'РЛЦИ МОД', 'РЛЦИ УМ', 'РЛЦИ РЕЖИМ', 'РЛЦИ ВСЕ БЛОКИ'),
        ('ФКП ОПРОС KV', 'ФКП УСТ ДИ1с', 'ФКП УСТ ДИ10с', 'ФКП РЛЦИ ДР', 'ФКП РЛЦИ СР'),
        'ОПИСАНИЕ ТЕСТОВ')

print()
yprint('РЛЦИВ ПМ1')
sendFromJson(SCPICMD, 0x4258, AsciiHex('0x0100 0000')),  # уставка на опрос ДИ ФКП
while True:
    print()
    try:
        windowChooser(btnsText=btns, fooDict=foo, labels=['АФУ-Х', 'РЛЦИ-В', 'Упр РЛЦИ-В', 'ФКП', ''])
    except Exception as ex:
        rprint("ОШИБКА В ТЕСТЕ")
        rprint(traceback.format_exc())