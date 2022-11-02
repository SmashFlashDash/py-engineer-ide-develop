from engineers_src.Devices.Device import Device
from engineers_src.Devices.BCK import BCK
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, config, AsciiHex, KPA, SOTC, SKPA, Ex, sleep
from lib.tabulate.tabulate import tabulate


class KSO(Device):
    cur = None
    di = config.odict(('00.01.PPS1', []), ('00.01.PPS2', []),
                        ('00.02.Sat_Bx', []), ('00.02.Sat_By', []), ('00.02.Sat_Bz', []),
                        ('00.02.Sat_Bx_2', []), ('00.02.Sat_By_2', []), ('00.02.Sat_Bz_2', []),
                        ('00.01.FT1_FD1', []), ('00.01.FT1_FD2', []), ('00.01.FT1_FD3', []), ('00.01.FT1_FD4', []),
                        ('00.01.FT2_FD1', []), ('00.01.FT2_FD2', []), ('00.01.FT2_FD3', []), ('00.01.FT2_FD4', []),
                        ('00.05.BIUS1MeasX', []), ('00.05.BIUS1MeasY', []), ('00.05.BIUS1MeasZ', []),
                        ('00.05.BIUS2MeasX', []), ('00.05.BIUS2MeasY', []), ('00.05.BIUS2MeasZ', []),
                        ("00.08.Q_ST1_0", [],), ("00.08.Q_ST1_1", [],), ("00.08.Q_ST1_2", [],), ("00.08.Q_ST1_3", [],),
                        ("00.08.Q_ST2_0", [],), ("00.08.Q_ST2_1", [],), ("00.08.Q_ST2_2", [],), ("00.08.Q_ST2_3", [],),
                        ("00.08.Q_ST3_0", [],), ("00.08.Q_ST3_1", [],), ("00.08.Q_ST3_2", [],), ("00.08.Q_ST3_3", [],),
                        ("00.08.Q_ST4_0", [],), ("00.08.Q_ST4_1", [],), ("00.08.Q_ST4_2", [],), ("00.08.Q_ST4_3", [],))
    quaternions = {
        1: (round(0.497978, 2), round(-0.599586, 2), round(-0.419021, 2), round(-0.465764, 2)),
        2: (round(0.526215, 2), round(-0.625533, 2), round(-0.380668, 2), round(-0.432317, 2)),
        3: (round(0.528514, 2), round(-0.625921, 2), round(-0.373003, 2), round(-0.43562, 2)),
        4: (round(0.666464, 2), round(-0.722384, 2), round(-0.072327, 2), round(-0.169576, 2)),
    }

    @classmethod
    @print_start_and_end(string='КСО: включить')
    def on(cls):
        if cls.cur is not None:
            raise Exception('КСО уже включен!')
        cls.cur = True  # или определить какой включится
        sendFromJson(SCPICMD, 0xE114, AsciiHex('0x4400 0000 0000 0000'), describe='Отключить ЦНФ')  # Отключить ЦНФ
        sendFromJson(SCPICMD, 0xE004, AsciiHex('0x0209 0000 0000 0000'))  # Включить КСО + обмен
        bprint(':::Ждем 60 сек 00.01.ARO == 15200 ')
        if not Ex.wait('ТМИ', '{00.01.ARO.НЕКАЛИБР} == 15200', 60):  # ждем КСО включился
            rprint('00.01.ARO == 15200')
            inputG('00.01.ARO не == 15200')
        else:
            gprint('00.01.ARO == 15200')
        sendFromJson(SCPICMD, 0x0082, AsciiHex('0x0100 0000'), describe='Фейк мод', pause=10)  # Фейк мод
        executeTMI("{00.01.fakeAocsMode}@H == 1")  # Ex.wait('ТМИ', '{00.01.fakeAocsMode} == 1', 10)
        sendFromJson(SCPICMD, 0x0064, AsciiHex('0x0300 0000'), describe='Перейти 2ЗКТ', pause=10)  # перейти в 2ЗКТ для ЗД
        executeTMI("{00.01.mode}@H == 1 and {00.01.submode}@H == 31")  # Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10)

        # первичный опрос ТМИ
        # prevLength = len(cls.di)
        # cls._get_tmi()  # опросить ТМИ
        # if prevLength != len(cls.di):
        #     raise Exception("Ошибка KSO._tmi")
        # cls._printTmi(cls.di)

    @classmethod
    @print_start_and_end(string='КСО: отключить')
    def off(cls):
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0001 0000'))  # Установка статусов отказа для устройств БИУС1
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0101 0000'))  # БИУС2
        sendFromJson(SCPICMD, 0x006E, AsciiHex('0x8100 0000'))  # Установка режима управления ДМ
        sendFromJson(SCPICMD, 0x0071)   # Остановка всех ДМ
        sleep(10)                       # пауза на остановку ДМ
        BCK.clc_BCK()
        BCK.downBCK()
        bprint('Ждем остановки ДМ 60 сек')
        if not Ex.wait('{00.02.MeasuredSpeed1.НЕКАЛИБР} < 10 and {00.02.MeasuredSpeed2.НЕКАЛИБР} < 10 and '
                       '{00.02.MeasuredSpeed3.НЕКАЛИБР} < 10 and {00.02.MeasuredSpeed4.НЕКАЛИБР} < 10', 60):
            rprint('ДМ не остановлен')
            inputG('ДМ не остановлен')
        else:
            gprint('ДМ остновлен')
        sendFromJson(SCPICMD, 0x53F1)  # Отключить КСО

        cls.cur = None
        for key in cls.di.keys():
            cls.di[key] = []

        BCK.clc_BCK()
        BCK.downBCK()
        if executeTMI("{05.01.beKSOA2}@H==0")[0]:  # == 1 Состояние коммутатора КСО Коммутатор А Ключевой элемент 2
            executeTMI(
                ' and '.join(("{05.02.VKSOA}@H<10",  # Напряжение канала коммутатора КСО Коммутатор А Ключевой элемент 1
                              "{05.02.CKSOA}@H<4")))  # Ток коммутатора КСО Коммутатор А Ключевой элемент 2
            sendFromJson(SCPICMD, 0x53ED)  # Остановка БИУС1
            sendFromJson(SCPICMD, 0x53EE)  # Остановка БИУС1
            sendFromJson(SCPICMD, 0x53E9)  # Остановка ММ
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0000 0000'))  # Остановка ЗД1
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0100 0000'))  # Остановка ЗД2
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0200 0000'))  # Остановка ЗД3
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0300 0000'))  # Остановка ЗД4
            sendFromJson(SCPICMD, 0x5401)  # Остановка ДМ1
            sendFromJson(SCPICMD, 0x5402)  # Остановка ДМ2
            sendFromJson(SCPICMD, 0x5403)  # Остановка ДМ3
            sendFromJson(SCPICMD, 0x5404)  # Остановка ДМ4
        else:
            rprint("КСО КСО ЗАМКНУТ")
            inputG()

    @classmethod
    @print_start_and_end(string='КСО: опросить ТМИ')
    def get_tmi(cls):
        """Получить тми и вывод"""
        prevLength = len(cls.di)
        cls._get_tmi()  # опросить ТМИ
        if prevLength != len(cls.di):
            raise Exception("Ошибка KSO._tmi")
        cls._printTmi(cls.di)

    @classmethod
    def _get_tmi(cls):
        if KSO.cur is None:
            raise Exception("КСО должен быть включен")

        # проверить секундную от АСН, что меняется в КСО счетчи
        res, values = executeTMI(doEquation('00.01.PPS1', '@H', ref_val='@unsame') + " or " +
                                 doEquation('00.01.PPS2', '@H', ref_val='@unsame'), count=2, period=8, stopFalse=False)
        if res:
            gprint('Есть секундная метка от АСН')
        else:
            rprint('Не изменяется секундная метка от АСН')
            inputG('Не изменяется секундная метка от АСН')

        # Сброс БЦК чтобы опросить занчения БИУС
        BCK.clc_BCK()
        BCK.downBCK()
        # Опрос ММ1, 2ДС, 2БИУС
        tmi = Ex.get('ТМИ', {"00.02.Sat_Bx": 'КАЛИБР',
                             "00.02.Sat_By": 'КАЛИБР',
                             "00.02.Sat_Bz": 'КАЛИБР',
                             "00.01.FT1_FD1": 'НЕКАЛИБР',
                             "00.01.FT1_FD2": 'НЕКАЛИБР',
                             "00.01.FT1_FD3": 'НЕКАЛИБР',
                             "00.01.FT1_FD4": 'НЕКАЛИБР',
                             "00.01.FT2_FD1": 'НЕКАЛИБР',
                             "00.01.FT2_FD2": 'НЕКАЛИБР',
                             "00.01.FT2_FD3": 'НЕКАЛИБР',
                             "00.01.FT2_FD4": 'НЕКАЛИБР',
                             "00.05.BIUS1MeasX": 'КАЛИБР',
                             "00.05.BIUS1MeasY": 'КАЛИБР',
                             "00.05.BIUS1MeasZ": 'КАЛИБР',
                             "00.05.BIUS2MeasX": 'КАЛИБР',
                             "00.05.BIUS2MeasY": 'КАЛИБР',
                             "00.05.BIUS2MeasZ": 'КАЛИБР'}, None)

        # переключить ММ, опросить, добавить доп значения в словарь
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0201 0000'), pause=10)  # Отказ ММ1
        sleep(10)  # пауза на переключение
        mm2 = Ex.get('ТМИ', {"00.02.Sat_Bx": 'КАЛИБР',
                             "00.02.Sat_By": 'КАЛИБР',
                             "00.02.Sat_Bz": 'КАЛИБР'}, None)
        for item in mm2.items():
            tmi[item[0] + '_2'] = item[1]
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0200 0000'), pause=1)  # Сброс отказ ММ1
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0301 0000'), pause=1)  # отказ ММ2

        # Звездники работают только в режиме 0x0065(0x1F00 0000)- подрежим ориентации (штатая ориентация)
        if not Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10):
            sendFromJson(SCPICMD, 0x0065, AsciiHex('0x1F00 0000'))  # задать штатный режим ориентации
            Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10)
        zd = {}
        for x in range(0, 4):
            zd['00.08.Q_ST%s_0' % (x + 1)] = 'КАЛИБР'
            zd['00.08.Q_ST%s_1' % (x + 1)] = 'КАЛИБР'
            zd['00.08.Q_ST%s_2' % (x + 1)] = 'КАЛИБР'
            zd['00.08.Q_ST%s_3' % (x + 1)] = 'КАЛИБР'
        zd = Ex.get('ТМИ', zd, None)
        for item in zd.items():
            tmi[item[0]] = round(item[1], 2) if item[1] is not None else 'None'

        # заменяем значения
        for item in tmi.items():
            cls.di[item[0]].append(item[1])

    @classmethod
    def _printTmi(cls, tmi, twoVals=False):
        """Вывод словаря тми, или сопоставить два одинаковых словаря"""
        ar = []
        for item in tmi.items():
            if twoVals is True:
                columns = item[1][-2]
            else:
                columns = item[1]
            for index, x in enumerate(columns):
                if not isinstance(x, str):
                    columns[index] = str(x)
            ar.append([item[0] + ':', *columns])
        string = tabulate(ar, tablefmt='simple')
        print(string.strip('- \n'))
