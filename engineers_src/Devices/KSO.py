from engineers_src.Devices.Device import Device
from engineers_src.Devices.BCK import BCK
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, executeWaitTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, config, AsciiHex, KPA, SOTC, SKPA, Ex, sleep
from lib.tabulate.tabulate import tabulate
from copy import deepcopy


class KSO(Device):
    cur = None
    di_range = config.odict()
    di = config.odict(('00.01.PPS1', []), ('00.01.PPS2', []),
                      ('00.02.Sat_Bx', []), ('00.02.Sat_By', []), ('00.02.Sat_Bz', []),
                      ('00.02.Sat_Bx_2', []), ('00.02.Sat_By_2', []), ('00.02.Sat_Bz_2', []),
                      # ('00.01.FT1_FD1', []), ('00.01.FT1_FD2', []), ('00.01.FT1_FD3', []), ('00.01.FT1_FD4', []),
                      # ('00.01.FT2_FD1', []), ('00.01.FT2_FD2', []), ('00.01.FT2_FD3', []), ('00.01.FT2_FD4', []),
                      ('00.05.BIUS1MeasX', []), ('00.05.BIUS1MeasY', []), ('00.05.BIUS1MeasZ', []),
                      ('00.05.BIUS2MeasX', []), ('00.05.BIUS2MeasY', []), ('00.05.BIUS2MeasZ', []),
                      # ("00.08.Q_ST1_0", [],), ("00.08.Q_ST1_1", [],), ("00.08.Q_ST1_2", [],), ("00.08.Q_ST1_3", [],),
                      # ("00.08.Q_ST2_0", [],), ("00.08.Q_ST2_1", [],), ("00.08.Q_ST2_2", [],), ("00.08.Q_ST2_3", [],),
                      # ("00.08.Q_ST3_0", [],), ("00.08.Q_ST3_1", [],), ("00.08.Q_ST3_2", [],), ("00.08.Q_ST3_3", [],),
                      # ("00.08.Q_ST4_0", [],), ("00.08.Q_ST4_1", [],), ("00.08.Q_ST4_2", [],), ("00.08.Q_ST4_3", [],)
                      )
    __di_list = [
        # {"00.01.FT1_FD1": 'НЕКАЛИБР',
        # "00.01.FT1_FD2": 'НЕКАЛИБР',
        # "00.01.FT1_FD3": 'НЕКАЛИБР',
        # "00.01.FT1_FD4": 'НЕКАЛИБР',
        # "00.01.FT2_FD1": 'НЕКАЛИБР',
        # "00.01.FT2_FD2": 'НЕКАЛИБР',
        # "00.01.FT2_FD3": 'НЕКАЛИБР',
        # "00.01.FT2_FD4": 'НЕКАЛИБР'},
        {"00.05.BIUS1MeasX": 'КАЛИБР',
         "00.05.BIUS1MeasY": 'КАЛИБР',
         "00.05.BIUS1MeasZ": 'КАЛИБР',
         "00.05.BIUS2MeasX": 'КАЛИБР',
         "00.05.BIUS2MeasY": 'КАЛИБР',
         "00.05.BIUS2MeasZ": 'КАЛИБР'},
        {"00.02.Sat_Bx": 'КАЛИБР',
         "00.02.Sat_By": 'КАЛИБР',
         "00.02.Sat_Bz": 'КАЛИБР'},
        # {'00.08.Q_ST1_0': 'КАЛИБР',
        #  '00.08.Q_ST1_1': 'КАЛИБР',
        #  '00.08.Q_ST1_2': 'КАЛИБР',
        #  '00.08.Q_ST1_3': 'КАЛИБР',
        #  '00.08.Q_ST2_0': 'КАЛИБР',
        #  '00.08.Q_ST2_1': 'КАЛИБР',
        #  '00.08.Q_ST2_2': 'КАЛИБР',
        #  '00.08.Q_ST2_3': 'КАЛИБР',
        #  '00.08.Q_ST3_0': 'КАЛИБР',
        #  '00.08.Q_ST3_1': 'КАЛИБР',
        #  '00.08.Q_ST3_2': 'КАЛИБР',
        #  '00.08.Q_ST3_3': 'КАЛИБР',
        #  '00.08.Q_ST4_0': 'КАЛИБР',
        #  '00.08.Q_ST4_1': 'КАЛИБР',
        #  '00.08.Q_ST4_2': 'КАЛИБР',
        #  '00.08.Q_ST4_3': 'КАЛИБР'}
    ]
    quaternions = {
        1: (round(0.497978, 2), round(-0.599586, 2), round(-0.419021, 2), round(-0.465764, 2)),
        2: (round(0.526215, 2), round(-0.625533, 2), round(-0.380668, 2), round(-0.432317, 2)),
        3: (round(0.528514, 2), round(-0.625921, 2), round(-0.373003, 2), round(-0.43562, 2)),
        4: (round(0.666464, 2), round(-0.722384, 2), round(-0.072327, 2), round(-0.169576, 2)),
    }

    # TODO: сменить на Ex.wait
    @classmethod
    @print_start_and_end(string='КСО: включить')
    def on(cls, ask_TMI=True):
        if cls.cur is not None:
            raise Exception('КСО уже включен!')
        cls.log('Включить')
        cls.cur = True  # или определить какой включится
        # sendFromJson(SCPICMD, 0xE114, AsciiHex('0x4400 0000 0000 0000'), describe='Отключить ЦНФ')  # Отключить ЦНФ
        sendFromJson(SCPICMD, 0xE004, AsciiHex('0x0209 0000 0000 0000'))  # Включить КСО + обмен
        bprint(':::Ждем 60 сек 00.01.ARO == 15200 ')
        # if not Ex.wait('ТМИ', '{00.01.ARO.НЕКАЛИБР} == 15200', 60):  # ждем КСО включился
        #     rprint('00.01.ARO == 15200')
        #     inputG('00.01.ARO не == 15200')
        # else:
        #     gprint('00.01.ARO == 15200')
        executeWaitTMI("{00.01.fakeAocsMode}@H == 1", 60)
        sendFromJson(SCPICMD, 0x0082, AsciiHex('0x0100 0000'), describe='Фейк мод')  # Фейк мод
        # executeTMI("{00.01.fakeAocsMode}@H == 1")  # Ex.wait('ТМИ', '{00.01.fakeAocsMode} == 1', 10)
        executeWaitTMI("{00.01.fakeAocsMode}@H == 1", 20)
        sendFromJson(SCPICMD, 0x0064, AsciiHex('0x0300 0000'), describe='Перейти 2ЗКТ')  # перейти в 2ЗКТ для ЗД
        # executeTMI("{00.01.mode}@H == 3 and {00.01.submode}@H == 31")  # Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10)
        executeWaitTMI("{00.01.mode}@H == 3 and {00.01.submode}@H == 31", 20)
        # первичный опрос ТМИ
        # if ask_TMI:
        #     prevLength = len(cls.di)
        #     cls._get_tmi()  # опросить ТМИ
        #     if prevLength != len(cls.di):
        #         raise Exception("Ошибка KSO._tmi")
        #     cls._printTmi(cls.di)

    @classmethod
    @print_start_and_end(string='КСО: отключить')
    def off(cls, ask_TMI=True):
        cls.log('Отключить')
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0001 0000'))  # Установка статусов отказа для устройств БИУС1
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0101 0000'))  # БИУС2
        sendFromJson(SCPICMD, 0x006E, AsciiHex('0x8100 0000'))  # Установка режима управления ДМ
        sendFromJson(SCPICMD, 0x0071)   # Остановка всех ДМ
        sleep(10)                       # пауза на остановку ДМ
        BCK.clcBCK()
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
        cls.clear_tmi()
        BCK.downBCK(pause=20)
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
        # if ask_TMI:
        #     pass

    @classmethod
    @print_start_and_end(string='КСО: очистить словарь ДИ')
    def clear_tmi(cls):
        """Очистить словари ди"""
        for key in cls.di.keys():
            cls.di[key] = []

    @classmethod
    @print_start_and_end(string='КСО: сменить ММ')
    def set_MM(cls, num, ask_TMI=True):
        if num == 1:
            sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0201 0000'), pause=10)  # Отказ ММ1
            sleep(10)  # пауза на переключение
        elif num == 2:
            sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0301 0000'), pause=1)  # отказ ММ2
            sleep(10)
            sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0200 0000'), pause=1)  # Сброс отказ ММ1
            sendFromJson(SCPICMD, 0x0084, AsciiHex('0x0602 0000'), pause=1)  # ММ пнуть
        else:
            raise Exception('Номер ММ1 или ММ2')
        if ask_TMI:
            pass

    @classmethod
    def init_di(cls):
        """обновить id di из postgre в redis чтобы запрашивать Ex.get ИНТРЕВАЛ"""
        values = {}
        for x in cls.__di_list:
            values.update(**x)
        Ex.get('ТМИ', values, 'КАЛИБР ТЕКУЩ')

    @classmethod
    @print_start_and_end(string='КСО: опросить ТМИ')
    def get_tmi(cls, isInterval=None):
        prevLength = len(cls.di)
        if isInterval is None:
            cls._get_tmi()  # опросить ТМИ
        else:
            cls._get_tmi(isInterval='ИНТЕРВАЛ')
            # записать в di_range min max числа
            for x in cls.di.items():
                vals = [z for z in x[1] if z is not None]   # убрать None из значения
                if len(vals) == 0:
                    cls.di_range[x[0]] = None
                else:
                    cls.di_range[x[0]] = [min(vals), max(vals)]
        if prevLength != len(cls.di):
            raise Exception("Ошибка KSO._tmi")
        cls._printTmi(cls.di)

    @classmethod
    def get_tmi_and_compare(cls):
        cls.__unrealized__()
        # """Получить ди и сравнить с диапазоном cls.di если там не пустые диапазон
        # переделать diRange в список и кинуть в табулет"""
        # # TODO: можно сделать функцию для расчетам массивов труе фалс и цвета, и кидать это в tabulate
        # to_tabulate = []
        # for key, vals in cls.di_range.items():
        #     row = []
        #     to_tabulate.append(row)
        #     row.append(key)
        #     if vals is None:
        #         row.append(str(None))
        #     else:
        #         vals = [str(x) for x in vals]
        #         row.extend(vals)
        # string = tabulate(to_tabulate, tablefmt='simple')
        # print(string.strip('- \n'))


    # @classmethod
    # @print_start_and_end(string='КСО: опросить ТМИ и сравнить')
    # def get_tmi_and_compare(cls):
    #     cls._get_tmi()  # опросить ТМИ
    #     text = []
    #     bools = []
    #     for key, vals in cls.di.items():
    #         # берем значеие в di если нет то кидаем None и закинем None в основной res
    #         rowText = [cls.di_range[key][0] + ' <= {' + key + '} <= ' + cls.di_range[key][1] + ':']
    #         rowBools = []
    #         text.append(rowText)
    #         bools.append(rowBools)
    #         for index, x in enumerate(vals):
    #             rowBools.append(eval('%s <= %s <= %s' % (cls.di_range[key][0], x, cls.di_range[key][1])))
    #             rowText.append(x)
    #         if len(rowBools) == 0:
    #             rowBools.append(None)
    #         else:
    #             rowBools.insert(all(True), 0)
        # string = tabulate(ar, tablefmt='simple')
        # print(string.strip('- \n'))
        # print('')


    @classmethod
    def _get_tmi(cls, isInterval=None):
        if KSO.cur is None:
            raise Exception("КСО должен быть включен")
        # проверить секундную от АСН, что меняется в КСО счетчи
        res = executeTMI(doEquation('00.01.PPS1', '@H', ref_val='@unsame') + " or " +
                         doEquation('00.01.PPS2', '@H', ref_val='@unsame'), count=2, stopFalse=False)[0]
        if res:
            gprint('Есть секундная метка от АСН')
        else:
            rprint('Не изменяется секундная метка от АСН')
            res = inputGG(btnsList=["Продолжить", "Отменить"], title='Не изменяется секундная метка от АСН')
            if res == 'Отменить':
                return
        # Сброс БЦК чтобы опросить занчения БИУС
        BCK.downBCK(pause=20)
        if isInterval:
            values = {}
            for x in cls.__di_list:
                values.update(**x)
            tmi = Ex.get('ТМИ', values, isInterval)
            # TODO: узать текущий ММ нужен шифр
            length = len(tmi["00.02.Sat_Bx"])
            for x in cls.__di_list[1].keys():
                tmi[x + '_2'] = [None] * length
            ''''# опрос ЗД
            for key in cls.__di_list[2].keys():
                rounded = []
                for value in tmi[key]:
                    if value is None or isinstance(value, str):
                        rprint('%s - %s Значение нельзя округлить' % (key, value))
                        rounded.append('Err')
                        continue
                    rounded.append(round(value, 2))
                tmi[key] = rounded'''
        else:
            tmi = Ex.get('ТМИ', {**cls.__di_list[0], **cls.__di_list[1]}, None)     # Опрос ММ1, 2ДС, 2БИУС
            # ММ2
            cls.set_MM(2, ask_TMI=False)
            mm2 = Ex.get('ТМИ', cls.__di_list[1], None)
            for item in mm2.items():
                tmi[item[0] + '_2'] = item[1]
            cls.set_MM(1, ask_TMI=False)
            # sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0201 0000'), pause=10)  # Отказ ММ1
            # sleep(10)  # пауза на переключение
            # mm2 = Ex.get('ТМИ', cls.__di_list[1], None)
            # for item in mm2.items():
            #     tmi[item[0] + '_2'] = item[1]
            # sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0301 0000'), pause=1)  # отказ ММ2
            # sleep(10)
            # sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0200 0000'), pause=1)  # Сброс отказ ММ1
            # sendFromJson(SCPICMD, 0x0084, AsciiHex('0x0602 0000'), pause=1)  # ММ2 пнуть
            '''# Звездники работают только в режиме 0x0065(0x1F00 0000)- подрежим ориентации (штатая ориентация)
            if not Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10):
                sendFromJson(SCPICMD, 0x0065, AsciiHex('0x1F00 0000'))  # задать штатный режим ориентации
                if not Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10):
                    inputG('Не выставлен режим 2ЗКТ, не опросить ЗД.\nПопробуй вручную')
            zd = Ex.get('ТМИ', cls.__di_list[2], None)
            for item in zd.items():
                if item[1] is None or isinstance(item[1], str):
                    rprint('%s - %s Значение нельзя округлить' % (item[0], item[1]))
                    tmi[item[0]] = 'Err'
                    continue
                tmi[item[0]] = round(item[1], 2)'''

        # полученное записать в cls.di
        for item in tmi.items():
            if isinstance(item[1], (list, tuple)):
                cls.di[item[0]].extend(item[1])
            else:
                cls.di[item[0]].append(item[1])

    @classmethod
    def _printTmi(cls, tmi, twoVals=False):
        """Вывод словаря тми, или сопоставить два одинаковых словаря"""
        tmi = deepcopy(tmi)
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
