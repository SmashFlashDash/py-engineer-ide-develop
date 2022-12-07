from engineers_src.Devices.Device import Device
from engineers_src.Devices.BCK import BCK
from engineers_src.Devices.dictionariesUVDI import *
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


forma = "%-20s --> %s"  # вывод шифр --> значение


class ASN(Device):
    cur = None

    @classmethod
    @print_start_and_end(string='АСН: включить')
    def on(cls, num):
        if cls.cur is not None:
            raise Exception('АСН-%s уже включен!' % cls.cur)
        cls.log('Включить', num)
        if num == 1:
            # sendFromJson(SCPICMD, 0x4005, pause=1)   # Вкл АСН1 через канал 5
            # sendFromJson(SCPICMD, 0xE219, pause=1)   # Вкл обмен АСН1
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0106010000000000'), pause=1)  # Включить АСН1
            # sendFromJson(SCPICMD, 0xE22D, pause=1)  # Выключить приоритет АСН2
            # sendFromJson(SCPICMD, 0xE22C, pause=1)  # Включить приоритет АСН1  # или 0xE242 ПРОВЕРИТЬ
        elif num == 2:
            # sendFromJson(SCPICMD, 0x4195, pause=1)  # Вкл АСН2 через канал 6
            # sendFromJson(SCPICMD, 0xE230, pause=1)  # Вкл обмен АСН2
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0109000000000000'), pause=1)  # Включить АСН2
            # sendFromJson(SCPICMD, 0xE22D, pause=1)  # Выключить приоритет АСН1
            # sendFromJson(SCPICMD, 0xE243, pause=1)  # Включить приоритет АСН2
        else:
            raise Exception('Номер блока только 1 и 2')
        cls.cur = num
        # cls.res_control()

    @classmethod
    @print_start_and_end(string='АСН: отключить')
    def off(cls, num):
        """Отключение АСН"""
        cls.log('Отключить', num)
        syst_num = cls.__get_syst_num(num)
        if num == 1:
            print("УВ: Отключить обмены с АСН1")
            # sendFromJson(SCPICMD, 0xE21A, pause=1)  # Отключить обмены с АСН1 0xE21A EXCH_OFF_ASN1
            sendFromJson(SCPICMD, 0xE005, AsciiHex('0106000000000000'), pause=1)  # Отключить АСН1
        else:
            print("УВ: Отключить обмены с АСН2")
            # sendFromJson(SCPICMD, 0xE231, pause=1)  # Отключить обмены с АСН1 0xE21A EXCH_OFF_ASN1
            sendFromJson(SCPICMD, 0xE005, AsciiHex('0109000000000000'), pause=1)  # Отключить АСН2
        # sendFromJson(SCPICMD, 0x43ED, pause=1)   # Отключить АСН  (Каналы 5 и 6)
        inputG('Проверь что АСН отключен')
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        cls.__unrealized__()

    @staticmethod
    def __get_syst_num(num):
        syst_num = {1: 11, 2: 12}.get(num)
        if syst_num is None:
            raise Exception('Неверный параметр')
        return syst_num

    @classmethod
    @print_start_and_end(string='АСН: проверка результатов самоконтроля асн')
    def res_control(cls):
        """Проверка результатов самоконтроля АСН"""
        if cls.cur is None:
            raise Exception('Необходимо включить АСН для контроля')
        num = cls.cur
        syst_num = cls.__get_syst_num(cls.cur)
        SS = ad_dict_SS(syst_num)
        DI_2 = ad_dict_DI_2(syst_num)
        DI_3 = ad_dict_DI_3(syst_num)
        DI_4 = ad_dict_DI_4(syst_num)
        DI_10 = ad_dict_DI_10(syst_num)
        control_result = Ex.get('ТМИ', SS["ResControl"], 'КАЛИБР ТЕКУЩ')
        failure_flag = Ex.get('ТМИ', SS["FailureFlag"], 'КАЛИБР ТЕКУЩ')
        state_ASN = Ex.get('ТМИ', SS["PrgStateSvUS"], 'КАЛИБР ТЕКУЩ')
        state_PN = Ex.get('ТМИ', SS["PrgStateSvPN"], 'КАЛИБР ТЕКУЩ')
        if control_result == 'АСН исправна' and failure_flag == "сбои не зафиксированы":
            # Достаточно считать 5 основных параметров самоконтроля и режимов работы УС и ПН
            tprint(forma % (
            'Суммарный результат контроля АСН', Text.green + 'АСН исправна, сбои не зафиксированы') + Text.default)
            keys = list(SS.keys())  # список шифров
            for cypher in keys[0:5]:
                tprint(forma % (cypher, Ex.get('ТМИ', SS[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
        elif control_result == 'АСН неисправна':
            # 	Неисправным называется такое состояние аппаратной части, при котором АСН в состоянии выполнять
            #   основные функции, но с некоторым ухудшением требуемых характеристик
            bprint("Суммарный результат контроля АСН: %s" % control_result)
            tprint("Наличие сбоев в процессе тестирования: %s" % failure_flag)
            tprint("Программное состояние АСН (СВ УС): %s" % state_ASN)
            tprint("Программное состояние АСН (СВ ПН): %s" % state_PN)
            BCK.clcBCK()
            cls.__di_form(num, 2)  # Запрос ДИ2 АСН
            cls.__di_form(num, 3)  # Запрос ДИ3 АСН
            sleep(20)
            BCK.downBCK()
            for cypher in tuple(DI_2.keys())[0:-20]:  # Вывод расширенных результатов самоконтроля АСН (96 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_2[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_3.keys())[0:-3]:  # Описание сбоев АСН (43 параметра)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_3[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_4.keys())[0:8]:  # Описание сбоев АСН. Продолжение (8 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_4[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
        elif control_result == 'отказ-ПН':
            bprint('Произошел отказ ПН. АСН может использоваться только как источник МВ, управляемой по УВ')
            for cypher in tuple(DI_2.keys())[5:9] + tuple(DI_2.keys())[31:-20]:
                # Вывод расширенных результатов самоконтроля АСН (96 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_2[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_3.keys())[0:-3]:  # Описание сбоев АСН (43 параметра)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_3[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_4.keys())[0:8]:  # Описание сбоев АСН. Продолжение (8 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_4[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            AN_mode = Ex.get('ТМИ', DI_10["ASN_Mode"], 'НЕКАЛИБР ТЕКУЩ')
            print('АСН в режиме "Автономная навигация"' if AN_mode == 101 else
                  'АСН не переведена в режим "Автономная навигация"\nТекущий режим работы АСН: ' + AN_mode)
        else:
            bprint('Произошел отказ АСН (критическое нарушение в УС)', tab=1)
            for cypher in tuple(DI_2.keys())[9:31]:
                tprint(forma % (cypher, Ex.get('ТМИ', DI_2[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_3.keys())[0:-3]:
                tprint(forma % (cypher, Ex.get('ТМИ', DI_3[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_4.keys())[0:8]:
                tprint(forma % (cypher, Ex.get('ТМИ', DI_4[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)

    @staticmethod
    def __di_form(block_num, di_num):
        """Функция формирования (заполнения) ИОКов АСН из запрашиваемых ПА и их запрос"""

        def out_single_asn(asciihex):
            for i in range(0, 2):
                sendFromJson(SCPICMD, UV["OUT_SINGLE_ASN" + str(block_num)], AsciiHex(asciihex))

        if di_num == 2:
            bprint('Запрос ДИ-2: ПА1 "РезКонтроль" и ПА2 "ГотВывод" --- АСН' + str(block_num))
            out_single_asn('0x0100 0000 0000 0000')  # Запрос одноразовой выдачи ПА1
            sendFromJson(SCPICMD, UV["TLM2_ASN" + str(block_num)])  # Запрос ДИ2 АСН
        elif di_num == 3:
            bprint('Запрос ДИ-3: ПА3 "ТлмРабота" (ИСД1…ИСД25) и ПА=22, ДН=11 "ВыводДвиж" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)],
                         AsciiHex('0x0200 031C 0000 0000'))  # Периодический запрос ПА3 с выдачей по изменению
            out_single_asn('0x7601 0000 0000 0000')  # Запрос одноразовой выдачи ПА22 ДН11
            sendFromJson(SCPICMD, UV["TLM3_ASN" + str(block_num)], AsciiHex('0x0200 031C 0000 0000'))  # Запрос ДИ3 АСН
        elif di_num == 4:
            bprint(
                'Запрос ДИ-4: ПА3 "ТлмРабота" (ИСД26…ИСД30), ПА=4 "ДаНетВвод", ПА=6 "ПриемСНП", ПА=13, ДН=4 "ТекВывод" --- АСН' + str(
                    block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)],
                         AsciiHex('0x0200 031C 0000 0000'))  # Периодический запрос ПА3 с выдачей по изменению
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)],
                         AsciiHex('0x0200 041C 0000 0000'))  # Периодический запрос ПА4 с выдачей по изменению
            out_single_asn('0x0600 0000 0000 0000')  # Запрос одноразовой выдачи ПА6
            out_single_asn('0x8D00 0000 0000 0000')  # Запрос одноразовой выдачи ПА13 ДН4
            sendFromJson(SCPICMD, UV["TLM4_ASN" + str(block_num)])  # Запрос ДИ4 АСН
        elif di_num == 5:
            bprint('Запрос ДИ-5: ПА=5, ДН=10 "ВыводПарам" и  ПА=12, ДН=5 "ТекРежим" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex(
                '0x0200 451D 0000 0000'))  # Периодический запрос ПА5 ДН10 с выдачей по изменению  (вывод 1 раз в 10 секунд)
            out_single_asn('0xAC00 0000 0000 0000')  # Запрос одноразовой выдачи ПА12 ДН5
            sendFromJson(SCPICMD, UV["TLM5_ASN" + str(block_num)])  # Запрос ДИ5 АСН
        elif di_num == 6:
            bprint(
                'Запрос ДИ-6: ПА=22, ДН=5 "ВыводДвиж", ПА=22, ДН=10 "ВыводДвиж", ПА=12, ДН=3 "ТекРежим" --- АСН' + str(
                    block_num))
            out_single_asn('0xB600 0000 0000 0000')  # Запрос одноразовой выдачи ПА22 ДН5
            out_single_asn('0x5601 0000 0000 0000')  # Запрос одноразовой выдачи ПА22 ДН10
            out_single_asn('0x06C0 0000 0000 0000')  # Запрос одноразовой выдачи ПА12 ДН3
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)],
                         AsciiHex('0x0200 451D 0000 0000'))  # Периодический запрос ПА5 ДН10 с выдачей по изменению
            sendFromJson(SCPICMD, UV["TLM6_ASN" + str(block_num)])  # Запрос ДИ6 АСН
        elif di_num == 7:
            bprint('Запрос ДИ-7: ПА=9 "КоордПолюс", ПА=24 "ОцифрШВ", ПА=5, ДН=8 "ВыводПарам" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex(
                '0x0200 0904 0000 0000'))  # Периодический запрос ПА9 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex(
                '0x0200 1804 0000 0000'))  # Периодический запрос ПА24 с периодом опроса 1 раз в секунду
            out_single_asn('0x0501 0000 0000 0000')  # Запрос одноразовой выдачи ПА5 ДН8
            sendFromJson(SCPICMD, UV["TLM7_ASN" + str(block_num)])  # Запрос ДИ7 АСН
        elif di_num == 8:
            bprint('Запрос ДИ-8: ПА=5, ДН=2 "ВыводПарам" и ПА=5, ДН=6 "ВыводПарам" --- АСН' + str(block_num))
            out_single_asn('0x4500 0000 0000 0000')  # Запрос одноразовой выдачи ПА5 ДН2
            out_single_asn('0xC500 0000 0000 0000')  # Запрос одноразовой выдачи П5 ДН6
            sendFromJson(SCPICMD, UV["TLM8_ASN" + str(block_num)])  # Запрос ДИ8 АСН
        elif di_num == 9:
            bprint('Запрос ДИ-9: ПА=5, ДН=7 "ВыводПарам" --- АСН' + str(block_num))
            out_single_asn('0xE500 0000 0000 0000')  # Запрос одноразовой выдачи ПА5 ДН7
            sendFromJson(SCPICMD, UV["TLM9_ASN" + str(block_num)])  # Запрос ДИ9 АСН
        elif di_num == 10:
            bprint(
                'Запрос ДИ-10: ПА=5, ДН=5 "ВыводПарам", ПА=12, ДН=2 "ТекРежим",  ПА=12, ДН=1 "ТекРежим" --- АСН' + str(
                    block_num))
            out_single_asn('0xA500 0000 0000 0000')  # Запрос одноразовой выдачи ПА5 ДН5
            out_single_asn('0x2C00 0000 0000 0000')  # Запрос одноразовой выдачи ПА12 ДН1
            out_single_asn('0x4C00 0000 0000 0000')  # Запрос одноразовой выдачи ПА12 ДН2
            sendFromJson(SCPICMD, UV["TLM10_ASN" + str(block_num)])  # Запрос ДИ10 АСН
        elif di_num == 11:
            bprint('Запрос ДИ-11: ПА=19, ДН=1 "КСВЧобщее" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex(
                '0x0200 3304 0000 0000'))  # Периодический запрос ПА19 ДН1 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["TLM11_ASN" + str(block_num)])  # Запрос ДИ11 АСН
        elif di_num == 12:
            bprint('Запрос ДИ-12: ПА=19, ДН=1 "КСВЧобщее" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex(
                '0x0200 3304 0000 0000'))  # Периодический запрос ПА19 ДН1 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["TLM12_ASN" + str(block_num)])  # Запрос ДИ12 АСН
        elif di_num == 13:
            bprint('Запрос ДИ-13: ПА18 "УслМгнКСВЧ" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex(
                '0x0200 1204 0000 0000'))  # Периодический запрос ПА18 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["TLM13_ASN" + str(block_num)])  # Запрос ДИ12 АСН
        else:
            raise Exception('Некорректный номер ДИ')
        return

    @classmethod
    @print_start_and_end(string='АСН: проверка выдачи см в бцк %s')
    def check_sm_output(cls):
        """Функция проверки корректной выдачи СМ из АСН"""
        if ASN.cur is None:
            raise Exception('Для провеки необходимо включить АСН!')
        num = cls.cur
        syst_num = cls.__get_syst_num(num)
        cls.__KSVCH_check(syst_num)
        DI_7 = ad_dict_DI_7(syst_num)
        confirm_MV = Ex.get('ТМИ', DI_7["ConfirmMV"], 'КАЛИБР ТЕКУЩ')
        bprint('Подтверждение выдачи импульса МВ: %s' % confirm_MV)
        controlGet(confirm_MV, 'импульс МВ выведен',
                   text=('', 'Проверьте, что на Имитаторе К2-100 запущен сценарий имитации!'))

    @classmethod
    def __KSVCH_check(cls, syst_num):
        """Функция проверки достоверности КСВЧ-решения"""
        DI_7 = ad_dict_DI_7(syst_num)
        DI_13 = ad_dict_DI_13(syst_num)
        Valid_KSVCh = Ex.get('ТМИ', DI_13["ValidKSVCh"], 'КАЛИБР ТЕКУЩ')
        bprint('Достоверность координатно-скоростного решения: %s' % Valid_KSVCh)
        for cypher in tuple(DI_7.keys())[15:19]:
            tprint(forma % (cypher, Ex.get('ТМИ', DI_7[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
        controlGet(Valid_KSVCh, 'решение достоверно')



