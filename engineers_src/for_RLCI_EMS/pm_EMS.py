"""
ИСП ЭМС ЧАСТЬ 1 НАСТРОЙКА РЭС
  - МКА полность собран, установлен на диэлектрическую подставку для БЭК ОМ67.91.22.000 и размещен на поворотном круге в БЭК1 так,
    чтобы его ось –Y была направлена на АИК; антенна АФУ-Х направлена в «зенит» в соответствии с ИВЯФ.464655.033РЭ и закреплена в этом положении
    с помощью приспособления для фиксация АФУ-Х ТАИК.301318.026 в соответствии с его ТАИК.410114.001 РЭ; разъемы Х3 и Х4 АФУ-Х расстыкованы;
    выполнить работы с АФУ Ku в соответствии с РЭ на БСК с тем, чтобы его диаграмма была направлена на АИК;
  - собрана схема Э6.2;
  - РМ включено согласно ОМ66.81.00.000 РЭ;
  - внешние ворота БЭК закрыты и прижаты;
  - МКА включен по ИЭ17.2 в следуещем варианте: питание от ИГБФ, БА КИС в ДР.
"""
# DEBUG
from time import sleep as sleep2
import time
time.sleep = lambda *args: sleep2(0)
sleep = lambda *args: sleep2(0)
# Импорт зависимостей на винде
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

# Импорт с рабочей директории скрипта
from engineers_src.Devices.functions import windowChooser, sendFromJson, doEquation, executeTMI, print_start_and_end
from engineers_src.Devices.dictionariesUVDI import DIstorage
from engineers_src.Devices import BCK, M778, KIS, RLCI, ASN, Imitators, BSK_BSPA, BSK_P, BSK_KU, KSO
from engineers_src.Devices.Device import LOGGER
from engineers_src.Devices.functions import DB

# TODO: првоерить
#  есть ли коммутация в DiStorage и RLCIV
#  все функции

# TODO flag на запись лога, т.к. запрпшивает ДИ,
#  можно добавить функцию в абстрактный класс
#  и логить если есть handlers

# TODO: разнести классы на методы Управление
#  и методы опроса ДИ, мб через словари функциями

# TODO: в КСО добавить получить среднее значение по измерыннм параметрам
#  и првоерять ТМИ в диапазоне от этого параметра

# TODO:
#  когда вклчили асн
#  выключили КИС
#  получить ТМИ по всем ДИ за это врумя
#  config.updData("%d_%s" % (threading.get_ident(), param_name), res[1])
#  Ex.getTMIS - не работает для кучи зачений
#  получить словрь записать в словарь

# TODO: в абстрактном классе сделать методы для опроса телеметрии интервалом и по одному
#  на универсальных занчения, методы приватными и их можно юзать в классах блоков
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
btn_ask_di = True
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
ASN.cur = None
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
    KIS.sensitive_prm_bin(5)
    KIS.off()
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ2', tab=2)
    KIS.on(2)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(5)
    KIS.off()
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ3', tab=2)
    KIS.on(3)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(5)
    KIS.off()
    print()
    yprint('НАСТРОЙКА РЛ КИС И ЗАМЕР ИСХОДНОЙ ЧУВСТВИТЕЛЬНОСТИ ПРМ4', tab=2)
    KIS.on(4)
    KIS.get_tmi()
    KIS.sensitive_prm_bin(5)
    KIS.off()
    comm_print("Полученные значения мощности:")
    KIS.print_BARL_levels()


#####################     MAIN      ###########################
print()
# словрь с функциями для кнопок
foo = {
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
    'БАРЛ КПА УСТ МОЩ': lambda: KIS.set_KPA_level(),
    'БАРЛ КПА ИЗМ МОЩ': lambda: KIS.sensitive_prm(5),
    'БАРЛ КПА ИЗМ МОЩ БИН': lambda: KIS.sensitive_prm_bin(5),
    'БАРЛ ТЕСТ ПРИЕМА': lambda: KIS.get_tmi_conn_test(),
    'БАРЛ КПА ВЫВОД МОЩ': lambda: KIS.print_BARL_levels(),
    # 'ПОТОК SOTC': lambda: KIS._barl_run(),
    'АСН ВКЛ ОТКЛ': lambda: windowChooser(
        btnsText=('ВКЛ 1', 'ВКЛ 2', 'ОТКЛ 1', 'ОТКЛ2',),
        title='АСН ВКЛ',
        fooDict={
            'ВКЛ 1': lambda: ASN.on(1),
            'ВКЛ 2': lambda: ASN.on(2),
            'ОТКЛ 1': lambda: ASN.off(1),
            'ОТКЛ2': lambda: ASN.off(2)},
        ret_btn=True),
    'АСН ПРОВ СИГНАЛ': lambda: ASN.check_sm_output(),
    'АСН КОНТРОЛЬ РАБОТЫ': lambda: ASN.res_control(),
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
    'КСО ТМИ ТЕКУЩ': lambda: KSO.get_tmi(),
    'КСО ТМИ ИНТРЕВАЛ': lambda: KSO.get_tmi(isInterval=True),
    'КСО СБРОС НАКОП ДИ': lambda: KSO.clear_tmi(),
    '!!!КСО ПРОВ ТМИ': KSO.__unrealized__,
    '!!!КСО ТОК': KSO.__unrealized__,
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
            'ВКЛ ЭА332-1': lambda: RLCI.EA332.on(1, stop_shd=True, ask_TMI=True),
            'ВКЛ ЭА332-2': lambda: RLCI.EA332.on(2, stop_shd=True, ask_TMI=True),
            'ОТКЛ ЭА332': lambda: RLCI.EA332.off(),
            'ВКЛ ЭА331-1': lambda: RLCI.EA331.on(1),
            'ВКЛ ЭА331-2': lambda: RLCI.EA332.on(2),
            'ОТКЛ ЭА331': lambda: RLCI.EA331.off()},
        labels=['ЭА332', 'ЭА331'],
        ret_btn=True),
    'РЛЦИ ПЧ': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ ПЧ',
        fooDict={
            'ОСН': lambda: RLCI.PCH.on(1),
            'РЕЗ': lambda: RLCI.PCH.on(2),
            'ОТКЛ': lambda: RLCI.PCH.off()},
        ret_btn=True),
    'РЛЦИ ФИП': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ ФИП',
        fooDict={
            'ОСН': lambda: RLCI.FIP.on(1),
            'РЕЗ': lambda: RLCI.FIP.on(2),
            'ОТКЛ': lambda: RLCI.FIP.off()},
        ret_btn=True),
    'РЛЦИ МОД': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ МОД',
        fooDict={
            'ОСН': lambda: RLCI.MOD.on(1),
            'РЕЗ': lambda: RLCI.MOD.on(2),
            'ОТКЛ': lambda: RLCI.MOD.off()},
        ret_btn=True),
    'РЛЦИ УМ': lambda: windowChooser(
        btnsText=('ОСН', 'РЕЗ', 'ОТКЛ'),
        title='РЛЦИ УМ',
        fooDict={
            'ОСН': lambda: RLCI.UM.on(1),
            'РЕЗ': lambda: RLCI.UM.on(2),
            'ОТКЛ': lambda: RLCI.UM.off()},
        ret_btn=True),
    'РЛЦИ АФУ МАССИВ': lambda: RLCI.sendArrayToAntenna(
        'КПА', CPIMD(addr=0x0,
                     data=AsciiHex(
                         '0x805004509411E8030A00D0870A00F4011400C4890A00000000000A0000000000000000000000000000000000000'
                         '000000000000000000000000000000000000000000000A05005509411E8030A00D0870A00F4011400C4890A000000'
                         '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                         '000000000000000000000000000000000000000000000000000000000000000'),
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
    'БСКР ВКЛ': lambda: BSK_P.on(),
    'БСКР ОТКЛ': lambda: BSK_P.off(),
    'БСКР ДИ': lambda: BSK_P.get_tmi(),
    'БСКKu ВКЛ': lambda: BSK_KU.on(),
    'БСКKu ОТКЛ': lambda: BSK_KU.off(),
    'БСКKu ДИ': lambda: BSK_KU.get_tmi(),
    'БСКСП ВКЛ': lambda: BSK_BSPA.on(),
    'БСКСП ОТКЛ': lambda: BSK_BSPA.off(),
    'БСКСП ДИ': lambda: BSK_BSPA.get_tmi(),
    'ОПИСАНИЕ ТЕСТОВ': lambda: TEST_DESCRIPTION(),
    'АВТОМАТИЗ ТЕСТЫ': lambda: windowChooser(
        btnsText=('ИЗМ БАРЛ',),
        title='АВТОМАТИЗ ТЕСТЫ',
        fooDict={'ИЗМ БАРЛ': lambda: TEST_senseKIS()},
        ret_btn=True)
}
# кнопки
btns = (('ОЧИСТ НАКОПИТЕЛЬ', 'СБРОС НАКОПИТЕЛЬ'),
        ('БАРЛ СР ДР', 'БАРЛ КПА УСТ МОЩ', 'БАРЛ КПА ИЗМ МОЩ БИН', 'БАРЛ КПА ИЗМ МОЩ', 'БАРЛ ТЕСТ ПРИЕМА', 'БАРЛ КПА ВЫВОД МОЩ'),
        ('АСН ВКЛ ОТКЛ', 'АСН ПРОВ СИГНАЛ', 'АСН КОНТРОЛЬ РАБОТЫ'),
        ('ИМ ДС ВКЛ', 'ИМ ДС ОТКЛ', 'ИМ ЗД ВКЛ', 'ИМ ЗД ОТКЛ',),
        ('КСО ВКЛ ОТКЛ', 'КСО ТМИ ТЕКУЩ', 'КСО ТМИ ИНТРЕВАЛ', 'КСО СБРОС НАКОП ДИ', '!!!КСО ПРОВ ТМИ', '!!!КСО ТОК'),
        'M778',
        ('РЛЦИ ЭА', 'РЛЦИ АФУ МАССИВ', 'РЛЦИ ПЧ', 'РЛЦИ ФИП', 'РЛЦИ МОД', 'РЛЦИ УМ', 'РЛЦИ РЕЖИМ', 'РЛЦИ ВСЕ БЛОКИ'),
        ('БСКР ВКЛ', 'БСКР ОТКЛ', 'БСКР ДИ'),
        ('БСКKu ВКЛ', 'БСКKu ОТКЛ', 'БСКKu ДИ'),
        ('БСКСП ВКЛ', 'БСКСП ОТКЛ', 'БСКСП ДИ'),
        ('ОПИСАНИЕ ТЕСТОВ', 'АВТОМАТИЗ ТЕСТЫ'))
print()
yprint('ИСПЫТАНИЕ: АИП ИСПЫТАНИЙ МКА НА ЭМС ЧАСТЬ 1 НАСТРОЙКА РЭС', tab=3)
# KIS._barl_run()     # запустить поток SOTC
while True:
    print()
    try:
        windowChooser(btnsText=btns, fooDict=foo, labels=['БЦК', 'БАРЛ', 'АСН', 'ИМИТ КСО', 'КСО', 'M778',
                                                          'РЛЦИ', 'БСК P', 'БСК Ku', 'БСКСП', 'ТЕСТЫ'])
    except Exception as ex:
        LOGGER.error(traceback.format_exc().strip('\n').split('\n')[-1])
        rprint(traceback.format_exc())

# начать с АСН, включить имитатор и асн, посмотреть что он поймал от 4 спутниклов
# выдвать команды на КИС смотреть есть ли влияние на навигацию
# КАМЕРА ПРИБОРЫ ОРИЕНТАЦИИ
#

# сначала АСН - включается проверяется прием на КИС и на АСН

# включать всю целлевую
# yprint('НАСТРОЙКА РЛ РЛЦИВ', tab=2)
# Ex.send('КПА', KPA('Мощность-уст', KA_Status.barl_names['1\\2']))  # установить настроенную мощность КПА
# KIS.mode_SR(nbarl='1\\2')
# KIS.validateConn()
# # Код для РЛЦИ-В
# KIS.mode_DR()
# print()
#
# # работа КИС
# sleep(40)
#
# print()
# #KIS.mode_standby()      # БАРЛ в ДР
# sleep(20)

# KIS_measure_sensitivity(1, n_SOTC=5, started=started_KIS_session, add_sensitive=0)  # замер чувствт КИС
# KIS.mode_standby(1)  # БАРЛ в дужерный режим
