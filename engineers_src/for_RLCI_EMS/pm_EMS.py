"""
ИСП ЭМС
  - МКА полность собран, установлен на диэлектрическую подставку для БЭК ОМ67.91.22.000 и размещен на поворотном круге в БЭК1 так,
    чтобы его ось –Y была направлена на АИК; антенна АФУ-Х направлена в «зенит» в соответствии с ИВЯФ.464655.033РЭ и закреплена в этом положении
    с помощью приспособления для фиксация АФУ-Х ТАИК.301318.026 в соответствии с его ТАИК.410114.001 РЭ; разъемы Х3 и Х4 АФУ-Х расстыкованы;
    выполнить работы с АФУ Ku в соответствии с РЭ на БСК с тем, чтобы его диаграмма была направлена на АИК;
  - собрана схема Э6.2;
  - РМ включено согласно ОМ66.81.00.000 РЭ;
  - внешние ворота БЭК закрыты и прижаты;
  - МКА включен по ИЭ17.2 в следуещем варианте: питание от ИГБФ, БА КИС в ДР.

    ЭТАП1:
    - перевести БАКИС в СР
    - запустить функцию инит: установка текщего времени БШВ, включение КИР, КПДУ
    - включить АСН, КСО
    - КСО установить ММ2
    - проверить АСН кнопка: проверить КСВЧ
    - выполнить измерение УРКПА: кнопки - перевести БАРД в СР, Изм УР КПА
    - после измерения УРКПА на каждом БАКИС, записать измеренные урвоние в пременные в скрипте
    KIS.levels_kpa[1] = None
    KIS.levels_kpa[2] = None
    KIS.levels_kpa[3] = None
    KIS.levels_kpa[4] = None
    Просмотр уровней измерений кнопка: БАРЛ КПА вывод изм

    ЭТАП2 (при переводе КИС в СР установить из-ур мощности кнопка: БАРЛ КПА уст изм):
    - при включенном БАКИС, включить скрипт сброс РЛЦИ, при выполнении сброса
    запустить тест связи с КИС кнопка: БАРЛ тест связи, если тест прошел успешно, значит
    излучение РЛЦИ не влияет на КИС
    - повторить инстукцию с радиолинией БСК

    ЭТАП3 (при необходимости выполнить в ЭТАП2):
    - повторить инструкцю ЭТАП2, где вместо выполнения тест связи КИС, запустить тест АСН КСВЧ,
    смотерть ДИ: ММ, БИУС
    - запустить тест ПМ ДУК
    если пазуа между РИК менее 20 минут использовать разыне комплекты БК, в пм команды 0 или 2
    пример параметров вводимых в пм:
    (5 - 100 - 0 или 2 - 0 - 1 - 100)
"""
# DEBUG
from cpi_framework.utils.toolsForCPI import sec_diff
from time import sleep as sleep2
import time
time.sleep = lambda *args: sleep2(0)
sleep = lambda *args: sleep2(0)
# # Импорт зависимостей на винде
import sys
sys.path.insert(0, 'lib/')
from engineers_src.tools.tools import *
Ex.ivk_file_name = "script.ivkng"
Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"


import traceback
import logging
# Импорт с другой папки
# sys.path.insert(0, 'F:/VMShared/ivk-scripts/')  # путь к программе испытаний абсолютный
# DIstorage = None
# windowChooser = None
# sendFromJson = None
# doEquation = None
# executeTMI = None
# exec('from Dictionaries_UVDI import *')
# exec('from EMSRLCI_foos import windowChooser, sendFromJson, doEquation, executeTMI, getAndSleep, executeDI')

from engineers_src.tools.tools import ClassInput
def wrapInput(text):
   return input(text)
ClassInput.set(wrapInput)
from engineers_src.Devices.functions import windowChooser, sendFromJson, doEquation, executeTMI, print_start_and_end
from engineers_src.Devices.dictionariesUVDI import DIstorage
from engineers_src.Devices import BCK, M778, KIS, RLCI, ASN, Imitators, BSK_BSPA, BSK_P, BSK_KU, KSO
from engineers_src.Devices.DUK import DUK
from engineers_src.Devices.Device import LOGGER
from engineers_src.Devices.functions import DB
from engineers_src.Devices.mpz import launch as MPZlaunch
from engineers_src.Devices.bck_off import bck_rlci_off
from engineers_src.Devices.ku_ems import ku_mpz
from engineers_src.Devices.rlci_ems import rlci_mpz
from engineers_src.Devices.kdu_execute import launch as KDUExecute


##################### LOGGER ##################################
file_logger = logging.StreamHandler(open('engineers_src/for_RLCI_EMS/ems.log', 'a', encoding='UTF8'))
file_logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(bshv)s  - %(message)s'))
LOGGER.addHandler(file_logger)
# LOGGER.handlers[0].setStream(open('engineers_src/for_RLCI_EMS2/ems.log', 'a', encoding='UTF8'))
LOGGER.info('\n')
LOGGER.info('Начало скрипта ' + sys.argv[0])

##################### COMMUTATIONS ############################
DIstorage.commute('M778B', False)
# Кнопки опрос ДИ
btn_ask_di = False
# пауза на опросБД
DB.pause = 8
# паузы БЦК
BCK.clc_pause = 10
BCK.down_pause = 20
# уровние КИС
KIS.levels_kpa[1] = None
KIS.levels_kpa[2] = None
KIS.levels_kpa[3] = None
KIS.levels_kpa[4] = None
# Включенные блоки
KIS.cur = None
ASN.cur = []
KSO.cur = None
M778.cur = None
RLCI.EA332.cur = None
RLCI.EA331.cur = None
RLCI.PCH.cur = None
RLCI.FIP.cur = None
RLCI.MOD.cur = None
RLCI.UM.cur = None
BSK_BSPA.cur = None
BSK_P.cur = None
BSK_KU.cur = None


#####################    TESTS ###############################
def TEST_DESCRIPTION():
    print(Text.yellow + "БАРЛ ВСЕ МПРД" + Text.default + ": ИЗМЕРИТЬ МИНИМАЛЬНУЮ МОЩНОСТЬ КПА;")
    # Сначала настраиваем все комплекты КИС
    # потом включаем АСН и имитатор АСН, проверяем что есть решение KSVCH
    # включаем КСО, переводим в фейк режим, опрашиваем БИУС, ММ, ДС, ЗД, пров метку АСН
    # включаем РЛЦИ првоеряем КИС, АСН, КСО, РЛЦИ на КПА
    # включаем KU првоеряем КИС, АСН, КСО, РЛЦИ на КПА, KU
    # включаем P проверяем КИС, АСН, КСО, РЛЦИ на КПА, KU, P
    # включаем БСПА проверяем КИС, АСН, КСО, РЛЦИ на КПА, KU, P, БСПА


def TEST_senseKIS():
    """Тест настройки мощности КПА КИС
    входит в СР по очереди на разных БАРЛ, меняет мощност КПА к минимуму, проверяет прохождение команд"""
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ1', tab=2)
    KIS.on(1)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(10)
    KIS.off()
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ2', tab=2)
    KIS.on(2)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(10)
    KIS.off()
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ3', tab=2)
    KIS.on(3)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(10)
    KIS.off()
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ4', tab=2)
    KIS.on(4)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(10)
    KIS.off()
    comm_print("Полученные значения мощности:")
    KIS.print_BARL_levels()


def init():
    import datetime
    # Выставить время бцк, включить кир, кпду
    SCPICMD(0xE011,
            AsciiHex('0x' + sec_diff(datetime.datetime.now().isoformat(sep=':').replace('-', ':')[:-7])[0][2:] + '55'))
    sleep(1)
    SCPICMD(0xE004, AsciiHex('0x 010B 0000'))  # вкл КИР
    sleep(1)
    SCPICMD(0xE004, AsciiHex('0x 0109 0000'))  # вкл КПДУ
    sleep(1)
    SCPICMD(0x401D)  # вкл силовую КПДУ


def change_kis():
    """В автоматизированных тестах спрашивать о продлении или смене БАРЛ"""
    res = windowChooser(btnsText=('1', '2', '3', '4', 'Продлить сеанс'),
                        title='Сменить БАРЛ',
                        fooDict={'1': lambda: [x() for x in KIS.on(1)],
                                 '2': lambda: RLCI.on(2),
                                 '3': lambda: RLCI.on(2),
                                 '4': lambda: RLCI.on(2),
                                 'Продлить сеанс': lambda: RLCI.off()})
    if res == 'Продлить сеанс':
        KIS.__run_cmd('continue')
    else:
        KIS.off()
        sleep()
        KIS.on(int(res))


# TODO: надо ли включать M778Б для приема информаци
def Test_ASN_BARL(kis, asn):
    KIS.on(kis)
    KIS.set_KPA_level()
    inputG('Включи АСН К2')
    yprint('Включи АСН К2')
    ASN.on(asn)
    ASN.res_control()
    inputG('Проверить КИС АСН')
    KIS.get_tmi_conn_test()
    ASN.get_tmi()

    # включить КСО и проинитить обстановку опросив тми при выключенном всем
    change_kis()
    Imitators.on_imitators_DS()
    Imitators.on_imitators_ZD()
    KSO.on()
    KSO.get_tmi()
    KSO.clear_tmi()
    KIS.off()
    sleep(60)
    KIS.on(kis)
    KIS.set_KPA_level()
    KSO.get_tmi(isInterval=True)  # получим телеметрию когда КИС был выключен

    inputG('Проверить КИС АСН КСО')
    KSO.get_tmi()  # берем тут среднее значение
    KIS.get_tmi_conn_test()
    ASN.get_tmi()

    change_kis()
    RLCI.on(1, stop_shd=True)  # Вкл все блоки РЛЦИ
    inputG('Проверить КИС АСН КСО РЛЦИ')
    inputG('Проверь информацию КПА РЛЦИ-В VS2 M4')
    KIS.get_tmi_conn_test()
    ASN.get_tmi()
    KSO.clear_tmi()
    KSO.get_tmi()

    # KIS.off()
    # ASN.off(asn)
    # Imitators.off_imitators_DS()
    # Imitators.off_imitators_ZD()
    # KSO.off()
    # RLCI.off()


def Test_ASN_BARL_KSO_RLCI_BSK_P_BSK_Ku():
    pass


#####################     MAIN      ###########################
print()
foo = {
    'БШВ, КИР, КПДУ': init,
    'ОЧИСТ НАКОПИТЕЛЬ': lambda: BCK.clcBCK(),
    'СБРОС НАКОПИТЕЛЬ': lambda: BCK.downBCK(),
    'БАРЛ СР ДР': lambda: windowChooser(
        btnsText=('СР 1/2', 'СР 2/2', 'СР 3/4', 'СР 4/4', 'ДР'),
        title='БАРЛ СР ДР',
        fooDict={
            'СР 1/2': lambda: KIS.on(1),
            'СР 2/2': lambda: KIS.on(2),
            'СР 3/4': lambda: KIS.on(3),
            'СР 4/4': lambda: KIS.on(4),
            'ДР': lambda: KIS.off()},
        ret_btn=True),
    'БАРЛ КПА уст изм': lambda: KIS.set_KPA_level(),
    'БАРЛ КПА настройка': lambda: KIS.sensitive_prm_bin(10),  # lambda: KIS.sensitive_prm(10),
    'БАРЛ тест связи': lambda: windowChooser(
        btnsText=('10', '100', 'Ввод'),
        title='БАРЛ тест связи',
        fooDict={
            '10': lambda: KIS.get_tmi_conn_test(10),
            '100': lambda: KIS.get_tmi_conn_test(100),
            'Ввод': lambda: KIS.get_tmi_conn_test(
                int(inputGGG('num', title='Ввод кол-во комманд для проверик связи БАРЛ')))},
        ret_btn=True),
    'БАРЛ КПА вывод изм': lambda: KIS.print_BARL_levels(),
    # 'ПОТОК SOTC': lambda: KIS._barl_run(),
    'АСН ВКЛ ОТКЛ': lambda: windowChooser(
        btnsText=('ВКЛ 1', 'ВКЛ 2', 'ОТКЛ 1', 'ОТКЛ 2',),
        title='АСН ВКЛ',
        fooDict={
            'ВКЛ 1': lambda: ASN.on(1),
            'ВКЛ 2': lambda: ASN.on(2),
            'ОТКЛ 1': lambda: ASN.off(1),
            'ОТКЛ 2': lambda: ASN.off(2)},
        ret_btn=True),
    'АСН тест КСВЧ': lambda: windowChooser(
        btnsText=('АСН 1', 'АСН 2'),
        title='АСН тест КСВЧ',
        fooDict={
            'АСН 1': lambda: ASN.get_tmi(1),
            'АСН 2': lambda: ASN.get_tmi(2)},
        ret_btn=True),
    'АСН сброс все ДИ': lambda: windowChooser(
        btnsText=('АСН 1', 'АСН 2'),
        title='АСН сброс все ДИ',
        fooDict={
            'АСН 1': lambda: ASN.get_all_di(1),
            'АСН 2': lambda: ASN.get_all_di(2)},
        ret_btn=True),
    'АСН контроль': lambda: windowChooser(
        btnsText=('АСН 1', 'АСН 2'),
        title='АСН контроль',
        fooDict={
            'АСН 1': lambda: ASN.res_control(1),
            'АСН 2': lambda: ASN.res_control(2)},
        ret_btn=True),
    'ИМ ДС ВКЛ': lambda: Imitators.on_imitators_DS(),
    'ИМ ДС ОТКЛ': lambda: Imitators.off_imitators_DS(),
    'ИМ ЗД ВКЛ': lambda: Imitators.on_imitators_ZD(),
    'ИМ ЗД ОТКЛ': lambda: Imitators.off_imitators_ZD(),
    'КСО ВКЛ ОТКЛ': lambda: windowChooser(
        btnsText=('ВКЛ', 'ОТКЛ'),
        title='КСО ВКЛ ОТКЛ',
        fooDict={
            'ВКЛ': lambda: KSO.on(),
            'ОТКЛ': lambda: KSO.off()},
        ret_btn=True),
    # 'КСО ДИ': KSO.__unrealized__,
    'КСО ДИ': lambda: windowChooser(
        btnsText=('init', 'ТЕКУЩ', 'ИНТРЕВАЛ', 'Очистить лог'),
        title='КСО ДИ',
        fooDict={
            'init': lambda: KSO.init_di(),
            'ТЕКУЩ': lambda: KSO.get_tmi(),
            'ИНТРЕВАЛ': lambda: KSO.get_tmi(isInterval=True),
            # 'ИНТРЕВАЛ сравнить': KSO.get_tmi_and_compare,
            'Очистить лог': lambda: KSO.clear_tmi()},
        ret_btn=True),
    'КСО ММ': lambda: windowChooser(
        btnsText=('ММ 1', 'ММ 2'),
        title='КСО ММ',
        fooDict={
            'ММ 1': lambda: KSO.set_MM(1),
            'ММ 2': lambda: KSO.set_MM(2)},
        ret_btn=True),
    # 'ДУК ВКЛ': DUK.on,
    # 'ДУК ОТКЛ': DUK.off,
    # 'ДУК ВКЛ КИБК': DUK.autoOnDUk,
    'КДУ ПМ': KDUExecute,
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
    'РЛЦИ АФУ МАССИВ': lambda: RLCI.sendArrayToAntenna(
        'КПА', CPIMD(addr=0x0,
                     data=AsciiHex(
                         '0x'
                         '805004509411E8030A00D0870A00F4011400C4890A00000000000A0000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                         'A05005509411E8030A00D0870A00F4011400C4890A0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                         '00000000000000000000000000000000000000000000000000000000000000000000'),
                     std=2)),
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
    # 'БСКР ВКЛ': lambda: BSK_P.on(),
    # 'БСКР ОТКЛ': lambda: BSK_P.off(),
    # 'БСКР ДИ': lambda: BSK_P.get_tmi(),
    # 'БСКKu ВКЛ': lambda: BSK_KU.on(),
    # 'БСКKu ОТКЛ': lambda: BSK_KU.off(),
    # 'БСКKu ДИ': lambda: BSK_KU.get_tmi(),
    # 'БСКСП ВКЛ': lambda: BSK_BSPA.on(),
    # 'БСКСП ОТКЛ': lambda: BSK_BSPA.off(),
    # 'БСКСП ДИ': lambda: BSK_BSPA.get_tmi(),
    'БСК РЛЦИ ВЫКЛ': bck_rlci_off,
    'МПЗ ПМ': MPZlaunch,
    'МПЗ ПМ РЛЦИ': rlci_mpz,
    'МПЗ ПМ БСК': ku_mpz,
    'ОПИСАНИЕ ТЕСТОВ': lambda: TEST_DESCRIPTION(),
    'АВТОМАТИЗ ТЕСТЫ': lambda: windowChooser(
        btnsText=('ИЗМ БАРЛ',
                  ('АСН КИС', '')),
        title='АВТОМАТИЗ ТЕСТЫ',
        fooDict={'ИЗМ БАРЛ': TEST_senseKIS,
                 'ВЕСЬ ЭМС НЕ ВКЛЮЧАТЬ': Test_ASN_BARL},
        ret_btn=True)
}
btns = ('БШВ, КИР, КПДУ',
        ('ОЧИСТ НАКОПИТЕЛЬ', 'СБРОС НАКОПИТЕЛЬ'),
        ('БАРЛ СР ДР', 'БАРЛ тест связи', 'БАРЛ КПА настройка', 'БАРЛ КПА уст изм', 'БАРЛ КПА вывод изм'),
        ('АСН ВКЛ ОТКЛ', 'АСН тест КСВЧ', 'АСН контроль', 'АСН сброс все ДИ'),
        ('ИМ ДС ВКЛ', 'ИМ ДС ОТКЛ', 'ИМ ЗД ВКЛ', 'ИМ ЗД ОТКЛ',),
        ('КСО ВКЛ ОТКЛ', 'КСО ДИ', 'КСО ММ'),
        # ('ДУК ВКЛ', 'ДУК ОТКЛ', 'ДУК ВКЛ КИБК'),
        'КДУ ПМ',
        'M778',
        ('РЛЦИ ЭА', 'РЛЦИ АФУ МАССИВ', 'РЛЦИ ПЧ', 'РЛЦИ ФИП', 'РЛЦИ МОД', 'РЛЦИ УМ', 'РЛЦИ РЕЖИМ', 'РЛЦИ ВСЕ БЛОКИ'),
        ('МПЗ ПМ РЛЦИ', 'МПЗ ПМ БСК', 'БСК РЛЦИ ВЫКЛ'),
        # ('БСКР ВКЛ', 'БСКР ОТКЛ', 'БСКР ДИ'),
        # ('БСКKu ВКЛ', 'БСКKu ОТКЛ', 'БСКKu ДИ'),
        # ('БСКСП ВКЛ', 'БСКСП ОТКЛ', 'БСКСП ДИ'),
        ('ОПИСАНИЕ ТЕСТОВ', 'АВТОМАТИЗ ТЕСТЫ'))
print()
yprint('ИСПЫТАНИЕ: АИП ИСПЫТАНИЙ МКА НА ЭМС ЧАСТЬ 1 НАСТРОЙКА РЭС', tab=3)
# KIS._barl_run()     # запустить поток SOTC
while True:
    print()
    try:
        windowChooser(btnsText=btns, fooDict=foo,
                      labels=['Init', 'БЦК', 'БАРЛ', 'АСН', 'ИМИТ КСО', 'КСО', 'ДУК', 'M778',
                              'РЛЦИ',
                              'МПЗ',  # 'БСК P', 'БСК Ku', 'БСКСП',
                              'ТЕСТЫ'])
    except Exception as ex:
        LOGGER.error(traceback.format_exc().strip('\n').split('\n')[-1])
        rprint(traceback.format_exc())
