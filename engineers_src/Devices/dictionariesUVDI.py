from collections import OrderedDict


def DI_CYPHER(syst_num, pa, di_name):
    """сгенерировать шифр ДИ"""
    # syst_num = str(syst_num)  # Строковой формат номера системы
    # if pa < 10:
    #     pa_str = '0' + str(pa)
    # else:
    #     pa_str = str(pa)
    # return '%s.%s.%s' % (syst_num, pa, di_name)
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
        '10.01.FIP_M778B_INF': {'@K': {'on': '\'есть @any\'', 'off': '\'нет @all\''},         # Наличие данных от ЦА: «0» – есть, «1» – нет
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
        '10.01.PRD_MOD_FIP_INF': {'@K': {'on': '\'есть @any\'', 'off': '\'нет @all\''},   # Наличие данных от ФИП: «0» – есть / «1» – нет
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


# надо выполнить reset чтобы устанвоились DI в классе
DIstorage.reset()


# def ad_RLCI_BA_SS():
#     return OrderedDict([
#         ("BA_FIP1", DI_CYPHER(10, 1, 'BA_FIP1')),
#         ("BA_FIP2", DI_CYPHER(10, 1, 'BA_FIP2')),
#         ("BA_MOD1", DI_CYPHER(10, 1, 'BA_MOD1')),
#         ("BA_MOD2", DI_CYPHER(10, 1, 'BA_MOD2')),
#         ("BA_PCH1", DI_CYPHER(10, 1, 'BA_PCH1')),
#         ("BA_PCH2", DI_CYPHER(10, 1, 'BA_PCH2')),
#         ("BA_UM1", DI_CYPHER(10, 1, 'BA_UM1')),
#         ("BA_UM2", DI_CYPHER(10, 1, 'BA_UM2')),
#         ("BA_TEMP_CARD", DI_CYPHER(10, 1, 'BA_TEMP_CARD')),
#         ("BA_TEMP_CONTR", DI_CYPHER(10, 1, 'ControlType')),
#         ("BA_U_Ret1", DI_CYPHER(10, 1, 'ControlType')),
#         ("BA_U_Ret2", DI_CYPHER(10, 1, 'ControlType')),
#         ("BA_Sec", DI_CYPHER(10, 1, 'ControlType')),
#         ("BA_NUMB_LAST_UV", DI_CYPHER(10, 1, 'ControlType')),
#         ("BA_FRAME_COUNTER_DI", DI_CYPHER(10, 1, 'ControlType'))])
#
#
# def ad_RLCI_FIP_SS(block_num):
#     return OrderedDict([
#         ("FIP_BS", DI_CYPHER(10, 1, 'FIP%s_BS' % block_num)),
#         ("FIP_U", DI_CYPHER(10, 1, 'FIP%s_U' % block_num)),
#         ("FIP_INFO_M778B", DI_CYPHER(10, 1, 'FIP_INFO_M778B')),
#         ("FIP_MOD1_CONNECT", DI_CYPHER(10, 1, 'FIP_MOD1_CONNECT')),
#         ("FIP_MOD2_CONNECT", DI_CYPHER(10, 1, 'FIP_MOD2_CONNECT')),
#         ("FIP_M778B1_CONNECT", DI_CYPHER(10, 1, 'FIP_M778B1_CONNECT')),
#         ("FIP_M778B2_CONNECT", DI_CYPHER(10, 1, 'FIP_M778B2_CONNECT')),
#         ("FIP_M778B_INF", DI_CYPHER(10, 1, 'FIP_M778B_INF')),
#         ("FIP_PLL1", DI_CYPHER(10, 1, 'FIP_PLL1')),
#         ("FIP_PLL2", DI_CYPHER(10, 1, 'FIP_PLL2')),
#         ("FIP_TEMP_IP", DI_CYPHER(10, 1, 'FIP_TEMP_IP')),
#         ("FIP_TEMP_PLIS", DI_CYPHER(10, 1, 'FIP_TEMP_PLIS'))])
#
#
# def ad_RLCI_MOD_SS(block_num):
#     return OrderedDict([
#         ("PRD_MOD_BS", DI_CYPHER(10, 1, 'PRD_MOD%s_BS' % block_num)),
#         ("PRD_MOD_U", DI_CYPHER(10, 1, 'PRD_MOD%s_U' % block_num)),
#         ("PRD_MOD_INFO", DI_CYPHER(10, 1, 'PRD_MOD_INFO')),
#         ("MOD_VS", DI_CYPHER(10, 1, 'MOD_VS')),
#         ("PRD_MOD_M", DI_CYPHER(10, 1, 'PRD_MOD_M')),
#         ("PRD_MOD_FIP_CONNECT", DI_CYPHER(10, 1, 'PRD_MOD_FIP%s_CONNECT' % block_num)),
#         ("PRD_MOD_FIP_INF", DI_CYPHER(10, 1, 'PRD_MOD_FIP_INF')),
#         ("PRD_MOD_STAT_FREQ_PLL", DI_CYPHER(10, 1, 'PRD_MOD_STAT_FREQ_PLL')),
#         ("PRD_MOD_TEMP_CARD", DI_CYPHER(10, 1, 'PRD_MOD_TEMP_CARD')),
#         ("PRD_MOD_TEMP_PLIS", DI_CYPHER(10, 1, 'PRD_MOD_TEMP_PLIS')),
#         ("PRD_MOD1_U_SIT1_Temp", DI_CYPHER(10, 1, 'PRD_MOD1_U_SIT1_Temp')),
#         ("PRD_MOD2_U_SIT5_Temp", DI_CYPHER(10, 1, 'PRD_MOD2_U_SIT5_Temp'))])
#
#
# def ad_RLCI_PCH_SS(block_num):
#     return OrderedDict([
#         ("PRD_PCH_BS", DI_CYPHER(10, 1, 'PRD_PCH%s_BS' % block_num)),
#         ("PRD_PCH_P_SYNT", DI_CYPHER(10, 1, 'PRD_PCH%s_P_SYNT' % block_num)),
#         ("PRD_PCH_F_SYNT", DI_CYPHER(10, 1, 'PRD_PCH%s_F_SYNT' % block_num)),
#         ("PRD_PCH_P", DI_CYPHER(10, 1, 'PRD_PCH%s_P' % block_num)),
#         ("PRD_PCH_F", DI_CYPHER(10, 1, 'PRD_PCH%s_F' % block_num))])
#
#
# def ad_RLCI_UM_SS(block_num):
#     return OrderedDict([
#         ("PRD_UM_BS", DI_CYPHER(10, 1, 'PRD_UM%s_BS' % block_num)),
#         ("PRD_UM_P", DI_CYPHER(10, 1, 'PRD_UM%s_P' % block_num)),
#         ("PRD_UM_P_Out", DI_CYPHER(10, 1, 'PRD_UM%s_P_Out' % block_num)),
#         ("PRD_KONV_U_SIT6_Temp", DI_CYPHER(10, 1, 'PRD_KONV_U_SIT6_Temp'))])
#
#
# def ad_RLCI_AFU_SS():
#     return OrderedDict([
#         ("BA_AFU_NP_OX", DI_CYPHER(10, 1, 'BA_AFU_NP_OX')),
#         ("BA_AFU_NP_OZ", DI_CYPHER(10, 1, 'BA_AFU_NP_OZ')),
#         ("BA_AFU_DNP_OX", DI_CYPHER(10, 1, 'BA_AFU_DNP_OX')),
#         ("BA_AFU_DNP_OZ", DI_CYPHER(10, 1, 'BA_AFU_DNP_OZ')),
#         ("BA_AFU_DKP_OX", DI_CYPHER(10, 1, 'BA_AFU_DKP_OX')),
#         ("BA_AFU_DKP_OZ", DI_CYPHER(10, 1, 'BA_AFU_DKP_OZ')),
#         ("BA_AFU_IMP_OX", DI_CYPHER(10, 1, 'BA_AFU_IMP_OX')),
#         ("BA_AFU_IMP_OZ", DI_CYPHER(10, 1, 'BA_AFU_IMP_OZ'))])


def ad_dict_SS(syst_num):
    # Упорядоченный словарь СС АСН
    return OrderedDict([
        ("ResControl", DI_CYPHER(syst_num, 1, 'ResControl')), ("FailureFlag", DI_CYPHER(syst_num, 1, 'FailureFlag')),
        ("ControlType", DI_CYPHER(syst_num, 1, 'ControlType')),
        ("PrgStateSvUS", DI_CYPHER(syst_num, 1, 'PrgStateSvUS')),
        ("PrgStateSvPN", DI_CYPHER(syst_num, 1, 'PrgStateSvPN')),
        ("OrbitNavFlag", DI_CYPHER(syst_num, 1, 'OrbitNavFlag')),
        ("ConFormKS", DI_CYPHER(syst_num, 1, 'ConFormKS')), ("ConFormTimeSc", DI_CYPHER(syst_num, 1, 'ConFormTimeSc')),
        ("AutNavData", DI_CYPHER(syst_num, 1, 'AutNavData')),
        ("PreciseDigUse", DI_CYPHER(syst_num, 1, 'PreciseDigUse')),
        ("FormMV", DI_CYPHER(syst_num, 1, 'FormMV')), ("Year", DI_CYPHER(syst_num, 1, 'Year')),
        ("Month", DI_CYPHER(syst_num, 1, 'Month')),
        ("Day", DI_CYPHER(syst_num, 1, 'Day')), ("DateSource", DI_CYPHER(syst_num, 1, 'DateSource')),
        ("Hour", DI_CYPHER(syst_num, 1, 'Hour')),
        ("Minute", DI_CYPHER(syst_num, 1, 'Minute')), ("Second", DI_CYPHER(syst_num, 1, 'Second')),
        ("TimeCorKSVCh", DI_CYPHER(syst_num, 1, 'TimeCorKSVCh')),
        ("TimeCorMV", DI_CYPHER(syst_num, 1, 'TimeCorMV')), ("X", DI_CYPHER(syst_num, 1, 'X')),
        ("Y", DI_CYPHER(syst_num, 1, 'Y')),
        ("Z", DI_CYPHER(syst_num, 1, 'Z')), ("VX", DI_CYPHER(syst_num, 1, 'VX')), ("VY", DI_CYPHER(syst_num, 1, 'VY')),
        ("VZ", DI_CYPHER(syst_num, 1, 'VZ'))])


def ad_dict_DI_2(syst_num):
    # Упорядоченный словарь ДИ-2 АСН
    return OrderedDict([
        ("ResControl", DI_CYPHER(syst_num, 2, 'ResControl')), ("FailureFlag", DI_CYPHER(syst_num, 2, 'FailureFlag')),
        ("ControlType", DI_CYPHER(syst_num, 2, 'ControlType')),
        ("PrgStateSvUS", DI_CYPHER(syst_num, 2, 'PrgStateSvUS')),
        ("PrgStateSvPN", DI_CYPHER(syst_num, 2, 'PrgStateSvPN')), ("StateUS", DI_CYPHER(syst_num, 2, 'StateUS')),
        ("TestFaultsUS", DI_CYPHER(syst_num, 2, 'TestFaultsUS')), ("StatePN", DI_CYPHER(syst_num, 2, 'StatePN')),
        ("TestFaultsPN", DI_CYPHER(syst_num, 2, 'TestFaultsPN')), ("StateSPI", DI_CYPHER(syst_num, 2, 'StateSPI')),
        ("InterruptTSG", DI_CYPHER(syst_num, 2, 'InterruptTSG')),
        ("TimeMarkTSG", DI_CYPHER(syst_num, 2, 'TimeMarkTSG')),
        ("TimeMarkPN", DI_CYPHER(syst_num, 2, 'TimeMarkPN')), ("SyncPNandTM", DI_CYPHER(syst_num, 2, 'SyncPNandTM')),
        ("AdjustTMUS", DI_CYPHER(syst_num, 2, 'AdjustTMUS')), ("SecLenVarUS", DI_CYPHER(syst_num, 2, 'SecLenVarUS')),
        ("ProcStSvUS", DI_CYPHER(syst_num, 2, 'ProcStSvUS')), ("AccDataSvUS", DI_CYPHER(syst_num, 2, 'AccDataSvUS')),
        ("SPO3ofPN", DI_CYPHER(syst_num, 2, 'SPO3ofPN')), ("SPO1inBX0", DI_CYPHER(syst_num, 2, 'SPO1inBX0')),
        ("SPO1inBX1", DI_CYPHER(syst_num, 2, 'SPO1inBX1')), ("StateEPM", DI_CYPHER(syst_num, 2, 'StateEPM')),
        ("StateRAM", DI_CYPHER(syst_num, 2, 'StateRAM')), ("WatchTimerUS", DI_CYPHER(syst_num, 2, 'WatchTimerUS')),
        ("WorkTimerUS", DI_CYPHER(syst_num, 2, 'WorkTimerUS')), ("StateASP1US", DI_CYPHER(syst_num, 2, 'StateASP1US')),
        ("StateASP2US", DI_CYPHER(syst_num, 2, 'StateASP2US')),
        ("WatchTimerUS", DI_CYPHER(syst_num, 2, 'WatchTimerUS')),
        ("StateMKOUS", DI_CYPHER(syst_num, 2, 'StateMKOUS')), ("USsafetyPO1", DI_CYPHER(syst_num, 2, 'USsafetyPO1')),
        ("USsafetyPO2", DI_CYPHER(syst_num, 2, 'USsafetyPO2')), ("PNsafetyPO", DI_CYPHER(syst_num, 2, 'PNsafetyPO')),
        ("StateRPU1", DI_CYPHER(syst_num, 2, 'StateRPU1')), ("StateRPU2", DI_CYPHER(syst_num, 2, 'StateRPU2')),
        ("StateRPU3", DI_CYPHER(syst_num, 2, 'StateRPU3')), ("StateRPU4", DI_CYPHER(syst_num, 2, 'StateRPU4')),
        ("StateRPU5", DI_CYPHER(syst_num, 2, 'StateRPU5')), ("ResTestSynPN", DI_CYPHER(syst_num, 2, 'ResTestSynPN')),
        ("RPU1Sync", DI_CYPHER(syst_num, 2, 'RPU1Sync')), ("RPU1ActFilt", DI_CYPHER(syst_num, 2, 'RPU1ActFilt')),
        ("RPU1Temp", DI_CYPHER(syst_num, 2, 'RPU1Temp')), ("RPU1VCO", DI_CYPHER(syst_num, 2, 'RPU1VCO')),
        ("RPU1LPF11", DI_CYPHER(syst_num, 2, 'RPU1LPF11')), ("RPU1CHRC", DI_CYPHER(syst_num, 2, 'RPU1CHRC')),
        ("RPU1Gain", DI_CYPHER(syst_num, 2, 'RPU1Gain')), ("RPU2Sync", DI_CYPHER(syst_num, 2, 'RPU2Sync')),
        ("RPU2ActFilt", DI_CYPHER(syst_num, 2, 'RPU2ActFilt')), ("RPU2Temp", DI_CYPHER(syst_num, 2, 'RPU2Temp')),
        ("RPU2VCO", DI_CYPHER(syst_num, 2, 'RPU2VCO')), ("RPU2LPF11", DI_CYPHER(syst_num, 2, 'RPU2LPF11')),
        ("RPU2CHRC", DI_CYPHER(syst_num, 2, 'RPU2CHRC')), ("RPU2Gain", DI_CYPHER(syst_num, 2, 'RPU2Gain')),
        ("RPU3Sync", DI_CYPHER(syst_num, 2, 'RPU3Sync')), ("RPU3ActFilt", DI_CYPHER(syst_num, 2, 'RPU3ActFilt')),
        ("RPU3Temp", DI_CYPHER(syst_num, 2, 'RPU3Temp')), ("RPU3VCO", DI_CYPHER(syst_num, 2, 'RPU3VCO')),
        ("RPU3LPF11", DI_CYPHER(syst_num, 2, 'RPU3LPF11')), ("RPU3CHRC", DI_CYPHER(syst_num, 2, 'RPU3CHRC')),
        ("RPU3Gain", DI_CYPHER(syst_num, 2, 'RPU3Gain')), ("RPU4Sync", DI_CYPHER(syst_num, 2, 'RPU4Sync')),
        ("RPU4ActFilt", DI_CYPHER(syst_num, 2, 'RPU4ActFilt')), ("RPU4Temp", DI_CYPHER(syst_num, 2, 'RPU4Temp')),
        ("RPU4VCO", DI_CYPHER(syst_num, 2, 'RPU4VCO')), ("RPU4LPF11", DI_CYPHER(syst_num, 2, 'RPU4LPF11')),
        ("RPU4CHRC", DI_CYPHER(syst_num, 2, 'RPU4CHRC')), ("RPU4Gain", DI_CYPHER(syst_num, 2, 'RPU4Gain')),
        ("RPU5Sync", DI_CYPHER(syst_num, 2, 'RPU5Sync')), ("RPU5ActFilt", DI_CYPHER(syst_num, 2, 'RPU5ActFilt')),
        ("RPU5Temp", DI_CYPHER(syst_num, 2, 'RPU5Temp')), ("RPU5VCO", DI_CYPHER(syst_num, 2, 'RPU5VCO')),
        ("RPU5LPF11", DI_CYPHER(syst_num, 2, 'RPU5LPF11')), ("RPU5CHRC", DI_CYPHER(syst_num, 2, 'RPU5CHRC')),
        ("RPU5Gain", DI_CYPHER(syst_num, 2, 'RPU5Gain')), ("PNFreqVCO", DI_CYPHER(syst_num, 2, 'PNFreqVCO')),
        ("PNSync", DI_CYPHER(syst_num, 2, 'PNSync')), ("ProcSvPN", DI_CYPHER(syst_num, 2, 'ProcSvPN')),
        ("RAM0SvPN", DI_CYPHER(syst_num, 2, 'RAM0SvPN')), ("RAM1SvPN", DI_CYPHER(syst_num, 2, 'RAM1SvPN')),
        ("ROM2SvPN", DI_CYPHER(syst_num, 2, 'ROM2SvPN')), ("RAM3SvPN", DI_CYPHER(syst_num, 2, 'RAM3SvPN')),
        ("EPMSvPN", DI_CYPHER(syst_num, 2, 'EPMSvPN')), ("WatchTimerPN", DI_CYPHER(syst_num, 2, 'WatchTimerPN')),
        ("WorkTimerPN", DI_CYPHER(syst_num, 2, 'WorkTimerPN')), ("StateASP1PN", DI_CYPHER(syst_num, 2, 'StateASP1PN')),
        ("StateASP2PN", DI_CYPHER(syst_num, 2, 'StateASP2PN')), ("StatePKPN", DI_CYPHER(syst_num, 2, 'StatePKPN')),
        ("PNStateMKO", DI_CYPHER(syst_num, 2, 'PNStateMKO')), ("PNStateUTSO", DI_CYPHER(syst_num, 2, 'PNStateUTSO')),
        ("TimerFailPN", DI_CYPHER(syst_num, 2, 'TimerFailPN')),
        ("OPMsafetyBX0", DI_CYPHER(syst_num, 2, 'OPMsafetyBX0')),
        ("OPMsafetyBX1", DI_CYPHER(syst_num, 2, 'OPMsafetyBX1')), ("StatePIKw1", DI_CYPHER(syst_num, 2, 'StatePIKw1')),
        ("StatePIKw2", DI_CYPHER(syst_num, 2, 'StatePIKw2')), ("StatePIKw3", DI_CYPHER(syst_num, 2, 'StatePIKw3')),
        ("StateBBP", DI_CYPHER(syst_num, 2, 'StateBBP')), ("StateBDV", DI_CYPHER(syst_num, 2, 'StateBDV')),
        ("StateBD", DI_CYPHER(syst_num, 2, 'StateBD')), ("TimeSyncUnit", DI_CYPHER(syst_num, 2, 'TimeSyncUnit')),
        ("RdnW1", DI_CYPHER(syst_num, 2, 'RdnW1')), ("RdnW2", DI_CYPHER(syst_num, 2, 'RdnW2')),
        ("RdnW3", DI_CYPHER(syst_num, 2, 'RdnW3')), ("RdnW4", DI_CYPHER(syst_num, 2, 'RdnW4')),
        ("RdnW5", DI_CYPHER(syst_num, 2, 'RdnW5')), ("RdnW6", DI_CYPHER(syst_num, 2, 'RdnW6')),
        ("RdnW7", DI_CYPHER(syst_num, 2, 'RdnW7')), ("RdnW8", DI_CYPHER(syst_num, 2, 'RdnW8')),
        ("RdnCos", DI_CYPHER(syst_num, 2, 'RdnCos')), ("RdnW9", DI_CYPHER(syst_num, 2, 'RdnW9')),
        ("RdnW10", DI_CYPHER(syst_num, 2, 'RdnW10')), ("RdnW11", DI_CYPHER(syst_num, 2, 'RdnW11')),
        ("RdnW12", DI_CYPHER(syst_num, 2, 'RdnW12')), ("RdnW13", DI_CYPHER(syst_num, 2, 'RdnW13')),
        ("RdnW14", DI_CYPHER(syst_num, 2, 'RdnW14')), ("RdnW15", DI_CYPHER(syst_num, 2, 'RdnW15')),
        ("RdnW16", DI_CYPHER(syst_num, 2, 'RdnW16')), ("RdnW17", DI_CYPHER(syst_num, 2, 'RdnW17')),
        ("RdnW18", DI_CYPHER(syst_num, 2, 'RdnW18'))])


def ad_dict_DI_3(syst_num):
    # Упорядоченный словарь ДИ-3 АСН
    return OrderedDict([
        ("IntegrFailCrit1", DI_CYPHER(syst_num, 3, 'IntegrFailCrit1')),
        ("IntegrFailPlace1", DI_CYPHER(syst_num, 3, 'IntegrFailPlace1')),
        ("NumberBX1", DI_CYPHER(syst_num, 3, 'NumberBX1')), ("NumberBExe1", DI_CYPHER(syst_num, 3, 'NumberBExe1')),
        ("FailureCode1", DI_CYPHER(syst_num, 3, 'FailureCode1')),
        ("FailureTime1", DI_CYPHER(syst_num, 3, 'FailureTime1')),
        ("FailureInf1W1", DI_CYPHER(syst_num, 3, 'FailureInf1W1')),
        ("FailureInf1W2", DI_CYPHER(syst_num, 3, 'FailureInf1W2')),
        ("IntegrFailCrit2", DI_CYPHER(syst_num, 3, 'IntegrFailCrit2')),
        ("IntegrFailPlace2", DI_CYPHER(syst_num, 3, 'IntegrFailPlace2')),
        ("NumberBX2", DI_CYPHER(syst_num, 3, 'NumberBX2')), ("NumberBExe2", DI_CYPHER(syst_num, 3, 'NumberBExe2')),
        ("FailureCode2", DI_CYPHER(syst_num, 3, 'FailureCode2')),
        ("FailureTime2", DI_CYPHER(syst_num, 3, 'FailureTime2')),
        ("FailureInf2W1", DI_CYPHER(syst_num, 3, 'FailureInf2W1')),
        ("FailureInf2W2", DI_CYPHER(syst_num, 3, 'FailureInf2W2')),
        ("IntegrFailCrit3", DI_CYPHER(syst_num, 3, 'IntegrFailCrit3')),
        ("IntegrFailPlace3", DI_CYPHER(syst_num, 3, 'IntegrFailPlace3')),
        ("NumberBX3", DI_CYPHER(syst_num, 3, 'NumberBX3')), ("NumberBExe3", DI_CYPHER(syst_num, 3, 'NumberBExe3')),
        ("FailureCode3", DI_CYPHER(syst_num, 3, 'FailureCode3')),
        ("FailureTime3", DI_CYPHER(syst_num, 3, 'FailureTime3')),
        ("FailureInf3W1", DI_CYPHER(syst_num, 3, 'FailureInf3W1')),
        ("FailureInf3W2", DI_CYPHER(syst_num, 3, 'FailureInf3W2')),
        ("IntegrFailCrit4", DI_CYPHER(syst_num, 3, 'IntegrFailCrit4')),
        ("IntegrFailPlace4", DI_CYPHER(syst_num, 3, 'IntegrFailPlace4')),
        ("NumberBX4", DI_CYPHER(syst_num, 3, 'NumberBX4')), ("NumberBExe4", DI_CYPHER(syst_num, 3, 'NumberBExe4')),
        ("FailureCode4", DI_CYPHER(syst_num, 3, 'FailureCode4')),
        ("FailureTime4", DI_CYPHER(syst_num, 3, 'FailureTime4')),
        ("FailureInf4W1", DI_CYPHER(syst_num, 3, 'FailureInf4W1')),
        ("FailureInf4W2", DI_CYPHER(syst_num, 3, 'FailureInf4W2')),
        ("IntegrFailCrit5", DI_CYPHER(syst_num, 3, 'IntegrFailCrit5')),
        ("IntegrFailPlace5", DI_CYPHER(syst_num, 3, 'IntegrFailPlace5')),
        ("NumberBX5", DI_CYPHER(syst_num, 3, 'NumberBX5')), ("NumberBExe5", DI_CYPHER(syst_num, 3, 'NumberBExe5')),
        ("FailureCode5", DI_CYPHER(syst_num, 3, 'FailureCode5')),
        ("FailureTime5", DI_CYPHER(syst_num, 3, 'FailureTime5')),
        ("FailureInf5W1", DI_CYPHER(syst_num, 3, 'FailureInf5W1')),
        ("FailureInf5W2", DI_CYPHER(syst_num, 3, 'FailureInf5W2')),
        ("ST_AvailTemp", DI_CYPHER(syst_num, 3, 'ST_AvailTemp')),
        ("ST_SurcTemp", DI_CYPHER(syst_num, 3, 'ST_SurcTemp')),
        ("ST_Temp", DI_CYPHER(syst_num, 3, 'ST_Temp'))])


def ad_dict_DI_4(syst_num):
    # Упорядоченный словарь ДИ-4 АСН
    return OrderedDict([
        ("IntegrFailCrit6", DI_CYPHER(syst_num, 4, 'IntegrFailCrit6')),
        ("IntegrFailPlace6", DI_CYPHER(syst_num, 4, 'IntegrFailPlace6')),
        ("NumberBX6", DI_CYPHER(syst_num, 4, 'NumberBX6')),
        ("NumberBEexe6", DI_CYPHER(syst_num, 4, 'NumberBEexe6')),
        ("FailureCode6", DI_CYPHER(syst_num, 4, 'FailureCode6')),
        ("FailureTime6", DI_CYPHER(syst_num, 4, 'FailureTime6')),
        ("FailureInf6W1", DI_CYPHER(syst_num, 4, 'FailureInf6W1')),
        ("FailureInf6W2", DI_CYPHER(syst_num, 4, 'FailureInf6W2')),
        ("InputConfWord", DI_CYPHER(syst_num, 4, 'InputConfWord')),
        ("InputRejectWord", DI_CYPHER(syst_num, 4, 'InputRejectWord')),
        ("NumPAFail1", DI_CYPHER(syst_num, 4, 'NumPAFail1')),
        ("NumDNFail1", DI_CYPHER(syst_num, 4, 'NumDNFail1')),
        ("InfAboutFail1", DI_CYPHER(syst_num, 4, 'InfAboutFail1')),
        ("NumPAFail2", DI_CYPHER(syst_num, 4, 'NumPAFail2')),
        ("NumDNFail2", DI_CYPHER(syst_num, 4, 'NumDNFail2')),
        ("InfAboutFail2", DI_CYPHER(syst_num, 4, 'InfAboutFail2')),
        ("NumPAFail3", DI_CYPHER(syst_num, 4, 'NumPAFail3')),
        ("NumDNFail3", DI_CYPHER(syst_num, 4, 'NumDNFail3')),
        ("InfAboutFail3", DI_CYPHER(syst_num, 4, 'InfAboutFail3')),
        ("NumPAFail4", DI_CYPHER(syst_num, 4, 'NumPAFail4')),
        ("NumDNFail4", DI_CYPHER(syst_num, 4, 'NumDNFail4')),
        ("InfAboutFail4", DI_CYPHER(syst_num, 4, 'InfAboutFail4')),
        ("NumPAFail5", DI_CYPHER(syst_num, 4, 'NumPAFail5')),
        ("NumDNFail5", DI_CYPHER(syst_num, 4, 'NumDNFail5')),
        ("InfAboutFail5", DI_CYPHER(syst_num, 4, 'InfAboutFail5')),
        ("CurrentTime", DI_CYPHER(syst_num, 4, 'CurrentTime')),
        ("TimeMsg1057", DI_CYPHER(syst_num, 4, 'TimeMsg1057')),
        ("TimeMsg1058", DI_CYPHER(syst_num, 4, 'TimeMsg1058')),
        ("TimeMsg1059", DI_CYPHER(syst_num, 4, 'TimeMsg1059')),
        ("TimeMsg1063", DI_CYPHER(syst_num, 4, 'TimeMsg1063')),
        ("TimeMsg1064", DI_CYPHER(syst_num, 4, 'TimeMsg1064')),
        ("TimeMsg1065", DI_CYPHER(syst_num, 4, 'TimeMsg1065')),
        ("PPSOutputConfig", DI_CYPHER(syst_num, 4, 'PPSOutputConfig')),
        ("RecordToEZP", DI_CYPHER(syst_num, 4, 'RecordToEZP'))])


def ad_dict_DI_5(syst_num):
    # Упорядоченный словарь ДИ-5 АСН
    return OrderedDict([
        ("DataRdnRPU1", DI_CYPHER(syst_num, 5, 'DataRdnRPU1')), ("DataRdnRPU2", DI_CYPHER(syst_num, 5, 'DataRdnRPU2')),
        ("DataRdnRPU3", DI_CYPHER(syst_num, 5, 'DataRdnRPU3')), ("DataRdnRPU4", DI_CYPHER(syst_num, 5, 'DataRdnRPU4')),
        ("DataRdnRPU5", DI_CYPHER(syst_num, 5, 'DataRdnRPU5')),
        ("TempRPU1", DI_CYPHER(syst_num, 5, 'TempRPU1')), ("StateRegRPU1", DI_CYPHER(syst_num, 5, 'StateRegRPU1')),
        ("ThrQuantRPU1", DI_CYPHER(syst_num, 5, 'ThrQuantRPU1')),
        ("TempRPU2", DI_CYPHER(syst_num, 5, 'TempRPU2')), ("StateRegRPU2", DI_CYPHER(syst_num, 5, 'StateRegRPU2')),
        ("ThrQuantRPU2", DI_CYPHER(syst_num, 5, 'ThrQuantRPU2')),
        ("TempRPU3", DI_CYPHER(syst_num, 5, 'TempRPU3')), ("StateRegRPU3", DI_CYPHER(syst_num, 5, 'StateRegRPU3')),
        ("ThrQuantRPU3", DI_CYPHER(syst_num, 5, 'ThrQuantRPU3')),
        ("TempRPU4", DI_CYPHER(syst_num, 5, 'TempRPU4')), ("StateRegRPU4", DI_CYPHER(syst_num, 5, 'StateRegRPU4')),
        ("ThrQuantRPU4", DI_CYPHER(syst_num, 5, 'ThrQuantRPU4')),
        ("TempRPU5", DI_CYPHER(syst_num, 5, 'TempRPU5')), ("StateRegRPU5", DI_CYPHER(syst_num, 5, 'StateRegRPU5')),
        ("ThrQuantRPU5", DI_CYPHER(syst_num, 5, 'ThrQuantRPU5')),
        ("StartStopStorage", DI_CYPHER(syst_num, 5, 'StartStopStorage')),
        ("MemWriteRules", DI_CYPHER(syst_num, 5, 'MemWriteRules')),
        ("RawData", DI_CYPHER(syst_num, 5, 'RawData')), ("TLMdata", DI_CYPHER(syst_num, 5, 'TLMdata')),
        ("PVTdata", DI_CYPHER(syst_num, 5, 'PVTdata')),
        ("SCdata", DI_CYPHER(syst_num, 5, 'SCdata')), ("StartStopOutput", DI_CYPHER(syst_num, 5, 'StartStopOutput')),
        ("AccumRawData", DI_CYPHER(syst_num, 5, 'AccumRawData')),
        ("AccumTLM", DI_CYPHER(syst_num, 5, 'AccumTLM')), ("AccumPVT", DI_CYPHER(syst_num, 5, 'AccumPVT')),
        ("AccumGLOdata", DI_CYPHER(syst_num, 5, 'AccumGLOdata')),
        ("AccumGPSdata", DI_CYPHER(syst_num, 5, 'AccumGPSdata')),
        ("AccumGALdata", DI_CYPHER(syst_num, 5, 'AccumGALdata')),
        ("AccumBEIdata", DI_CYPHER(syst_num, 5, 'AccumBEIdata')),
        ("PseudRangSmooth", DI_CYPHER(syst_num, 5, 'PseudRangSmooth')), ("PVTtype", DI_CYPHER(syst_num, 5, 'PVTtype')),
        ("RawDataInterval", DI_CYPHER(syst_num, 5, 'RawDataInterval')),
        ("PVTInterval", DI_CYPHER(syst_num, 5, 'PVTInterval')), ("FreeMem", DI_CYPHER(syst_num, 5, 'FreeMem'))])


def ad_dict_DI_6(syst_num):
    # Упорядоченный словарь ДИ-6 АСН
    return OrderedDict([
        ("AttAxesDataReady", DI_CYPHER(syst_num, 6, 'AttAxesDataReady')),
        ("AttAxesDataSrc", DI_CYPHER(syst_num, 6, 'AttAxesDataSrc')),
        ("AttXC", DI_CYPHER(syst_num, 6, 'AttXC')), ("AttYC", DI_CYPHER(syst_num, 6, 'AttYC')),
        ("AttZC", DI_CYPHER(syst_num, 6, 'AttZC')),
        ("DCSType", DI_CYPHER(syst_num, 6, 'DCSType')), ("cosXC_X", DI_CYPHER(syst_num, 6, 'cosXC_X')),
        ("cosXC_Y", DI_CYPHER(syst_num, 6, 'cosXC_Y')),
        ("cosXC_Z", DI_CYPHER(syst_num, 6, 'cosXC_Z')), ("cosYC_X", DI_CYPHER(syst_num, 6, 'cosYC_X')),
        ("cosYC_Y", DI_CYPHER(syst_num, 6, 'cosYC_Y')),
        ("cosYC_Z", DI_CYPHER(syst_num, 6, 'cosYC_Z')), ("cosZC_X", DI_CYPHER(syst_num, 6, 'cosZC_X')),
        ("cosZC_Y", DI_CYPHER(syst_num, 6, 'cosZC_Y')),
        ("cosZC_Z", DI_CYPHER(syst_num, 6, 'cosZC_Z')),
        ("NES_NRRestartYr", DI_CYPHER(syst_num, 6, 'NES_NRRestartYr')),
        ("NES_NRRestartMon", DI_CYPHER(syst_num, 6, 'NES_NRRestartMon')),
        ("NES_NRRestartD", DI_CYPHER(syst_num, 6, 'NES_NRRestartD')),
        ("DateSource", DI_CYPHER(syst_num, 6, 'DateSource')),
        ("NES_NRRestartHr", DI_CYPHER(syst_num, 6, 'NES_NRRestartHr')),
        ("NES_NRRestartMin", DI_CYPHER(syst_num, 6, 'NES_NRRestartMin')),
        ("NES_NRRestartS", DI_CYPHER(syst_num, 6, 'NES_NRRestartS')),
        ("NES_NRRestartCnt", DI_CYPHER(syst_num, 6, 'NES_NRRestartCnt')),
        ("ConvPVTOptions", DI_CYPHER(syst_num, 6, 'ConvPVTOptions')),
        ("OrbCalcLSM", DI_CYPHER(syst_num, 6, 'OrbCalcLSM')),
        ("FreqDriftPoly", DI_CYPHER(syst_num, 6, 'FreqDriftPoly')),
        ("TimeScForm", DI_CYPHER(syst_num, 6, 'TimeScForm')),
        ("KSform", DI_CYPHER(syst_num, 6, 'KSform')), ("KSVCh_SPN", DI_CYPHER(syst_num, 6, 'KSVCh_SPN'))])


def ad_dict_DI_7(syst_num):
    # Упорядоченный словарь ДИ-7 АСН
    return OrderedDict([
        ("ERP_AvailDT", DI_CYPHER(syst_num, 7, 'ERP_AvailDT')),
        ("ERP_AvailUT1_UTC", DI_CYPHER(syst_num, 7, 'ERP_AvailUT1_UTC')),
        ("ERP_AvailXYPole", DI_CYPHER(syst_num, 7, 'ERP_AvailXYPole')),
        ("ERP_UT1_UTCSrc", DI_CYPHER(syst_num, 7, 'ERP_UT1_UTCSrc')),
        ("ERP_XYPoleSrc", DI_CYPHER(syst_num, 7, 'ERP_XYPoleSrc')),
        ("Year_1", DI_CYPHER(syst_num, 7, 'Year_1')), ("Month_1", DI_CYPHER(syst_num, 7, 'Month_1')),
        ("Day_1", DI_CYPHER(syst_num, 7, 'Day_1')),
        ("DateSource_1", DI_CYPHER(syst_num, 7, 'DateSource_1')),
        ("Hour_1", DI_CYPHER(syst_num, 7, 'Hour_1')), ("Minute_1", DI_CYPHER(syst_num, 7, 'Minute_1')),
        ("Second_1", DI_CYPHER(syst_num, 7, 'Second_1')),
        ("ERP_UT1_UTC", DI_CYPHER(syst_num, 7, 'ERP_UT1_UTC')),
        ("ERP_Xp", DI_CYPHER(syst_num, 7, 'ERP_Xp')),
        ("ERP_Yp", DI_CYPHER(syst_num, 7, 'ERP_Yp')),
        ("TimeDateValid", DI_CYPHER(syst_num, 7, 'TimeDateValid')),
        ("ConfirmMV", DI_CYPHER(syst_num, 7, 'ConfirmMV')),
        ("ValidTAI_UTC", DI_CYPHER(syst_num, 7, 'ValidTAI_UTC')),
        ("ASN_Mode", DI_CYPHER(syst_num, 7, 'ASN_Mode')), ("Year_2", DI_CYPHER(syst_num, 7, 'Year_2')),
        ("Month_2", DI_CYPHER(syst_num, 7, 'Month_2')), ("Day_2", DI_CYPHER(syst_num, 7, 'Day_2')),
        ("DateSource_2", DI_CYPHER(syst_num, 7, 'DateSource_2')),
        ("Hour_2", DI_CYPHER(syst_num, 7, 'Hour_2')), ("Minute_2", DI_CYPHER(syst_num, 7, 'Minute_2')),
        ("Second_2", DI_CYPHER(syst_num, 7, 'Second_2')),
        ("ShiftMV", DI_CYPHER(syst_num, 7, 'ShiftMV')),
        ("OutputTS", DI_CYPHER(syst_num, 7, 'OutputTS')),
        ("OutputCS", DI_CYPHER(syst_num, 7, 'OutputCS')),
        ("EllipsNum", DI_CYPHER(syst_num, 7, 'EllipsNum')),
        ("TimeAcc", DI_CYPHER(syst_num, 7, 'TimeAcc')),
        ("OutTSbyGNSS", DI_CYPHER(syst_num, 7, 'OutTSbyGNSS')),
        ("OperTS", DI_CYPHER(syst_num, 7, 'OperTS')),
        ("OutTSWholeSrc", DI_CYPHER(syst_num, 7, 'OutTSWholeSrc')),
        ("DigitType", DI_CYPHER(syst_num, 7, 'DigitType')),
        ("OutTSFractSrc", DI_CYPHER(syst_num, 7, 'OutTSFractSrc')),
        ("Diff_TAI_UTC", DI_CYPHER(syst_num, 7, 'Diff_TAI_UTC')),
        ("SrcTAI", DI_CYPHER(syst_num, 7, 'SrcTAI')),
        ("SrcUTC", DI_CYPHER(syst_num, 7, 'SrcUTC')),
        ("CorUTCflag", DI_CYPHER(syst_num, 7, 'CorUTCflag')),
        ("MaxHeight", DI_CYPHER(syst_num, 7, 'MaxHeight')),
        ("MinHeight", DI_CYPHER(syst_num, 7, 'MinHeight')),
        ("NumExcThresh", DI_CYPHER(syst_num, 7, 'NumExcThresh'))])


def ad_dict_DI_8(syst_num):
    # Упорядоченный словарь ДИ-8 АСН
    return OrderedDict([
        ("NumberYA", DI_CYPHER(syst_num, 8, 'NumberYA')), ("RdnCoordYA", DI_CYPHER(syst_num, 8, 'RdnCoordYA')),
        ("RdnAnglesYA", DI_CYPHER(syst_num, 8, 'RdnAnglesYA')),
        ("RdnBeamPtrnYA", DI_CYPHER(syst_num, 8, 'RdnBeamPtrnYA')),
        ("SrcCoordYA", DI_CYPHER(syst_num, 8, 'SrcCoordYA')),
        ("SrcAnglesYA", DI_CYPHER(syst_num, 8, 'SrcAnglesYA')),
        ("SrcBeamPtrnYA", DI_CYPHER(syst_num, 8, 'SrcBeamPtrnYA')), ("XCoordYA", DI_CYPHER(syst_num, 8, 'XCoordYA')),
        ("YCoordYA", DI_CYPHER(syst_num, 8, 'YCoordYA')), ("ZCoordYA", DI_CYPHER(syst_num, 8, 'ZCoordYA')),
        ("XAngleYA", DI_CYPHER(syst_num, 8, 'XAngleYA')),
        ("YAngleYA", DI_CYPHER(syst_num, 8, 'YAngleYA')), ("ZAngleYA", DI_CYPHER(syst_num, 8, 'ZAngleYA')),
        ("DiagrWidthYA", DI_CYPHER(syst_num, 8, 'DiagrWidthYA')),
        ("TF2_Usage", DI_CYPHER(syst_num, 8, 'TF2_Usage')),
        ("T1PreprocKSVCh", DI_CYPHER(syst_num, 8, 'T1PreprocKSVCh')),
        ("CoefNforT2", DI_CYPHER(syst_num, 8, 'CoefNforT2')),
        ("TF1polyDriftOG", DI_CYPHER(syst_num, 8, 'TF1polyDriftOG')),
        ("TF2polyDriftOG", DI_CYPHER(syst_num, 8, 'TF2polyDriftOG')),
        ("HDoubleIono", DI_CYPHER(syst_num, 8, 'HDoubleIono')),
        ("HDoubleTropo", DI_CYPHER(syst_num, 8, 'HDoubleTropo')), ("ThrPDOP", DI_CYPHER(syst_num, 8, 'ThrPDOP'))])


def ad_dict_DI_9(syst_num):
    # Упорядоченный словарь ДИ-9 АСН
    return OrderedDict([
        ("SerialNmbASN1", DI_CYPHER(syst_num, 9, 'SerialNmbASN1')),
        ("SerialNmbASN2", DI_CYPHER(syst_num, 9, 'SerialNmbASN2')),
        ("SerialNmbASN3", DI_CYPHER(syst_num, 9, 'SerialNmbASN3')),
        ("RegistrNmbASN", DI_CYPHER(syst_num, 9, 'RegistrNmbASN')),
        ("SPONumberASN", DI_CYPHER(syst_num, 9, 'SPONumberASN')),
        ("SPOVersASN", DI_CYPHER(syst_num, 9, 'SPOVersASN')),
        ("FileNavConfName1", DI_CYPHER(syst_num, 9, 'FileNavConfName1')),
        ("FileNavConfName2", DI_CYPHER(syst_num, 9, 'FileNavConfName2')),
        ("FileNavConfName3", DI_CYPHER(syst_num, 9, 'FileNavConfName3')),
        ("FileNavConfName4", DI_CYPHER(syst_num, 9, 'FileNavConfName4')),
        ("FileNavConfName5", DI_CYPHER(syst_num, 9, 'FileNavConfName5')),
        ("FileNavConfName6", DI_CYPHER(syst_num, 9, 'FileNavConfName6')),
        ("WorkTimeASN", DI_CYPHER(syst_num, 9, 'WorkTimeASN')),
        ("WorkTimePN", DI_CYPHER(syst_num, 9, 'WorkTimePN'))])


def ad_dict_DI_10(syst_num):
    # Упорядоченный словарь ДИ-10 АСН
    return OrderedDict([(
        "ThrNKA", DI_CYPHER(syst_num, 10, 'ThrNKA')), ("ThrSNR", DI_CYPHER(syst_num, 10, 'ThrSNR')),
        ("ThrGDOP", DI_CYPHER(syst_num, 10, 'ThrGDOP')),
        ("AbsKSVChRstPN", DI_CYPHER(syst_num, 10, 'AbsKSVChRstPN')),
        ("ThrTDOP", DI_CYPHER(syst_num, 10, 'ThrTDOP')),
        ("ThrAccMV", DI_CYPHER(syst_num, 10, 'ThrAccMV')),
        ("ToleranceMV", DI_CYPHER(syst_num, 10, 'ToleranceMV')),
        ("GPSUsage", DI_CYPHER(syst_num, 10, 'GPSUsage')),
        ("GLOFUsage", DI_CYPHER(syst_num, 10, 'GLOFUsage')),
        ("GALUsage", DI_CYPHER(syst_num, 10, 'GALUsage')),
        ("BEIUsage", DI_CYPHER(syst_num, 10, 'BEIUsage')),
        ("GLOCUsage", DI_CYPHER(syst_num, 10, 'GLOCUsage')),
        ("GLOOASUsage", DI_CYPHER(syst_num, 10, 'GLOOASUsage')),
        ("GPS_L1_CA", DI_CYPHER(syst_num, 10, 'GPS_L1_CA')),
        ("GPS_L2_CM", DI_CYPHER(syst_num, 10, 'GPS_L2_CM')),
        ("GPS_L2_CL", DI_CYPHER(syst_num, 10, 'GPS_L2_CL')),
        ("GLO_ L1_OF", DI_CYPHER(syst_num, 10, 'GLO_ L1_OF')),
        ("GLO_ L2_OF", DI_CYPHER(syst_num, 10, 'GLO_ L2_OF')),
        ("GAL_E1_B", DI_CYPHER(syst_num, 10, 'GAL_E1_B')),
        ("GAL_E1_C", DI_CYPHER(syst_num, 10, 'GAL_E1_C')),
        ("GAL_E5b_I", DI_CYPHER(syst_num, 10, 'GAL_E5b_I')),
        ("GAL_E5b_Q", DI_CYPHER(syst_num, 10, 'GAL_E5b_Q')),
        ("BEI_B1_I", DI_CYPHER(syst_num, 10, 'BEI_B1_I')),
        ("GLO_L1Ocd", DI_CYPHER(syst_num, 10, 'GLO_L1Ocd')),
        ("GLO_L1Ocp", DI_CYPHER(syst_num, 10, 'GLO_L1Ocp')),
        ("GLO_L2Ocd", DI_CYPHER(syst_num, 10, 'GLO_L2Ocd')),
        ("GLO_L2Ocp", DI_CYPHER(syst_num, 10, 'GLO_L2Ocp')),
        ("DoplerType", DI_CYPHER(syst_num, 10, 'DoplerType')),
        ("GNSSTimeBiasUse", DI_CYPHER(syst_num, 10, 'GNSSTimeBiasUse')),
        ("GNSSTimeBiasType", DI_CYPHER(syst_num, 10, 'GNSSTimeBiasType')),
        ("TimeBiasSrcGLONF", DI_CYPHER(syst_num, 10, 'TimeBiasSrcGLONF')),
        ("TimeBiasSrcGAL", DI_CYPHER(syst_num, 10, 'TimeBiasSrcGAL')),
        ("TimeBiasSrcBEI", DI_CYPHER(syst_num, 10, 'TimeBiasSrcBEI')),
        ("TimeBiasSrcGLONC", DI_CYPHER(syst_num, 10, 'TimeBiasSrcGLONC')),
        ("KSVChRecalcMV", DI_CYPHER(syst_num, 10, 'KSVChRecalcMV')),
        ("TypeTS", DI_CYPHER(syst_num, 10, 'TypeTS')), ("ShiftMV", DI_CYPHER(syst_num, 10, 'ShiftMV')),
        ("ScaleMV_Type", DI_CYPHER(syst_num, 10, 'ScaleMV_Type')),
        ("NumOutputCS", DI_CYPHER(syst_num, 10, 'NumOutputCS')),
        ("EllipsNum", DI_CYPHER(syst_num, 10, 'EllipsNum')),
        ("ASN_Mode", DI_CYPHER(syst_num, 10, 'ASN_Mode')),
        ("OrbFlightSimMode", DI_CYPHER(syst_num, 10, 'OrbFlightSimMode')),
        ("IonoDelayUse", DI_CYPHER(syst_num, 10, 'IonoDelayUse')),
        ("TropoDelayUse", DI_CYPHER(syst_num, 10, 'TropoDelayUse')),
        ("RecordToEZP", DI_CYPHER(syst_num, 10, 'RecordToEZP'))])


def ad_dict_DI_11(syst_num):
    # Упорядоченный словарь ДИ-11 АСН
    return OrderedDict([
        ("ShiftMV", DI_CYPHER(syst_num, 11, 'ShiftMV')), ("OutputTS", DI_CYPHER(syst_num, 11, 'OutputTS')),
        ("OutputCS", DI_CYPHER(syst_num, 11, 'OutputCS')), ("EllipsNum", DI_CYPHER(syst_num, 11, 'EllipsNum')),
        ("FreqGLONF1", DI_CYPHER(syst_num, 11, 'FreqGLONF1')),
        ("FreqGLONF2", DI_CYPHER(syst_num, 11, 'FreqGLONF2')), ("CodeGLONF1", DI_CYPHER(syst_num, 11, 'CodeGLONF1')),
        ("CodeGLONF2", DI_CYPHER(syst_num, 11, 'CodeGLONF2')),
        ("GLONCTVT", DI_CYPHER(syst_num, 11, 'GLONCTVT')), ("GPSL1", DI_CYPHER(syst_num, 11, 'GPSL1')),
        ("GPSL2", DI_CYPHER(syst_num, 11, 'GPSL2')),
        ("GALILEOL1", DI_CYPHER(syst_num, 11, 'GALILEOL1')), ("GALILEOL2", DI_CYPHER(syst_num, 11, 'GALILEOL2')),
        ("BEIDOUL1", DI_CYPHER(syst_num, 11, 'BEIDOUL1')),
        ("BEIDOUL2", DI_CYPHER(syst_num, 11, 'BEIDOUL2')), ("UseDistantNKA", DI_CYPHER(syst_num, 11, 'UseDistantNKA')),
        ("SidelobesYANKA", DI_CYPHER(syst_num, 11, 'SidelobesYANKA')),
        ("DistNKATropo2", DI_CYPHER(syst_num, 11, 'DistNKATropo2')),
        ("DistNKAIono2", DI_CYPHER(syst_num, 11, 'DistNKAIono2')),
        ("KSVChMethod", DI_CYPHER(syst_num, 11, 'KSVChMethod')),
        ("CoordKSVCh19", DI_CYPHER(syst_num, 11, 'CoordKSVCh19')),
        ("TimeKSVCh19", DI_CYPHER(syst_num, 11, 'TimeKSVCh19')),
        ("OrbitNavFlag", DI_CYPHER(syst_num, 11, 'OrbitNavFlag')),
        ("ConFormKS", DI_CYPHER(syst_num, 11, 'ConFormKS')),
        ("ConFormTimeSc", DI_CYPHER(syst_num, 11, 'ConFormTimeSc')),
        ("AutNavData", DI_CYPHER(syst_num, 11, 'AutNavData')),
        ("PreciseDigUse", DI_CYPHER(syst_num, 11, 'PreciseDigUse')), ("FormMV", DI_CYPHER(syst_num, 11, 'FormMV')),
        ("KSVChAvgInt", DI_CYPHER(syst_num, 11, 'KSVChAvgInt')),
        ("KSVChPredictInt", DI_CYPHER(syst_num, 11, 'KSVChPredictInt')), ("Year", DI_CYPHER(syst_num, 11, 'Year')),
        ("Month", DI_CYPHER(syst_num, 11, 'Month')),
        ("Day", DI_CYPHER(syst_num, 11, 'Day')), ("DateSource", DI_CYPHER(syst_num, 11, 'DateSource')),
        ("Hour", DI_CYPHER(syst_num, 11, 'Hour')),
        ("Minute", DI_CYPHER(syst_num, 11, 'Minute')), ("Second", DI_CYPHER(syst_num, 11, 'Second')),
        ("TimeCorKSVCh", DI_CYPHER(syst_num, 11, 'TimeCorKSVCh')),
        ("TimeCorMV", DI_CYPHER(syst_num, 11, 'TimeCorMV')), ("NormFreqCor", DI_CYPHER(syst_num, 11, 'NormFreqCor')),
        ("VX", DI_CYPHER(syst_num, 11, 'VX')),
        ("VY", DI_CYPHER(syst_num, 11, 'VY')), ("VZ", DI_CYPHER(syst_num, 11, 'VZ'))])


def ad_dict_DI_12(syst_num):
    # Упорядоченный словарь ДИ-12 АСН
    return OrderedDict([
        ("X", DI_CYPHER(syst_num, 12, 'X')), ("Y", DI_CYPHER(syst_num, 12, 'Y')),
        ("Z", DI_CYPHER(syst_num, 12, 'Z')), ("SKP_X", DI_CYPHER(syst_num, 12, 'SKP_X')),
        ("SKP_Y", DI_CYPHER(syst_num, 12, 'SKP_Y')),
        ("SKP_Z", DI_CYPHER(syst_num, 12, 'SKP_Z')), ("SKP_Time", DI_CYPHER(syst_num, 12, 'SKP_Time')),
        ("SKP_VX", DI_CYPHER(syst_num, 12, 'SKP_VX')),
        ("SKP_VY", DI_CYPHER(syst_num, 12, 'SKP_VY')), ("SKP_VZ", DI_CYPHER(syst_num, 12, 'SKP_VZ')),
        ("SKP_NFreqCor", DI_CYPHER(syst_num, 12, 'SKP_NFreqCor'))])


def ad_dict_DI_13(syst_num):
    # Упорядоченный словарь ДИ-13 АСН
    return OrderedDict([
        ("DoplerType", DI_CYPHER(syst_num, 13, 'DoplerType')), ("UseBias", DI_CYPHER(syst_num, 13, 'UseBias')),
        ("ValidKSVCh", DI_CYPHER(syst_num, 13, 'ValidKSVCh')), ("UseSPN", DI_CYPHER(syst_num, 13, 'UseSPN')),
        ("Freq2Range", DI_CYPHER(syst_num, 13, 'Freq2Range')),
        ("ResRAIM", DI_CYPHER(syst_num, 13, 'ResRAIM')), ("CoordKSVCh", DI_CYPHER(syst_num, 13, 'CoordKSVCh')),
        ("TimeKSVCh", DI_CYPHER(syst_num, 13, 'TimeKSVCh')),
        ("ImitOrbFl", DI_CYPHER(syst_num, 13, 'ImitOrbFl')), ("ASN_Mode", DI_CYPHER(syst_num, 13, 'ASN_Mode')),
        ("UseGPS", DI_CYPHER(syst_num, 13, 'UseGPS')),
        ("UseGLON", DI_CYPHER(syst_num, 13, 'UseGLON')), ("UseGAL", DI_CYPHER(syst_num, 13, 'UseGAL')),
        ("UseBEID", DI_CYPHER(syst_num, 13, 'UseBEID')),
        ("PreciseDigUse", DI_CYPHER(syst_num, 13, 'PreciseDigUse')), ("FormMV", DI_CYPHER(syst_num, 13, 'FormMV')),
        ("BiasGPSGLON", DI_CYPHER(syst_num, 13, 'BiasGPSGLON')),
        ("BiasGPSGAL", DI_CYPHER(syst_num, 13, 'BiasGPSGAL')), ("BiasGALGLON", DI_CYPHER(syst_num, 13, 'BiasGALGLON')),
        ("BiasGPSBEID", DI_CYPHER(syst_num, 13, 'BiasGPSBEID')),
        ("BiasGLONBEID", DI_CYPHER(syst_num, 13, 'BiasGLONBEID')),
        ("BiasGALBEID", DI_CYPHER(syst_num, 13, 'BiasGALBEID')), ("ShiftMV", DI_CYPHER(syst_num, 13, 'ShiftMV')),
        ("OutputTS", DI_CYPHER(syst_num, 13, 'OutputTS')), ("OutputCS", DI_CYPHER(syst_num, 13, 'OutputCS')),
        ("EllipsNum", DI_CYPHER(syst_num, 13, 'EllipsNum')),
        ("TimeAcc", DI_CYPHER(syst_num, 13, 'TimeAcc')), ("OutTSbyGNSS", DI_CYPHER(syst_num, 13, 'OutTSbyGNSS')),
        ("OperTS", DI_CYPHER(syst_num, 13, 'OperTS')),
        ("OutTSSource", DI_CYPHER(syst_num, 13, 'OutTSSource')), ("DigitType", DI_CYPHER(syst_num, 13, 'DigitType')),
        ("OutTSFract", DI_CYPHER(syst_num, 13, 'OutTSFract')),
        ("DataTimeAv", DI_CYPHER(syst_num, 13, 'DataTimeAv')), ("CoordAv", DI_CYPHER(syst_num, 13, 'CoordAv')),
        ("UTCAv", DI_CYPHER(syst_num, 13, 'UTCAv')),
        ("LeapSecAv", DI_CYPHER(syst_num, 13, 'LeapSecAv')), ("GDOP", DI_CYPHER(syst_num, 13, 'GDOP')),
        ("PDOP", DI_CYPHER(syst_num, 13, 'PDOP')),
        ("HDOP", DI_CYPHER(syst_num, 13, 'HDOP')), ("VDOP", DI_CYPHER(syst_num, 13, 'VDOP')),
        ("TDOP", DI_CYPHER(syst_num, 13, 'TDOP'))])


def ad_dict_DI_BA(block_num):
    # Упорядоченный словарь ДИ БА МКА
    return OrderedDict([
        ("CASN", DI_CYPHER(BA_num["FKP1"], 2, 'CASN' + str(block_num))),
        ("VASN", DI_CYPHER(BA_num["FKP1"], 2, 'VASN' + str(block_num))),
        ("ASN_key2_state", DI_CYPHER(BA_num["FKP1"], 1, 'beASN' + str(block_num) + '2')),
        ("SM_4_main", DI_CYPHER(BA_num["BTSK"], 1, 'PPS0')),
        ("SM_4_res", DI_CYPHER(BA_num["BTSK"], 1, 'PPS1')),
        ("SM_3_main", DI_CYPHER(BA_num["KSO"], 1, 'PPS1')),
        ("SM_3_res", DI_CYPHER(BA_num["KSO"], 1, 'PPS2')), ])
