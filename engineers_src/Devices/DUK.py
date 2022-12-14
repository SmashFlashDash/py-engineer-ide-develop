from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep, SICCELL, s2h
import time
from cpi_framework.utils.basecpi_abc import *
from ivk import config
from ivk.scOMKA.simplifications import SCPICMD
from ivk.scOMKA.simplifications import SICCELL
from ivk.cpi_framework_connections import b2h
from ivk.cpi_framework_connections import s2h

Ex = config.get_exchange()
redis_dp_get = config.getData  # вторая бд redis
redis_dp_set = config.updData  # вторая бд redis
redis_dp_inc = config.incData  # вторая бд redis
from time import sleep
from engineers_src.tools.ivk_script_tools import *

'''Остальные импорты'''
from collections import OrderedDict
from copy import deepcopy


def executeTMI(*args, **kwargs):
    if 'pause' in kwargs:
        pause = kwargs['pause']
        kwargs.pop('pause', None)
    else:
        pause = 3
    sleep(pause)  # пауза перед опросм ДИ чтобы записалось в БД
    result, dict_cpyphers = controlGetEQ(*args, **kwargs)
    if not result:
        inputG('Проверь ТМИ')
    return dict_cpyphers


startswit = ('\'', '\"', '@', '[',) + tuple([str(x) for x in range(0, 10)])  # поставить в телеметри кавычки на слова


def doEquation(cyph, calib, status=None):
    cyph = cyph.strip()
    calib = calib.strip()
    if status is None:
        reference_value = DI[cyph][calib].strip()
    else:
        reference_value = DI[cyph][calib][status.strip()].strip()
    if calib in ('@K', '@К') and not reference_value.startswith(startswit):  # забыл кавчки в DI слвоаре
        reference_value = '\'' + reference_value + '\''
    return '{%s}%s==%s' % (cyph, calib, reference_value)


def equationDUK():
    equation = []
    for item_didict in DI.items():
        for item in item_didict[1].items():
            cypher = item[0]
            eq = item[1]['@H']
            equation.append('{%s}@H == %s' % (cypher, eq))
    return ' and '.join(equation)


def UV_CYPHER(block_num, uv_num):
    return uv_num + block_num * 0x1000


def setCountdownEnd(bk, k):
    global countdown
    if k == 'K1':
        notusedk = 'K2'
    else:
        notusedk = 'K1'
    countdown[bk + k] = time.time() + 1200.0
    countdown[bk + notusedk] = time.time() + 1200.0
    return


def checkBkBan(bk, k):
    global countdown
    if time.time() <= countdown[bk + k]:
        print('Пауза между включениями на {} должна составлять 20 мин'.format(bk))
        bk_pause = int(countdown[bk + k] - time.time())
        print('До следующего включения {} с'.format(bk_pause))
        time.sleep(bk_pause)
    print('Работа {} на {} разрешена'.format(bk, k))
    return


def checkCathodeBan(bk, k):
    global countdown
    if time.time() <= countdown[bk + k]:
        print('Запрет на включение {} на {} будет активен еще {} мин'.format(bk, k,
                                                                             (countdown[bk + k] - time.time()) / 60))
        bkk_ban = Ex.get('ТМИ', '01.02.{}{}_ZAPRET'.format(bk, k), 'НЕКАЛИБР ТЕКУЩ')
        print('{}{}_ZAPRET = {}'.format(bk, k, bkk_ban))
        while time.time() <= countdown[bk + k]:
            continue
    DROP_DI()
    bkk_ban = Ex.get('ТМИ', '01.02.{}{}_ZAPRET'.format(bk, k), 'НЕКАЛИБР ТЕКУЩ')
    print('{}{}_ZAPRET = {}'.format(bk, k, bkk_ban))
    print('Работа {} на {} разрешена'.format(bk, k))
    return


countdown = {

    'BK1K1': time.time(),
    'BK1K2': time.time(),
    'BK2K1': time.time(),
    'BK2K2': time.time()

}

UV = {

    # БЦК
    'БЦК_ОЧИСТКА_ДИ': UV_CYPHER(14, 0x107),
    'БЦК_СБРОС_ПАМЯТИ': UV_CYPHER(14, 0x60),
    'БЦК_ЗАПРОС_ПА29': UV_CYPHER(14, 0x88),

    # ФКП1
    'КПДУ_УПР_ВКЛ': UV_CYPHER(4, 0x09),
    'КПДУ_УПР_ОТКЛ': UV_CYPHER(4, 0x3F1),
    'КПДУ_СИЛ_ВКЛ': UV_CYPHER(4, 0x1D),
    'КПДУ_СИЛ_ОТКЛ': UV_CYPHER(4, 0x405),

    # ФКП2
    'СПУ_28В_ВКЛ': UV_CYPHER(5, 0x015),
    'СПУ_28В_ОТКЛ': UV_CYPHER(5, 0x3FD),

    # БК1
    'ХНГ1БК1': UV_CYPHER(1, 0x22),
    'ХНГ2БК1': UV_CYPHER(1, 0x23),
    'ХОНГБК1': UV_CYPHER(1, 0x24),
    'ХНГБК1_ТЕМП': UV_CYPHER(1, 0x25),
    'ХНГ1БК1_АВТО': UV_CYPHER(1, 0x26),
    'ХНГ2БК1_АВТО': UV_CYPHER(1, 0x27),

    # БК2
    'ХНГ1БК2': UV_CYPHER(1, 0x28),
    'ХНГ2БК2': UV_CYPHER(1, 0x29),
    'ХОНГБК2': UV_CYPHER(1, 0x2A),
    'ХНГБК2_ТЕМП': UV_CYPHER(1, 0x2B),
    'ХНГ1БК2_АВТО': UV_CYPHER(1, 0x2C),
    'ХНГ2БК2_АВТО': UV_CYPHER(1, 0x2D),

    # БПК
    'ХНГРД1': UV_CYPHER(1, 0x2E),
    'ХНГРД2': UV_CYPHER(1, 0x2F),
    'ХОНГРД': UV_CYPHER(1, 0x30),
    'ХНГРД_ТЕМП': UV_CYPHER(1, 0x31),
    'ХНГРД1_АВТО': UV_CYPHER(1, 0x32),
    'ХНГРД2_АВТО': UV_CYPHER(1, 0x33),

    # РК
    'ХСПУ1': UV_CYPHER(1, 0x34),
    'ХСПУ2': UV_CYPHER(1, 0x35),
    'ХОСПУ': UV_CYPHER(1, 0x36),
    'ХК1': UV_CYPHER(1, 0x37),
    'ХК2': UV_CYPHER(1, 0x38),
    'ХТНД': UV_CYPHER(1, 0x39),
    'ХНАД': UV_CYPHER(1, 0x3A),
    'ХЭПД': UV_CYPHER(1, 0x3B),
    'ХРД': UV_CYPHER(1, 0x3C),
    'ХОД': UV_CYPHER(1, 0x3D),
    'ХЭКД': UV_CYPHER(1, 0x3E),
    'Х1БПК': UV_CYPHER(1, 0x3F),
    'Х2БПК': UV_CYPHER(1, 0x40),
    'Х3БПК': UV_CYPHER(1, 0x41),
    'Х6БПК': UV_CYPHER(1, 0x42),
    'ХОБПК': UV_CYPHER(1, 0x43),
    'ХПК': UV_CYPHER(1, 0x44),
    'ХБПП': UV_CYPHER(1, 0x45),
    'ХОБПП': UV_CYPHER(1, 0x46),

    # ЦИКЛОГРАММЫ
    'ХВКЛ_КДУ': UV_CYPHER(1, 0x47),
    'ХДУК_Ц1': UV_CYPHER(1, 0x4D),
    'ХДУК_Ц2': UV_CYPHER(1, 0x4E),
    'ХДУК_Ц3': UV_CYPHER(1, 0x4F),
    'ХДУК_Ц4': UV_CYPHER(1, 0x50),

    # ПА
    'ХКПДУ_ПА2': UV_CYPHER(1, 0x51),
    'ХКПДУ_ПА3': UV_CYPHER(1, 0x52),
    'ХКПДУ_ПА4': UV_CYPHER(1, 0x53),

    # КПДУ
    'ХДУК_ТВ_ПРЕД': UV_CYPHER(1, 0x49),
    'ХКПДУ_СБРОС': UV_CYPHER(1, 0x4C),
    'ХСПУ_АВТО_ВКЛ': UV_CYPHER(1, 0x5A),
    'ХСПУ_АВТО_ОТКЛ': UV_CYPHER(1, 0x60),
    'ХДУК_АВТО': UV_CYPHER(1, 0x62),
    'ХНШ_СБРОС': UV_CYPHER(1, 0x63),
    'ХКПДУ_МОД': UV_CYPHER(1, 0x64),
    'ХДУК_РАЗР': UV_CYPHER(1, 0x65),
    'ХДНБПК_ВКЛ': UV_CYPHER(1, 0x6B),
    'ХДНБПК_ОТКЛ': UV_CYPHER(1, 0x6C),
    'ХМКПД_ВКЛ': UV_CYPHER(1, 0x6D),
    'ХМКПД_ОТКЛ': UV_CYPHER(1, 0x6E),
    'ХКАТОД_СБРОС': UV_CYPHER(1, 0x71),
    'ХДАТЧИК_ОТКЛ': UV_CYPHER(1, 0x72),
    'ХНЭО_ТД_ДД': UV_CYPHER(1, 0x73),
    'ХУСТ_ДД_БПК': UV_CYPHER(1, 0x74),
    'ХДАТЧИК_СБРОС': UV_CYPHER(1, 0x75),
    'ХТАРИР_АД': UV_CYPHER(1, 0x76),
    'ХАНАЛИЗ_НШ0': UV_CYPHER(1, 0x7A),
    'ХДУК_ЗАПРЕТ_ВКЛ': UV_CYPHER(1, 0x7B),
    'ХДУК_ЗАПРЕТ_ОТКЛ': UV_CYPHER(1, 0x7C)

}


def PA(t):
    print('Установка времени опроса ПА2, ПА3, ПА4-8 периодичностью {} с'.format(t))
    SCPICMD(UV['ХКПДУ_ПА2'], AsciiHex('0x' + s2h(t) + '000000000000'))  # опрос ДИ2
    time.sleep(1)
    SCPICMD(UV['ХКПДУ_ПА3'], AsciiHex('0x' + s2h(t) + '000000000000'))  # Время опроса ДИ3
    time.sleep(1)
    SCPICMD(UV['ХКПДУ_ПА4'], AsciiHex('0x' + s2h(t) + '000000000000'))  # Время опроса ДИ4-8
    time.sleep(1)


def DROP_DI():
    SCPICMD(UV['БЦК_ОЧИСТКА_ДИ'])  # очистка области ДИ БЦК
    sleep(5)
    SCPICMD(UV['БЦК_СБРОС_ПАМЯТИ'])  # сброс области ДИ БЦК
    sleep(5)
    return


def set_5HzTMI_dict(pa_num):
    pacypher = '01.0' + str(pa_num) + '.'
    return OrderedDict([
        (pacypher + 'NBPP', {'@K': None, '@H': '[0, 50]'}),
        (pacypher + 'TBPP', {'@K': None, '@H': '[0, 40]'}),
        (pacypher + 'NAD1', {'@K': None, '@H': '[0, 1000]'}),
        (pacypher + 'NAD2', {'@K': None, '@H': '[0, 1000]'}),
        (pacypher + 'TAD1', {'@K': None, '@H': '[0, 5]'}),
        (pacypher + 'TAD2', {'@K': None, '@H': '[0, 5]'}),
        (pacypher + 'TND1', {'@K': None, '@H': '[0, 10]'}),
        (pacypher + 'TND2', {'@K': None, '@H': '[0, 10]'}),
        (pacypher + 'TRRD1', {'@K': None, '@H': '[0, 5]'}),
        (pacypher + 'TRRD2', {'@K': None, '@H': '[0, 5]'}),
        (pacypher + 'DN1BPK', {'@K': None, '@H': '[0, 600]'}),
        (pacypher + 'DN2BPK', {'@K': None, '@H': '[0, 600]'}),
        (pacypher + 'DV1BPK', {'@K': None, '@H': '[0, 19500]'}),
        (pacypher + 'DV2BPK', {'@K': None, '@H': '[0, 19500]'}),
        (pacypher + '1KBPK', {'@K': None, '@H': '0'}),
        (pacypher + '2KBPK', {'@K': None, '@H': '0'}),
        (pacypher + 'STZA1', {'@K': None, '@H': '0'}),
        (pacypher + 'STZA2', {'@K': None, '@H': '0'}),
        (pacypher + 'EP1', {'@K': None, '@H': '0'}),
        (pacypher + 'EP2', {'@K': None, '@H': '0'}),
        (pacypher + 'K1', {'@K': None, '@H': '0'}),
        (pacypher + 'K2', {'@K': None, '@H': '0'}),
        (pacypher + 'STZBPP', {'@K': None, '@H': '0'}),
        (pacypher + 'RBPP', {'@K': None, '@H': '0'})
    ])


duk_tv_pred = Ex.get('ТМИ', '01.02.DUK_TV_PRED', 'НЕКАЛИБР ТЕКУЩ')

DI = OrderedDict([
    ('DI1', OrderedDict([
        ('01.01.NGRD1_AVTO', {'@K': None, '@H': '0'}),
        ('01.01.NGRD2_AVTO', {'@K': None, '@H': '0'}),
        ('01.01.MDKR1', {'@K': None, '@H': '0'}),
        ('01.01.MDKR2', {'@K': None, '@H': '0'}),
        ('01.01.NSh0KR1', {'@K': None, '@H': '0'}),
        ('01.01.NSh0KR2', {'@K': None, '@H': '0'}),
        ('01.01.NSh1K1BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh1K2BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh1K1BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh1K2BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh2K1BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh2K2BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh2K1BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh2K2BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh3K1BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh3K2BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh3K1BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh3K2BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh4BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh4BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh5K1BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh5K2BK1', {'@K': None, '@H': '0'}),
        ('01.01.NSh5K1BK2', {'@K': None, '@H': '0'}),
        ('01.01.NSh5K2BK2', {'@K': None, '@H': '0'}),
        ('01.01.KDU_SOST', {'@K': None, '@H': '0'}),
        ('01.01.REZH_DUK', {'@K': None, '@H': '1'}),
        ('01.01.DUK_ZAPRET', {'@K': None, '@H': '0'}),
        ('01.01.DUK_AVTO', {'@K': None, '@H': '0'}),
        ('01.01.SPU_AVTO', {'@K': None, '@H': '0'}),
        ('01.01.KPDU_MOD', {'@K': None, '@H': '0'}),
        ('01.01.KPDU_OBMEN', {'@K': None, '@H': '0'}),
        ('01.01.MKPD_KONTR', {'@K': None, '@H': '1'}),
        ('01.01.DNBPK_KONTR', {'@K': None, '@H': '1'}),
        # ('01.01.АНАЛИЗ_НШ0КР1', {'@K': None, '@H': '1'}),
        # ('01.01.АНАЛИЗ_НШ0КР2', {'@K': None, '@H': '1'}),
        ('01.01.DUK_ZAPRET_KONTR', {'@K': None, '@H': '1'}),
        ('01.01.BK1_TV', {'@K': None, '@H': '0'}),
        ('01.01.BK2_TV', {'@K': None, '@H': '0'})
    ])),
    ('DI2', OrderedDict([
        #        ('01.02.DUK_TV_TREB', {'@K': None, '@H': '0'}),
        ('01.02.DUK_TV_PRED', {'@K': None, '@H': str(duk_tv_pred)}),
        ('01.02.BK1K1_VREMYa', {'@K': None, '@H': '0'}),
        ('01.02.BK1K2_VREMYa', {'@K': None, '@H': '0'}),
        ('01.02.BK2K1_VREMYa', {'@K': None, '@H': '0'}),
        ('01.02.BK2K2_VREMYa', {'@K': None, '@H': '0'}),
        #        ('01.02.BK1K1_ZAPRET', {'@K': None, '@H': '0'}),
        #        ('01.02.BK1K2_ZAPRET', {'@K': None, '@H': '0'}),
        #        ('01.02.BK2K1_ZAPRET', {'@K': None, '@H': '0'}),
        #        ('01.02.BK2K2_ZAPRET', {'@K': None, '@H': '0'})
    ])),
    ('DI4', set_5HzTMI_dict(4)),
    ('DI5', set_5HzTMI_dict(5)),
    ('DI6', set_5HzTMI_dict(6)),
    ('DI7', set_5HzTMI_dict(7)),
    ('DI8', set_5HzTMI_dict(8))
])

DI_nach = deepcopy(DI)

di1_savedvalueslist = (

    '01.01.NSh0KR1',
    '01.01.NSh0KR2',
    '01.01.NSh1K1BK1',
    '01.01.NSh1K2BK1',
    '01.01.NSh1K1BK2',
    '01.01.NSh1K2BK2',
    '01.01.NSh2K1BK1',
    '01.01.NSh2K2BK1',
    '01.01.NSh2K1BK2',
    '01.01.NSh2K2BK2',
    '01.01.NSh3K1BK1',
    '01.01.NSh3K2BK1',
    '01.01.NSh3K1BK2',
    '01.01.NSh3K2BK2',
    '01.01.NSh4BK1',
    '01.01.NSh4BK2',

    '01.01.REZH_DUK',
    '01.01.DUK_ZAPRET',
    '01.01.DUK_AVTO',
    '01.01.SPU_AVTO',
    '01.01.KPDU_MOD',
    '01.01.KPDU_OBMEN',
    '01.01.MKPD_KONTR',
    '01.01.DNBPK_KONTR',
    '01.01.DUK_ZAPRET_KONTR',

    '01.01.BK1_TV',
    '01.01.BK2_TV'

)

di2_savedvalueslist = (

    '01.02.DUK_TV_PRED',
    '01.02.BK1K1_VREMYa',
    '01.02.BK1K2_VREMYa',
    '01.02.BK2K1_VREMYa',
    '01.02.BK2K2_VREMYa',
    #    '01.02.BK1K1_ZAPRET',
    #    '01.02.BK1K2_ZAPRET',
    #    '01.02.BK2K1_ZAPRET',
    #    '01.02.BK2K2_ZAPRET'

)

sensor = {

    'TIO1': 0x1C,
    'TIO2': 0x1D,
    'T1BPK': 0x0E,
    'T2BPK': 0x0F,
    'T3BPK': 0x10,
    'T4BPK': 0x11,
    'T5BPK': 0x12,
    'T6BPK': 0x13,
    'DN1BPK': 0x18,
    'DN2BPK': 0x19,
    'DV1BPK': 0x1A,
    'DV2BPK': 0x1B

}


def uvNum(uv_num):
    return uv_num - 0x1000


def setInitialStateValues():
    global DI_nach
    global DI

    DROP_DI()
    for i in di1_savedvalueslist:
        DI_nach['DI1'][i]['@H'] = str(Ex.get('ТМИ', i, 'НЕКАЛИБР ТЕКУЩ'))
    for i in di2_savedvalueslist:
        DI_nach['DI2'][i]['@H'] = str(Ex.get('ТМИ', i, 'НЕКАЛИБР ТЕКУЩ'))

    DI = deepcopy(DI_nach)
    return


def set_5HzTMI_value(dicypher, value):
    for i in range(4, 9):
        DI['DI{}'.format(str(i))]['01.0{}.{}'.format(str(i), dicypher)]['@H'] = value
    return


def setVariableDI(bk, k, bpk, nsh):
    bk_num = bk[2]
    bpk_num = bpk[3]
    k_num = k[1]

    ngrd_avto = 'NGRD{}_AVTO'.format(bpk_num)
    nad = 'NAD{}'.format(bk_num)
    tad = 'TAD{}'.format(bk_num)
    tnd = 'TND{}'.format(bk_num)
    trrd = 'TRRD{}'.format(bk_num)
    dnbpk = 'DN{}BPK'.format(bpk_num)
    dvbpk = 'DV{}BPK'.format(bpk_num)
    stza = 'STZA{}'.format(bk_num)
    ep = 'EP{}'.format(bk_num)
    k = 'K{}'.format(k_num)
    bpk = '{}KBPK'.format(bpk_num)
    bk_thrust_time = '{}_TV'.format(bk)
    if bk == 'BK1':
        notused_bk_thrust_time = 'BK2_TV'
    else:
        notused_bk_thrust_time = 'BK1_TV'
    bkk_time = '{}{}_VREMYa'.format(bk, k)
    if nsh == 'NSh4':
        nsh_cypher = nsh + bk
    elif nsh == None:
        nsh_cypher = None
    else:
        nsh_cypher = nsh + k + bk

    return ngrd_avto, nad, tad, tnd, trrd, dnbpk, dvbpk, stza, ep, bk, k, bpk, bk_thrust_time, bkk_time, nsh_cypher, notused_bk_thrust_time


def diWait(di, value, timeout):
    res = Ex.wait('ТМИ', '{' + di + '.НЕКАЛИБР} == ' + str(value), timeout)
    if res == 1:
        gprint('Зарегистрирована ДИ {} == {}'.format(di, value))
    else:
        rprint('ДИ {} не приняла ожидаемого значения {}'.format(di, value))
    return res


def modeRH():
    print('Перевод в режим РХ')
    SCPICMD(UV['ХДУК_Ц2'])
    time.sleep(20)
    setInitialStateValues()
    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')
    if kpdu_obmen == 1:
        DI['DI1']['01.01.KDU_SOST']['@H'] = '3'
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    DI['DI1']['01.01.KDU_SOST']['@H'] = '0'
    return


def setTioValue():
    SCPICMD(UV['ХНЭО_ТД_ДД'], AsciiHex('0x{} 0082 0000 0000'.format(s2h(sensor['TIO1']))))  # ТИО1 500 градусов
    time.sleep(1)
    SCPICMD(UV['ХНЭО_ТД_ДД'], AsciiHex('0x{} 0082 0000 0000'.format(s2h(sensor['TIO2']))))  # ТИО2 500 градусов
    time.sleep(1)
    return


def RK(rk_cypher):
    SCPICMD(UV[rk_cypher])
    print('Выдано РК {}'.format(rk_cypher))
    return


def dukZapretCheck():
    if (Ex.get('ТМИ', '01.01.DUK_ZAPRET_KONTR', 'НЕКАЛИБР ТЕКУЩ') == 1) and (
            Ex.get('ТМИ', '01.01.DUK_ZAPRET', 'НЕКАЛИБР ТЕКУЩ') == 1):
        gprint('Выставлен ЗАПРЕТ на включение ДУК')
    else:
        rprint('ЗАПРЕТ на включение ДУК не выставлен')
    return


def resetBan():
    duk_zapret = Ex.get('ТМИ', '01.01.DUK_ZAPRET', 'НЕКАЛИБР ТЕКУЩ')
    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')
    mkpd_control = Ex.get('ТМИ', '01.01.MKPD_KONTR', 'НЕКАЛИБР ТЕКУЩ')
    if duk_zapret == 1:
        SCPICMD(UV['ХДУК_РАЗР'])
        print('Выдано УВ на разрешение включения ДУК')
    if (kpdu_obmen == 1) and (mkpd_control == 1):
        SCPICMD(UV['ХКПДУ_СБРОС'])
        print('Выдано УВ на сброс признака нарушения обмена')
    if (duk_zapret == 1) or (kpdu_obmen == 1):
        time.sleep(5)
    return


def switchModuleKpdu():  # Функция переключения модуля КПДУ

    yprint('Переключение модуля КПДУ')
    mod1 = Ex.get('ТМИ', '01.01.KPDU_MOD', 'НЕКАЛИБР ТЕКУЩ') + 1
    print("Используемый модуль КПДУ: {}".format(mod1))
    spu_avto = Ex.get('ТМИ', '01.01.SPU_AVTO', 'НЕКАЛИБР ТЕКУЩ')
    print('SPU_AVTO == {}'.format(spu_avto))
    if spu_avto == 0:
        SCPICMD(UV['ХСПУ_АВТО_ВКЛ'])
        print('Выдано УВ на включение автоматического приведения СПУ в режим РХ')
        diWait('01.01.SPU_AVTO', 1, 20)
    SCPICMD(UV['ХКПДУ_МОД'])  # Переключение модуля КПДУ
    print("Выдано УВ на переключение модуля КПДУ")
    Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ТЕКУЩ')
    res = Ex.wait('ТМИ', '{01.01.KPDU_VREMYa.НЕКАЛИБР} < 5', 60)  # Ожидание сброса времени работы КПДУ
    if res == 1:
        gprint("Время работы КПДУ сброшено")
        print("Время КПДУ:", Ex.get('ТМИ', '01.01.KPDU_VREMYa', 'НЕКАЛИБР ТЕКУЩ'))
    else:
        rprint("Время работы КПДУ не сброшено")
    time.sleep(2)
    mod2 = Ex.get('ТМИ', '01.01.KPDU_MOD', 'НЕКАЛИБР ТЕКУЩ') + 1
    if mod2 != mod1:  # Сравнение ДИ работающего модуля с ДИ модуля до выдачи УВ на переключение
        gprint("Модуль КПДУ переключился. Текущий модуль КПДУ: {}".format(mod2))
    elif mod2 == mod1:
        rprint("Модуль КПДУ не переключился. Текущий модуль КПДУ {}".format(mod2))
    time.sleep(15)
    vyp_uv_list = Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ИНТЕРВАЛ')
    yprint('Проверка приведения СПУ в режим РХ после перезагрузки модуля КПДУ')
    checkUvList([0] + cyclogram['ХДУК_Ц2'], vyp_uv_list)
    setTioValue()
    PA(1)
    return


def dukZapret(bk, k):
    bk_num = bk[2]
    k_num = k[1]
    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')

    RK('ХБПП')
    set_5HzTMI_value('NBPP', '[5950, 6060]')
    set_5HzTMI_value('RBPP', '1')
    if kpdu_obmen == 1:
        DI['DI1']['01.01.KDU_SOST']['@H'] = '3'
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    RK('ХСПУ{}'.format(bk_num))
    time.sleep(1)
    RK('ХК{}'.format(k_num))
    set_5HzTMI_value(k, '0')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    modeRH()
    setInitialStateValues()
    input('Для продолжения нажмите Enter')
    return


def setDukBanControl(duk_ban_control):
    if duk_ban_control == 'ВКЛ':
        SCPICMD(UV['ХДУК_ЗАПРЕТ_ВКЛ'])
        print('Выдано УВ на включение контроля запрета ДУК')
    else:
        SCPICMD(UV['ХДУК_ЗАПРЕТ_ОТКЛ'])
        print('Выдано УВ на отключение контроля запрета ДУК')
    time.sleep(10)
    duk_zapret_kontr = Ex.get('ТМИ', '01.01.DUK_ZAPRET_KONTR', 'НЕКАЛИБР ТЕКУЩ')
    if ((duk_zapret_kontr == 1) and (duk_ban_control == 'ВКЛ')) or (
            (duk_zapret_kontr == 0) and (duk_ban_control == 'ОТКЛ')):
        gprint('DUK_ZAPRET_KONTR == {}'.format(duk_zapret_kontr))
    else:
        rprint('DUK_ZAPRET_KONTR == {}'.format(duk_zapret_kontr))
    return


def nsh0Check(mode, duk_ban_control):
    def print_kr_analizys():
        kr1_analizys = Ex.get('ТМИ', '01.01.ANALIZ_NSh0KR1', 'НЕКАЛИБР ТЕКУЩ')
        kr2_analizys = Ex.get('ТМИ', '01.01.ANALIZ_NSh0KR2', 'НЕКАЛИБР ТЕКУЩ')
        print('Анализ НШ0КР1 = {}'.format(kr1_analizys))
        print('Анализ НШ0КР2 = {}'.format(kr2_analizys))

    if mode == 'ВКЛ':
        yprint('Проверка НШ0 при включенном контроле')
    else:
        yprint('Проверка НШ0 при отключенном контроле')

    setDukBanControl(duk_ban_control)
    kr1_analizys = Ex.get('ТМИ', '01.01.ANALIZ_NSh0KR1', 'НЕКАЛИБР ТЕКУЩ')
    kr2_analizys = Ex.get('ТМИ', '01.01.ANALIZ_NSh0KR2', 'НЕКАЛИБР ТЕКУЩ')
    print_kr_analizys()
    if (mode == 'ВКЛ') and ((kr1_analizys == 0) or (kr2_analizys == 0)):
        SCPICMD(UV['ХАНАЛИЗ_НШ0'], AsciiHex('0x0000 0000 0000 0000'))
        print('Выдано УВ на включение анализа НШ0КР1 и НШ0КР2')
    elif (mode == 'ОТКЛ') and ((kr1_analizys == 1) or (kr2_analizys == 1)):
        SCPICMD(UV['ХАНАЛИЗ_НШ0'], AsciiHex('0x0300 0000 0000 0000'))
        print('Выдано УВ на отключение анализа НШ0КР1 и НШ0КР2')

    temp_value = 0xFF

    for i in range(1, 7):
        sensor_key = 'T{}BPK'.format(str(i))
        SCPICMD(UV['ХНЭО_ТД_ДД'], AsciiHex('0x{}00 {} 0000 0000'.format(s2h(sensor[sensor_key]), b2h(temp_value))))
        print('Выдано УВ на задание температуры -5 градусов датчика {}'.format(sensor_key))
        time.sleep(1)
    time.sleep(10)
    DROP_DI()
    for i in (1, 2):
        temp_med_value = Ex.get('ТМИ', '01.01.TKR{}BPKMED'.format(str(i)), 'КАЛИБР ТЕКУЩ')
        for j in (1, 2, 3):
            temp_key = 'T{}KR{}BPK'.format(str(j), str(i))
            print('{} == {}'.format(temp_key, Ex.get('ТМИ', '01.03.{}'.format(temp_key), 'НЕКАЛИБР ТЕКУЩ')))
        if temp_med_value == temp_value:
            gprint('Медианная температура TKR{}BPKMED == {}'.format(i, temp_med_value))
        else:
            rprint('Медианная температура TKR{}BPKMED == {}'.format(i, temp_med_value))
        if 200 <= temp_med_value <= 255:
            continue
        else:
            rprint('Медианная температура > 0')
            return

    for bpk_num in ['1', '2']:
        SCPICMD(UV['ХНГРД{}'.format(bpk_num)])
        print('Выдано УВ на включение НГРД{}'.format(bpk_num))
        time.sleep(10)
        state = Ex.get('ТМИ', '01.01.NGRD{}'.format(bpk_num), 'НЕКАЛИБР ТЕКУЩ')
        if state == 1:
            gprint('Состояние нагревателя НГРД{} = {}'.format(bpk_num, state))
        else:
            rprint('Состояние нагревателя НГРД{} = {}'.format(bpk_num, state))
            return
        if (mode == 'ВКЛ') and (duk_ban_control == 'ВКЛ'):
            diWait('01.01.NSh0KR{}'.format(bpk_num), 1, 120)
            diWait('01.01.NGRD{}'.format(bpk_num), 0, 20)
            diWait('01.01.DUK_ZAPRET', 1, 20)
        elif (mode == 'ВКЛ') and (duk_ban_control == 'ОТКЛ'):
            diWait('01.01.NSh0KR{}'.format(bpk_num), 1, 120)
            diWait('01.01.NGRD{}'.format(bpk_num), 0, 20)
            diWait('01.01.DUK_ZAPRET', 0, 20)
        else:
            time.sleep(100)
            diWait('01.01.NSh0KR{}'.format(bpk_num), 0, 20)
            diWait('01.01.NGRD{}'.format(bpk_num), 1, 20)
            diWait('01.01.DUK_ZAPRET', 0, 20)
    SCPICMD(UV['ХОНГРД'])
    time.sleep(1)
    SCPICMD(UV['ХДАТЧИК_СБРОС'])
    time.sleep(1)
    print('Выданы УВ на отключение НГРД и сброс установленных значений датчиков температуры')
    setTioValue()
    setDukBanControl('ВКЛ')
    SCPICMD(UV['ХАНАЛИЗ_НШ0'], AsciiHex('0x0000 0000 0000 0000'))
    print('Выдано УВ на включение анализа НШ0КР1 и НШ0КР2')
    time.sleep(10)
    print_kr_analizys()
    print('Проверка НШ0 завершена')
    input('Для продолжения нажмите Enter')
    return


def emergencyPressureRelease(mode, bpk):
    yprint('Проверка функционирования циклограммы аварийного сброса давления рабочего тела')

    if bpk == 'BPK1':
        dn_sens = 0x18
    else:
        dn_sens = 0x19
    bpk_num = bpk[3]

    if mode == 'ВКЛ':
        yprint('Проверка при включенном контроле ДНБПК')
        SCPICMD(UV['ХДНБПК_ВКЛ'])
        print('Выдано УВ на включение контроля давления БПК')
        diWait('01.01.DNBPK_KONTR', 1, 20)
    else:
        yprint('Проверка при отключенном контроле ДНБПК')
        SCPICMD(UV['ХДНБПК_ОТКЛ'])
        print('Выдано УВ на отключение контроля давления БПК')
        diWait('01.01.DNBPK_KONTR', 0, 20)
    DROP_DI()
    nizh_dn_bpk = Ex.get('ТМИ', '01.29.NIZH_DN_BPK', 'КАЛИБР ТЕКУЩ')
    verh_dn_bpk = Ex.get('ТМИ', '01.29.VERH_DN_BPK', 'КАЛИБР ТЕКУЩ')
    print('Нижний порог стравливания = {} кгс/см^2'.format(nizh_dn_bpk))
    print('Верхний порог стравливания = {} кгс/см^2'.format(verh_dn_bpk))

    SCPICMD(UV['ХНЭО_ТД_ДД'], AsciiHex('0x{}00 0001 0000 0000'.format(b2h(dn_sens))))  # ДНБПК
    time.sleep(10)
    dnbpk = Ex.get('ТМИ', '01.01.DN{}BPK'.format(bpk_num), 'КАЛИБР ТЕКУЩ')
    print('DN{}BPK == {}'.format(bpk_num, dnbpk))
    mdkr = Ex.get('ТМИ', '01.01.MDKR{}'.format(bpk_num), 'НЕКАЛИБР ТЕКУЩ')
    print('MDKR{} == {}'.format(bpk_num, mdkr))
    print('Последнее выполненное УВ == ' + str(Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ТЕКУЩ')))

    SCPICMD(UV['ХНЭО_ТД_ДД'], AsciiHex('0x{}00 0002 0000 0000'.format(b2h(dn_sens))))
    time.sleep(10)
    dnbpk = Ex.get('ТМИ', '01.01.DN{}BPK'.format(bpk_num), 'КАЛИБР ТЕКУЩ')
    print('DN{}BPK == {}'.format(bpk_num, dnbpk))

    if mode == 'ВКЛ':
        diWait('01.01.MDKR{}'.format(bpk_num), 1, 20)
        time.sleep(5)
    else:
        time.sleep(15)
        diWait('01.01.MDKR{}'.format(bpk_num), 0, 20)

    SCPICMD(UV['ХНЭО_ТД_ДД'], AsciiHex('0x{}00 0001 0000 0000'.format(b2h(dn_sens))))
    time.sleep(10)
    dnbpk = Ex.get('ТМИ', '01.01.DN{}BPK'.format(bpk_num), 'КАЛИБР ТЕКУЩ')
    print('DN{}BPK == {}'.format(bpk_num, dnbpk))
    diWait('01.01.MDKR{}'.format(bpk_num), 0, 20)
    time.sleep(10)
    vyp_uv_list = Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ИНТЕРВАЛ')
    if mode == 'ВКЛ':
        res_cyclogram = deepcopy(cyclogram['МДКР'])
        res_cyclogram[1] = uvNum(UV['ХСПУ{}'.format(bpk_num)])
        res_cyclogram[2] = uvNum(UV['Х{}БПК'.format(str(int(bpk_num) * 3))])
    else:
        res_cyclogram = []
    checkUvList(res_cyclogram, vyp_uv_list)

    SCPICMD(UV['ХДАТЧИК_СБРОС'])
    time.sleep(1)
    setTioValue()

    print('Проверка срабатывыния МДКР завершена')
    input('Для продолжения нажмите Enter')
    return


def heaterFailure(bk, k, bpk):
    bk_num = bk[2]
    k_num = k[1]
    bpk_num = bpk[3]

    NGRD_AVTO, NAD, TAD, TND, TRRD, DNBPK, DVBPK, STZA, EP, BK, K, BPK, BK_TV, BKK_VREMYa, NSH, notusedBK_TV = setVariableDI(
        bk, k, bpk, 'NSh3')

    irk_num = {

        'BK1K1': (0x02, 0x00),
        'BK1K2': (0x04, 0x00),
        'BK2K1': (0x00, 0x01),
        'BK2K2': (0x00, 0x02)

    }

    print('Выдача ИРК в ЭИБК{} на отключение цепи питания катода К{}'.format(bk_num, k_num))
    SICCELL('Импульс', out=[irk_num[bk + k][0], irk_num[bk + k][1]])
    time.sleep(5)
    RK('ХТНД')
    time.sleep(20)
    diWait('01.01.NSh3{}{}'.format(k, bk), 1, 30)
    diWait('01.01.KDU_SOST', 3, 10)
    nsh3k1 = Ex.get('ТМИ', '01.01.NSh3K1{}'.format(bk), 'НЕКАЛИБР ТЕКУЩ')
    nsh3k2 = Ex.get('ТМИ', '01.01.NSh3K2{}'.format(bk), 'НЕКАЛИБР ТЕКУЩ')
    if (nsh3k1 == 1) and (nsh3k2 == 1):
        print('Зарегистрирован отказ нагревателей обоих катодов')
        diWait('01.01.NSh4{}'.format(bk), 1, 10)
    print('Ожидание приведения ДУК в режим РХ')
    rh = diWait('01.01.VYP_UV_KPDU', uvNum(UV['ХДУК_Ц2']),
                15)  # Возможно, придется поменять контролируемое УВ на ХОБПП, если не увидит ХДУК_Ц2
    if rh == 1:
        gprint('ДУК приведен в режим РХ')
    else:
        rprint('ДУК не переведен в режим РХ')
        modeRH()
    print('Выдача ИРК на включение цепи питания катода')
    SICCELL('Импульс', out=[0x08, 0x00])
    SICCELL('Импульс', out=[0x00, 0x04])
    dukZapretCheck()
    setInitialStateValues()
    print('Проверка с НШ3{}{} завершена'.format(bk, k))
    input('Для продолжения нажмите Enter')
    return


def sublaunch(bk, k, bpk, nsh):
    if nsh != 'NSh4':
        nsh = None

    bk_num = bk[2]

    NGRD_AVTO, NAD, TAD, TND, TRRD, DNBPK, DVBPK, STZA, EP, BK, K, BPK, BK_TV, BKK_VREMYa, NSH, notusedBK_TV = setVariableDI(
        bk, k, bpk, nsh)

    print('Проверка подзапусков ДУК')
    input('Пауза. Для продолжения нажмите Enter')
    RK('ХНАД')
    DI['DI1']['01.01.{}'.format(NGRD_AVTO)]['@H'] = '[0,1]'
    set_5HzTMI_value(K, '[0, 1]')
    set_5HzTMI_value(NAD, '[0, 34000]')  # ПРЕДВАРИТЕЛЬНО ПРОВЕРИТЬ ДАННЫЙ КУСОК ПРИ ШТАТНОМ ВКЛЮЧЕНИИ
    set_5HzTMI_value(TAD, '[0, 150]')  # ВОЗМОЖНЫ ПРАВКИ -- СРАЗУ ВЫСТАВИТЬ ЗНАЧЕНИЯ ДЛЯ РЕЖИМА РД
    set_5HzTMI_value(TND, '[0, 1250]')
    set_5HzTMI_value(TRRD, '[0, 400]')
    set_5HzTMI_value('TBPP', '[0, 2200]')
    set_5HzTMI_value(EP, '[0, 1]')
    DI['DI1']['01.01.KDU_SOST']['@H'] = '0'
    DI['DI1']['01.01.REZH_DUK']['@H'] = '[0, 3]'
    #    DI['DI2']['01.02.BK{}K1_ZAPRET'.format(bk_num)]['@H'] = '[0, 1]'
    #    DI['DI2']['01.02.BK{}K2_ZAPRET'.format(bk_num)]['@H'] = '[0, 1]'
    controlGetEQ(equationDUK(), count=2, period=0, downBCK=True)
    if nsh == 'NSh4':
        print('Ожидание срабатывания НШ4')
        diWait('01.01.{}'.format(NSH), 1, 140)
        setCountdownEnd(bk, k)
        diWait('01.01.KDU_SOST', 3, 10)
        print('Ожидание приведения ДУК в режим РХ')
        rh = diWait('01.01.VYP_UV_KPDU', uvNum(UV['ХДУК_Ц2']),
                    15)  # Возможно, придется поменять контролируемое УВ на ХОБПП, если не увидит ХДУК_Ц2
        if rh == 1:
            gprint('ДУК приведен в режим РХ')
        else:
            rprint('ДУК не переведен в режим РХ')
            modeRH()
        dukZapretCheck()
        diWait('01.01.KDU_SOST', 0, 60)
        setInitialStateValues()
        controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
        print('Проверка подзапуска с НШ4{}{} завершена'.format(k, bk))
        input('Пауза. Для продолжения нажмите Enter')
        return
    else:
        yprint('Установите на ЭИБК{} ток разряда ТАД БОЛЬШЕ 1.5 А'.format(bk_num))
        input('Пауза. Для продолжения нажмите Enter')
    return


def invalidCathodeMode(bk, k, bpk, nsh):
    current_nsh1_value = Ex.get('ТМИ', '01.01.{}'.format(nsh), 'НЕКАЛИБР ТЕКУЩ')
    bk_num = bk[2]
    DROP_DI()
    time.sleep(3)
    Ex.get('ТМИ', '01.01.REZH_DUK', 'НЕКАЛИБР ТЕКУЩ')
    Ex.get('ТМИ', '01.04.TAD{}'.format(bk_num), 'НЕКАЛИБР ТЕКУЩ')
    Ex.get('ТМИ', '01.04.STZA{}'.format(bk_num), 'НЕКАЛИБР ТЕКУЩ')
    yprint('Переключите на ЭИБК{} тумблер ТОК ОГРАНИЧЕНИЯ в положение ВКЛ'.format(bk))
    input('Пауза. Для продолжения нажмите Enter')
    SCPICMD(UV['БЦК_СБРОС_ПАМЯТИ'])
    print('Ожидание приведения ДУК в режим РХ')
    rh = diWait('01.01.VYP_UV_KPDU', uvNum(UV['ХДУК_Ц2']), 200)
    setCountdownEnd(bk, k)
    diWait('01.04.{}'.format(bpk), 0, 200)
    if rh == 1:
        gprint('ДУК приведен в режим РХ')
    else:
        rprint('ДУК не переведен в режим РХ')
        modeRH()

    rezh_duk_list = Ex.get('ТМИ', '01.01.REZH_DUK', 'НЕКАЛИБР ИНТЕРВАЛ')
    tad_list = Ex.get('ТМИ', '01.04.TAD{}'.format(bk_num), 'НЕКАЛИБР ИНТЕРВАЛ')
    stza_list = Ex.get('ТМИ', '01.04.STZA{}'.format(bk_num), 'НЕКАЛИБР ИНТЕРВАЛ')
    if 5 in rezh_duk_list:
        gprint('Зарегистрирован режим ОМРД')
    else:
        rprint('Режим ОМРД не зарегистрирован')
    if 1 in stza_list:
        gprint('СТЗА{} зарегистрирован'.format(bk_num))
    else:
        rprint('СТЗА{} не зарегистрирован'.format(bk_num))
    counter = 0
    for i in tad_list:
        if i >= 6.2:
            counter += 1
    '''
    if 1 <= counter <= 4:
        gprint('Режим ОМРД длился от 2 до 4 с')
    else:
        rprint('Длительность режима ОМРД не соответствует требуемой')
    '''
    result_nsh1_value = Ex.get('ТМИ', '01.01.{}'.format(nsh), 'НЕКАЛИБР ТЕКУЩ')
    if result_nsh1_value == current_nsh1_value + 1:
        gprint('Значение {} увеличилось == {}'.format(nsh, result_nsh1_value))
    else:
        rprint('Значение {} не увеличилось == {}'.format(nsh, result_nsh1_value))
    nsh2 = Ex.get('ТМИ', '01.01.NSh2{}{}'.format(k, bk), 'НЕКАЛИБР ТЕКУЩ')
    if result_nsh1_value == 3:
        print('Количество зарегистрированных {} == 3'.format(nsh))
        if Ex.get('ТМИ', '01.01.NSh2{}{}'.format(k, bk), 'НЕКАЛИБР ТЕКУЩ') == 1:
            gprint('Зарегистрирована NSh2{}{} Отказ катода'.format(k, bk))
            if (Ex.get('ТМИ', '01.01.NSh2K1{}'.format(bk), 'НЕКАЛИБР ТЕКУЩ') == 1) and (
                    Ex.get('ТМИ', '01.01.NSh2K2{}'.format(bk), 'НЕКАЛИБР ТЕКУЩ') == 1):
                print('Зарегистрирован отказ обоих катодов {}'.format(bk))
                if Ex.get('ТМИ', '01.01.NSh4{}'.format(bk), 'НЕКАЛИБР ТЕКУЩ') == 1:
                    gprint('Зарегистрирована NSh4{0} отказ {0}'.format(bk))
                else:
                    rprint('Отказ {} не зарегистрирован'.format(bk))
        else:
            rprint('Отказ катода {} {} не зарегистрирован'.format(k, bk))
    dukZapretCheck()
    time.sleep(40)
    setInitialStateValues()
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    print('Проверка срабатывания NSh1{}{} завершена'.format(k, bk))
    input('Для продолжения нажмите Enter')
    return


def exchangeInterruption(bk, k, mkpd_kontr):
    print('ПРОВЕРКА НАРУШЕНИЯ ОБМЕНА БЦК и КПДУ')
    if mkpd_kontr == None:
        print('Контроль обмена: 0 -- отключить, 1 -- включить')
        mkpd_kontr = input('Введите значение - ')
    if mkpd_kontr == '0':
        SCPICMD(UV['ХМКПД_ОТКЛ'])
        print('Выдано УВ на отключение контроля информационного обмена')
        DI['DI1']['01.01.MKPD_KONTR']['@H'] = '0'
    else:
        SCPICMD(UV['ХМКПД_ВКЛ'])
        print('Выдано УВ на включение контроля информационного обмена')
        DI['DI1']['01.01.MKPD_KONTR']['@H'] = '1'
    time.sleep(10)

    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')
    print('KPDU_OBMEN = {}'.format(kpdu_obmen))
    while True:
        print("ОСТАНОВКА ОБМЕНА БЦК И КПДУ!")
        SCPICMD(0xE06F, AsciiHex('0x0100 0000 0000 0000'))
        input('Для продолжения нажмите Enter')
        time.sleep(10)
        kpdu_vremya = Ex.get('ТМИ', '01.01.KPDU_VREMYa', 'НЕКАЛИБР ТЕКУЩ')
        time.sleep(3)
        if kpdu_vremya == Ex.get('ТМИ', '01.01.KPDU_VREMYa', 'НЕКАЛИБР ТЕКУЩ'):
            print("ОБМЕН ОСТНОВЛЕН!")
            print("ВКЛЮЧЕНИЕ ОБМЕНА БЦК И КПДУ")
            break
        else:
            print("ОБМЕН НЕ ОСТНОВЛЕН!")

    time.sleep(10)

    SCPICMD(0xE06F, AsciiHex('0x0101 0000 0000 0000'))
    while True:
        kpdu_vremya = Ex.get('ТМИ', '01.01.KPDU_VREMYa', 'НЕКАЛИБР ТЕКУЩ')
        time.sleep(3)
        if kpdu_vremya != Ex.get('ТМИ', '01.01.KPDU_VREMYa', 'НЕКАЛИБР ТЕКУЩ'):
            print("ОБМЕН ВКЛЮЧЕН!")
            break
        else:
            continue
    if mkpd_kontr == '1':
        setInitialStateValues()
        DI['DI1']['01.01.KPDU_OBMEN']['@H'] = '1'
        DI['DI1']['01.01.DUK_AVTO']['@H'] = '0'
        DI['DI1']['01.01.DUK_ZAPRET']['@H'] = '1'
        DI['DI1']['01.01.REZH_DUK']['@H'] = '1'
        DI['DI1']['01.01.KDU_SOST']['@H'] = '3'
        controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    else:
        DI['DI1']['01.01.KPDU_OBMEN']['@H'] = '1'
        DI['DI1']['01.01.KDU_SOST']['@H'] = '3'
        controlGetEQ(equationDUK(), count=2, period=0, downBCK=True)
        modeRH()
    setCountdownEnd(bk, k)
    print('Проверка нарушения обмена КПДУ завершена')
    SCPICMD(UV['ХДУК_ТВ_ПРЕД'], AsciiHex('0x{} 0000 0000 0000'.format(s2h(time_pred))))
    print('Установлено предельное время тяги ДУК == {} с'.format(time_pred))
    time.sleep(10)
    setInitialStateValues()
    input('Для продолжения нажмите Enter')
    return


def setDukConfigValue_cyclo(bk, k, bpk):
    config_dict = {
        'BK1K1BPK1': 0,
        'BK1K2BPK1': 1,
        'BK2K1BPK1': 3,
        'BK2K2BPK1': 3,
        'BK1K1BPK2': 4,
        'BK1K2BPK2': 5,
        'BK2K1BPK2': 6,
        'BK2K2BPK2': 7
    }
    return config_dict[bk + k + bpk]


cyclogram = {
    'ХДУК_Ц1': [
        uvNum(UV['ХБПП']),
        uvNum(UV['ХСПУ1']),
        uvNum(UV['ХК1']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['ХК2']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['Х1БПК']),
        uvNum(UV['ХОД']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХСПУ2']),
        uvNum(UV['ХК1']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['ХК2']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['Х2БПК']),
        uvNum(UV['ХОД']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХСПУ1']),
        uvNum(UV['ХПК']),
        uvNum(UV['Х1БПК']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХК1']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['ХОД']),
        uvNum(UV['Х2БПК']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХОБПП']),
        uvNum(UV['ХДУК_Ц1'])  # проверить
    ],
    'ХДУК_Ц2': [
        uvNum(UV['ХБПП']),
        uvNum(UV['ХСПУ1']),
        uvNum(UV['ХОД']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХСПУ2']),
        uvNum(UV['ХОД']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХОБПП']),
        uvNum(UV['ХДУК_Ц2'])  # проверить
    ],
    'ХДУК_Ц3': [
        uvNum(UV['ХОД']),
        uvNum(UV['ХТНД']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['ХЭПД']),
        uvNum(UV['ХНАД']),
        uvNum(UV['ХДУК_Ц3'])  # проверить
    ],
    'ХДУК_Ц4': [
        uvNum(UV['ХБПП']),
        (uvNum(UV['ХСПУ1']), uvNum(UV['ХСПУ2'])),
        (uvNum(UV['ХК1']), uvNum(UV['ХК2'])),
        (uvNum(UV['Х1БПК']), uvNum(UV['Х2БПК'])),
        uvNum(UV['ХТНД']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['ХЭПД']),
        uvNum(UV['ХНАД']),
        uvNum(UV['ХОД']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХОБПП']),
        uvNum(UV['ХДУК_Ц4'])  # проверить
    ],
    'ХВКЛ_КДУ': [
        uvNum(UV['ХБПП']),
        (uvNum(UV['ХСПУ1']), uvNum(UV['ХСПУ2'])),
        (uvNum(UV['ХК1']), uvNum(UV['ХК2'])),
        (uvNum(UV['Х1БПК']), uvNum(UV['Х2БПК'])),
        uvNum(UV['ХТНД']),
        uvNum(UV['ХЭКД']),
        uvNum(UV['ХЭПД']),
        uvNum(UV['ХНАД']),
        uvNum(UV['ХОД']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХОБПП']),
        uvNum(UV['ХВКЛ_КДУ'])  # проверить
    ],
    'МДКР': [
        uvNum(UV['ХБПП']),
        (uvNum(UV['ХСПУ1']), uvNum(UV['ХСПУ2'])),
        (uvNum(UV['Х3БПК']), uvNum(UV['Х6БПК'])),
        uvNum(UV['ХНЭО_ТД_ДД']),
        uvNum(UV['ХОБПК']),
        uvNum(UV['ХОСПУ']),
        uvNum(UV['ХОБПП'])
    ]
}

cyclogram_pause = {
    'ХДУК_Ц1': 10930,
    'ХДУК_Ц2': 22,
    'ХДУК_Ц3': 16,
    'ХДУК_Ц4': 187  # Время паузы до первого ХНАД
}


def cyclogramChoice():
    print('Ц1 - РНП, Ц2 - РХ, Ц3 - ПОДЗАПУСК, Ц4 - ЗАПУСК')
    cyclo_dict = {
        '1': 'ХДУК_Ц1',
        '2': 'ХДУК_Ц2',
        '3': 'ХДУК_Ц3',
        '4': 'ХДУК_Ц4'
    }
    print(cyclo_dict)
    return cyclo_dict[input('Введите номер - ')]


def checkUvList(cyclo_list, uv_list):
    if len(cyclo_list) == len(uv_list):
        if uv_list == []:
            gprint('Выполненных УВ не зарегистрировано')
        else:
            gprint('Количество выполненных УВ соответствует количеству УВ циклограммы')
            for i in range(0, len(uv_list)):
                if cyclo_list[i] == uv_list[i]:
                    gprint('{0} УВ циклограммы == {1}, {0} УВ выполненное == {2}'.format(i, cyclo_list[i], uv_list[i]))
                else:
                    rprint('{0} УВ циклограммы == {1}, {0} УВ выполненное == {2}'.format(i, cyclo_list[i], uv_list[i]))
    else:
        rprint('Количество выполненных УВ не соответствует количеству УВ циклограммы')
        print('Список УВ циклограммы: \n', cyclo_list)
        print('Список выполненных УВ: \n', uv_list)
    return


def setDukConfigValue_avto(bk, k, bpk):
    config_dict = {
        'BK1K1BPK1': 1,
        'BK1K2BPK1': 17,
        'BK2K1BPK1': 33,
        'BK2K2BPK1': 49,
        'BK1K1BPK2': 65,
        'BK1K2BPK2': 81,
        'BK2K1BPK2': 97,
        'BK2K2BPK2': 113
    }
    return config_dict[bk + k + bpk]


def clearNsh():
    SCPICMD(UV['ХНШ_СБРОС'])
    print('Выдано УВ на сброс НШ')
    diWait('01.01.VYP_UV_KPDU', uvNum(UV['ХНШ_СБРОС']), 20)
    return


def avtoLaunchDuk(bk, k, bpk, *args):
    DROP_DI()
    bk2_tv = 0
    bkk_ban = Ex.get('ТМИ', '01.02.{}{}_ZAPRET'.format(bk, k), 'НЕКАЛИБР ТЕКУЩ')
    time_vkl = 600
    duk_zapret = Ex.get('ТМИ', '01.01.DUK_ZAPRET', 'НЕКАЛИБР ТЕКУЩ')
    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')
    duk_avto = Ex.get('ТМИ', '01.01.DUK_AVTO', 'НЕКАЛИБР ТЕКУЩ')

    if ('НЕВЫПОЛНЕНИЕ' in args) and ((duk_zapret == 1) or (kpdu_obmen == 1) or (duk_avto == 0) or (bkk_ban == 1)):
        yprint('ПРОВЕРКА НЕЗАПУСКА ДУК {} В АВТОМАТИЧЕСКОМ РЕЖИМЕ'.format(bk + k + bpk))
    elif not 'НЕВЫПОЛНЕНИЕ' in args:
        if not 'ПРЕРЫВАНИЕ' in args:
            yprint('ПРОВЕРКА ВКЛЮЧЕНИЯ ДУК {} В АВТОМАТИЧЕСКОМ РЕЖИМЕ НА {} С'.format(bk + k + bpk, time_vkl))
        else:
            yprint('ПРОВЕРКА ВКЛЮЧЕНИЯ ДУК {} В АВТОМАТИЧЕСКОМ РЕЖИМЕ')
            yprint('ПРЕРЫВАНИЕ ЦИКЛОГРАММОЙ РХ')
        resetBan()
    else:
        yprint('ПРОВЕРКА НЕЗАПУСКА НЕ МОЖЕТ БЫТЬ ВЫПОЛНЕНА, Т.К. ДУК_ЗАПРЕТ И КПДУ_ОБМЕН == 0')
        yprint('ПРОВЕДИТЕ ПРОВЕРКУ СРАБАТЫВАНИЯ НШ ИЛИ НАРУШЕНИЯ ОБМЕНА')
        return
    if args != (None,):
        print(args)

    if not 'НЕВЫПОЛНЕНИЕ' in args:
        checkBkBan(bk, k)
    flag = 0
    if (('НЕВЫПОЛНЕНИЕ' in args) and ((duk_zapret == 1) or (kpdu_obmen == 1) or (bkk_ban == 1))) or (
            not 'НЕВЫПОЛНЕНИЕ' in args):
        flag = 1
        SCPICMD(UV['ХДУК_АВТО'])
        print('Выдано УВ ХДУК_АВТО')
    time.sleep(10)
    duk_avto = Ex.get('ТМИ', '01.01.DUK_AVTO', 'НЕКАЛИБР ТЕКУЩ')
    if (flag == 1 and duk_avto == 1) or (flag == 0 and duk_avto == 0):
        gprint('Автоматический режим ДУК == {}'.format(duk_avto))
    else:
        rprint('Автоматический режим ДУК == {}'.format(duk_avto))
        print('Остановка проверки')
        input('Для продолжения нажмите Enter')
        return
    config_value = setDukConfigValue_avto(bk, k, bpk)
    Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ТЕКУЩ')

    print(s2h(time_vkl), b2h(config_value))
    SCPICMD(UV['ХВКЛ_КДУ'], AsciiHex('0x{0} {1}00 0000 0000'.format(s2h(time_vkl), b2h(config_value))))
    time.sleep(30)
    DROP_DI()
    duk_tv_treb = Ex.get('ТМИ', '01.02.DUK_TV_TREB', 'НЕКАЛИБР ТЕКУЩ')
    if 'НЕВЫПОЛНЕНИЕ' in args:
        if duk_tv_treb == 0:
            gprint('Требуемое время тяги ДУК == 0')
        else:
            rprint('Требуемое время тяги ДУК != 0. DUK_TV_TREB == {}'.format(duk_tv_treb))
            modeRH()
            return
    else:
        if duk_tv_treb == time_vkl:
            gprint('Требуемое время задано верно == {}'.format(duk_tv_treb))
            yprint('После индикации КД{} на ЭИБК{} установите ток разряда больше 1.5 А'.format(k[1], bk[2]))
            yprint('Затем установите ток разряда от 4.4 А до 4.6 А')
        else:
            rprint('Требуемое время задано не верно== {}'.format(duk_tv_treb))
            modeRH()
            return
    if 'ПРЕРЫВАНИЕ' in args:
        time.sleep(220)
        SCPICMD(UV['ХДУК_Ц2'])
        Ex.get('ТМИ', '01.01.BK2_TV', 'НЕКАЛИБР ТЕКУЩ')
        time.sleep(cyclogram_pause['ХДУК_Ц2'])
    elif 'НЕВЫПОЛНЕНИЕ' in args:
        time.sleep(10)
    else:
        time.sleep(800)
    time.sleep(15)
    vyp_uv_list = Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ИНТЕРВАЛ')
    if not 'НЕВЫПОЛНЕНИЕ' in args:
        setCountdownEnd(bk, k)
    bk2_tv_list = Ex.get('ТМИ', '01.01.BK2_TV', 'НЕКАЛИБР ИНТЕРВАЛ')
    if bk2_tv_list != []:
        bk2_tv = max(bk2_tv_list)
    res_cyclogram = deepcopy(cyclogram['ХВКЛ_КДУ'])
    res_cyclogram[1] = uvNum(UV['ХСПУ{}'.format(bk[2])])
    res_cyclogram[2] = uvNum(UV['ХК{}'.format(k[1])])
    res_cyclogram[3] = uvNum(UV['Х{}БПК'.format(bpk[3])])
    if 'ПРЕРЫВАНИЕ' in args:
        del res_cyclogram[len(res_cyclogram) - 5:len(res_cyclogram)]
        res_cyclogram += cyclogram['ХДУК_Ц2']
    elif 'НЕВЫПОЛНЕНИЕ' in args:
        if (kpdu_obmen == 1):
            res_cyclogram = []
        else:
            res_cyclogram = [uvNum(UV['ХВКЛ_КДУ'])]
    checkUvList(res_cyclogram, vyp_uv_list)
    DROP_DI()
    if bk == 'BK1':
        notused_bk = 'BK2'
    else:
        notused_bk = 'BK1'
    bk_tv = Ex.get('ТМИ', '01.01.{}_TV'.format(bk), 'НЕКАЛИБР ТЕКУЩ')
    notused_bk_tv = Ex.get('ТМИ', '01.01.{}_TV'.format(notused_bk), 'НЕКАЛИБР ТЕКУЩ')

    if 'ПРЕРЫВАНИЕ' in args:
        if bk == 'BK1':
            if bk_tv != 0:
                gprint('Время включения ДУК на {} == {}'.format(bk, bk_tv))
            else:
                rprint('Время включения ДУК на {} == {}'.format(bk, bk_tv))
        elif bk == 'BK2':
            if bk2_tv != 0:
                gprint('Время включения ДУК на {} == {}'.format(bk, bk2_tv))
            else:
                rprint('Время включения ДУК на {} == {}'.format(bk, bk2_tv))
    elif not 'НЕВЫПОЛНЕНИЕ' in args:
        if bk_tv == duk_tv_treb:
            gprint('Время включения ДУК на {} соответствует требуемому == {}'.format(bk, bk_tv))
        else:
            rprint('Время включения ДУК на {} не соответствует требуемому == {}'.format(bk, bk_tv))
    if not 'НЕВЫПОЛНЕНИЕ' in args:
        if notused_bk_tv == 0:
            gprint('Время включения ДУК на {} == {}'.format(notused_bk, notused_bk_tv))
        else:
            rprint('Время включения ДУК на {} == {}'.format(notused_bk, notused_bk_tv))

    print('Проверка включения ДУК через ХВКЛ_КДУ завершена')
    yprint('Приведите органы управления на ЭИБК{} в исходное положение'.format(bk[2]))
    input('Для продолжения нажмите Enter')
    return


def cyclogramDuk(cyclogram_key, *args, bk=None, k=None, bpk=None):
    bk2_tv_list = [0]
    duk_zapret = Ex.get('ТМИ', '01.01.DUK_ZAPRET', 'НЕКАЛИБР ТЕКУЩ')
    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')
    duk_avto = Ex.get('ТМИ', '01.01.DUK_AVTO', 'НЕКАЛИБР ТЕКУЩ')
    if ('НЕВЫПОЛНЕНИЕ' in args) and ((duk_zapret == 1) or (kpdu_obmen == 1)):
        yprint('ПРОВЕРКА НЕЗАПУСКА ЦИКЛОГРАММЫ ДУК {}'.format(cyclogram_key))
    elif not 'НЕВЫПОЛНЕНИЕ' in args:
        if 'ПРЕРЫВАНИЕ' in args:
            yprint('ПРОВЕРКА ЦИКЛОГРАММЫ {}'.format(cyclogram_key))
        else:
            yprint('ПРОВЕРКА ЦИКЛОГРАММЫ {}'.format(cyclogram_key))

        resetBan()
    else:
        yprint('ПРОВЕРКА НЕЗАПУСКА НЕ МОЖЕТ БЫТЬ ВЫПОЛНЕНА, Т.К. ДУК_ЗАПРЕТ И КПДУ_ОБМЕН == 0')
        yprint('ПРОВЕДИТЕ ПРОВЕРКУ СРАБАТЫВАНИЯ НШ ИЛИ НАРУШЕНИЯ ОБМЕНА')
        return
    if (bk != None) and (k != None) and (bpk != None):
        yprint('{}'.format(bk + k + bpk))
    if args != (None,):
        print(args)

    duk_tv_pred = Ex.get('ТМИ', '01.02.DUK_TV_PRED', 'НЕКАЛИБР ТЕКУЩ')
    pause_rh = 60
    time.sleep(10)
    config_value = 0
    if (cyclogram_key == 'ХДУК_Ц4') and (bk == None) and (k == None) and (bpk == None):
        bk, k, bpk = setDukConfig()
    if cyclogram_key == 'ХДУК_Ц4':
        print('Включение конфигурации {}{}{}'.format(bk, k, bpk))
        config_value = setDukConfigValue_cyclo(bk, k, bpk)
        if not 'НЕВЫПОЛНЕНИЕ' in args:
            checkBkBan(bk, k)
            yprint('После индикации КД{} на ЭИБК{} установите ток разряда больше 1.5 А'.format(k[1], bk[2]))
            yprint('Затем установите ток разряда от 4.4 А до 4.6 А')
    print('Последнее выполненное УВ = ' + str(Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ТЕКУЩ')))
    SCPICMD(UV[cyclogram_key], AsciiHex('0x{}00 0000 0000 0000'.format(b2h(config_value))))
    if 'НЕВЫПОЛНЕНИЕ' in args:
        time.sleep(10)
    else:
        time.sleep(cyclogram_pause[cyclogram_key])
        if (cyclogram_key == 'ХДУК_Ц4') and ('ПРЕРЫВАНИЕ' in args):
            time.sleep(pause_rh)
            SCPICMD(UV['ХДУК_Ц2'])
            Ex.get('ТМИ', '01.01.BK2_TV', 'НЕКАЛИБР ТЕКУЩ')
            time.sleep(cyclogram_pause['ХДУК_Ц2'] + pause_rh + 10)
        elif (cyclogram_key == 'ХДУК_Ц4'):
            time.sleep(cyclogram_pause['ХДУК_Ц2'] + duk_tv_pred + 10)
    vyp_uv_list = Ex.get('ТМИ', '01.01.VYP_UV_KPDU', 'НЕКАЛИБР ИНТЕРВАЛ')
    bk2_tv_list = Ex.get('ТМИ', '01.01.BK2_TV', 'НЕКАЛИБР ИНТЕРВАЛ')
    if bk2_tv_list != []:
        bk2_tv = max(bk2_tv_list)
    if 'НЕВЫПОЛНЕНИЕ' in args:
        checkUvList([], vyp_uv_list)
    elif cyclogram_key != 'ХДУК_Ц4':
        checkUvList(cyclogram[cyclogram_key], vyp_uv_list)
    #    elif (cyclogram_key == 'ХДУК_Ц4'):
    else:
        setCountdownEnd(bk, k)
        res_cyclogram = deepcopy(cyclogram['ХДУК_Ц4'])
        res_cyclogram[1] = uvNum(UV['ХСПУ{}'.format(bk[2])])
        res_cyclogram[2] = uvNum(UV['ХК{}'.format(k[1])])
        res_cyclogram[3] = uvNum(UV['Х{}БПК'.format(bpk[3])])
        if 'ПРЕРЫВАНИЕ' in args:
            del res_cyclogram[len(res_cyclogram) - 5:len(res_cyclogram)]
            res_cyclogram += cyclogram['ХДУК_Ц2']
    #        checkUvList(res_cyclogram, vyp_uv_list)
    DROP_DI()
    if (cyclogram_key == 'ХДУК_Ц4') and (not 'НЕВЫПОЛНЕНИЕ' in args):
        if bk == 'BK1':
            notused_bk = 'BK2'
        else:
            notused_bk = 'BK1'
        bk_tv = Ex.get('ТМИ', '01.01.{}_TV'.format(bk), 'НЕКАЛИБР ТЕКУЩ')
        notused_bk_tv = Ex.get('ТМИ', '01.01.{}_TV'.format(notused_bk), 'НЕКАЛИБР ТЕКУЩ')

        if ('ПРЕРЫВАНИЕ' in args) and (cyclogram_key == 'ХДУК_Ц4'):
            if bk == 'BK1':
                if bk_tv != 0:
                    gprint('Время включения ДУК на {} == {}'.format(bk, bk_tv))
                else:
                    rprint('Время включения ДУК на {} == {}'.format(bk, bk_tv))
            elif bk == 'BK2':
                if bk2_tv != 0:
                    gprint('Время включения ДУК на {} == {}'.format(bk, bk2_tv))
                else:
                    rprint('Время включения ДУК на {} == {}'.format(bk, bk2_tv))
        elif cyclogram_key == 'ХДУК_Ц4':
            if bk_tv == duk_tv_pred:
                gprint('Время включения ДУК на {} соответствует предельному == {}'.format(bk, bk_tv))
            else:
                rprint('Время включения ДУК на {} не соответствует предельному == {}'.format(bk, bk_tv))
        if not 'НЕВЫПОЛНЕНИЕ' in args:
            if (notused_bk_tv == 0) and (cyclogram_key == 'ХДУК_Ц4'):
                gprint('Время включения ДУК на {} == {}'.format(notused_bk, notused_bk_tv))
            else:
                rprint('Время включения ДУК на {} == {}'.format(notused_bk, notused_bk_tv))
        yprint('Приведите органы управления на ЭИБК{} в исходное положение'.format(bk[2]))

    print('Проверка выполнения циклограммы {} завершена'.format(cyclogram_key))
    input('Для продолжения нажмите Enter')
    return


def manualLaunchDuk(bk, k, bpk, nsh, *args, mkpd_kontr=None):
    NGRD_AVTO, NAD, TAD, TND, TRRD, DNBPK, DVBPK, STZA, EP, BK, K, BPK, BK_TV, BKK_VREMYa, NSH, notusedBK_TV = setVariableDI(
        bk, k, bpk, nsh)

    mkpd_control = Ex.get('ТМИ', '01.01.MKPD_KONTR', 'НЕКАЛИБР ТЕКУЩ')
    kpdu_obmen = Ex.get('ТМИ', '01.01.KPDU_OBMEN', 'НЕКАЛИБР ТЕКУЩ')
    if nsh == None:
        nshp = ''
    else:
        nshp = nsh
    duk_zapret = Ex.get('ТМИ', '01.01.DUK_ZAPRET', 'НЕКАЛИБР ТЕКУЩ')
    if ('НЕВЫПОЛНЕНИЕ' in args) and (duk_zapret == 1):
        yprint('ПРОВЕРКА НЕЗАПУСКА ДУК {}'.format(bk + k + bpk))
        setInitialStateValues()
        dukZapret(bk, k)
        return
    elif not 'НЕВЫПОЛНЕНИЕ' in args:
        yprint('ПРОВЕРКА ВКЛЮЧЕНИЯ ДУК {} {}'.format(bk + k + bpk, nshp))
        checkBkBan(bk, k)
        resetBan()
        setInitialStateValues()
    else:
        yprint('ПРОВЕРКА НЕЗАПУСКА НЕ МОЖЕТ БЫТЬ ВЫПОЛНЕНА, Т.К. ДУК_ЗАПРЕТ И КПДУ_ОБМЕН == 0')
        yprint('ПРОВЕДИТЕ ПРОВЕРКУ СРАБАТЫВАНИЯ НШ ИЛИ НАРУШЕНИЯ ОБМЕНА')
        return
    if args != (None,):
        print(args)

    if 'НАРУШЕНИЕ ОБМЕНА' in args:
        time_pred_exch_int = 300
        SCPICMD(UV['ХДУК_ТВ_ПРЕД'], AsciiHex('0x{} 0000 0000 0000'.format(s2h(time_pred_exch_int))))
        print('Установлено предельное время тяги ДУК == {} с'.format(time_pred_exch_int))
        time.sleep(10)
        DI['DI2']['01.02.DUK_TV_PRED']['@H'] = '300'

    bk_num = bk[2]
    k_num = k[1]
    bpk_num = bpk[3]

    if ((kpdu_obmen == 1) and (mkpd_control == 0)):
        DI['DI1']['01.01.KDU_SOST']['@H'] = '3'

    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    RK('ХБПП')
    DI['DI1']['01.01.DUK_AVTO']['@H'] = '0'
    set_5HzTMI_value('NBPP', '[5950, 6060]')
    set_5HzTMI_value('RBPP', '1')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    RK('ХСПУ{}'.format(bk_num))
    time.sleep(1)
    RK('ХК{}'.format(k_num))
    set_5HzTMI_value(K, '1')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    RK('Х{}БПК'.format(bpk_num))
    set_5HzTMI_value(BPK, '1')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    if nsh == 'NSh3':
        heaterFailure(bk, k, bpk)
        return

    RK('ХТНД')
    DI['DI1']['01.01.{}'.format(NGRD_AVTO)]['@H'] = '1'
    set_5HzTMI_value(TND, '[1150, 1250]')
    set_5HzTMI_value(TRRD, '[140, 180]')
    set_5HzTMI_value('TBPP', '[0, 1200]')
    DI['DI1']['01.01.REZH_DUK']['@H'] = '3'
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    RK('ХЭКД')
    yprint('Проверьте наличие индикатора КД на ЭИБК{}'.format(bk_num))
    if 'ПОДЗАПУСК' in args:
        yprint('Установите на ЭИБК{} ток разряда ТАД МЕНЬШЕ 1.5 А'.format(bk_num))
    else:
        yprint('Установите на ЭИБК{} ток разряда ТАД БОЛЬШЕ 1.5 А'.format(bk_num))
    time.sleep(10)
    RK('ХЭПД')
    set_5HzTMI_value(EP, '1')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    if ('ПОДЗАПУСК' in args) and nsh == 'NSh4':
        sublaunch(bk, k, bpk, nsh)
        return
    elif ('ПОДЗАПУСК' in args) and nsh != 'NSh4':
        sublaunch(bk, k, bpk, nsh)
    else:
        RK('ХНАД')
    yprint('Установите на ЭИБК{} ток разряда ТАД от 4.4 до 4.6 А'.format(bk_num))
    input('Для продолжения нажмите Enter')
    set_5HzTMI_value(NAD, '[28300, 31500]')  # ПРЕДВАРИТЕЛЬНО ПРОВЕРИТЬ ДАННЫЙ КУСОК ПРИ ШТАТНОМ ВКЛЮЧЕНИИ
    set_5HzTMI_value(TAD, '[430, 470]')  # ВОЗМОЖНЫ ПРАВКИ -- СРАЗУ ВЫСТАВИТЬ ЗНАЧЕНИЯ ДЛЯ РЕЖИМА РД
    set_5HzTMI_value(TND, '[0, 20]')
    set_5HzTMI_value(TRRD, '[0, 400]')
    set_5HzTMI_value('TBPP', '[2000, 2700]')
    set_5HzTMI_value(EP, '0')
    if not ((kpdu_obmen == 1) and (mkpd_control == 0)):
        DI['DI1']['01.01.KDU_SOST']['@H'] = '1'
    DI['DI1']['01.01.REZH_DUK']['@H'] = '4'
    DI['DI1']['01.01.{}'.format(BK_TV)]['@H'] = '@unsame@all'
    DI['DI1']['01.01.{}'.format(notusedBK_TV)]['@H'] = '0'
    DI['DI2']['01.02.{}'.format(BKK_VREMYa)]['@H'] = '@unsame@all'
    controlGetEQ(equationDUK(), count=2, period=0, downBCK=True)

    if (nsh == 'NSh1') or (nsh == 'NSh2'):
        invalidCathodeMode(BK, K, BPK, NSH)
        return

    if 'НАРУШЕНИЕ ОБМЕНА' in args:
        exchangeInterruption(BK, K, mkpd_kontr)
        return

    time.sleep(5)
    RK('ХОД')
    time.sleep(7)
    DROP_DI()
    DI['DI1']['01.01.{}'.format(NGRD_AVTO)]['@H'] = '0'
    set_5HzTMI_value(K, '0')
    set_5HzTMI_value(NAD, '[0, 1000]')
    set_5HzTMI_value(TAD, '[0, 50]')
    set_5HzTMI_value(TRRD, '[0, 50]')
    set_5HzTMI_value('TBPP', '[0, 40]')
    if not ((kpdu_obmen == 1) and (mkpd_control == 0)):
        DI['DI1']['01.01.KDU_SOST']['@H'] = '0'
    DI['DI1']['01.01.REZH_DUK']['@H'] = '4'
    bk_tv = Ex.get('ТМИ', '01.01.{}'.format(BK_TV), 'НЕКАЛИБР ТЕКУЩ')
    DI['DI1']['01.01.{}'.format(BK_TV)]['@H'] = str(bk_tv)
    bkk_time = Ex.get('ТМИ', '01.02.{}'.format(BKK_VREMYa), 'НЕКАЛИБР ТЕКУЩ')
    DI['DI2']['01.02.{}'.format(BKK_VREMYa)]['@H'] = str(bkk_time)
    #    DI['DI2']['01.02.BK{}K1_ZAPRET'.format(bk_num)]['@H'] = '1'
    #    DI['DI2']['01.02.BK{}K2_ZAPRET'.format(bk_num)]['@H'] = '1'
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    setCountdownEnd(bk, k)

    RK('ХОБПК')
    DI['DI1']['01.01.REZH_DUK']['@H'] = '1'
    set_5HzTMI_value(BPK, '0')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    RK('ХОСПУ')
    time.sleep(1)
    RK('ХОБПП')
    set_5HzTMI_value('NBPP', '[0, 50]')
    set_5HzTMI_value('RBPP', '0')
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)

    setInitialStateValues()
    if kpdu_obmen == 1:
        DI['DI1']['01.01.KDU_SOST']['@H'] = '3'
    controlGetEQ(equationDUK(), count=1, period=0, downBCK=True)
    DI['DI1']['01.01.KDU_SOST']['@H'] = '1'
    yprint('Приведите ЭИБК{} в исхожное состояние'.format(bk_num))
    input('Для продолжения нажмите Enter')
    return


def setDukConfig():
    print('1 - БК1, 2 - БК2')
    bk = 'BK' + input('Введите номер - ')
    print('1 - К1, 2 - К2')
    k = 'K' + input('Введите номер - ')
    print('1 - БПК1, 2 - БПК2')
    bpk = 'BPK' + input('Введите номер - ')
    return bk, k, bpk


def setBranch():
    branch = {
        '1': 'ПОДЗАПУСК',
        '2': 'НЕВЫПОЛНЕНИЕ',
        '3': 'НАРУШЕНИЕ ОБМЕНА',
        '0': None
    }
    print(branch)
    while True:
        br = input('Введите номер - ')
        if br in branch.keys():
            return branch[br]
        print('Введено неверное значение')


def setNSh():
    nsh_dict = {
        '1': 'NSh1',
        '3': 'NSh3',
        '4': 'NSh4',
        '0': None
    }
    print(nsh_dict)
    while True:
        nsh = input('Введите номер - ')
        if nsh in nsh_dict.keys():
            return nsh_dict[nsh]
        print('Введено неверное значение')


def setCycloBranch():
    cyclo_branch_dict = {
        '1': 'ПРЕРЫВАНИЕ',
        '2': 'НЕВЫПОЛНЕНИЕ',
        '0': None
    }
    print(cyclo_branch_dict)
    while True:
        cyclo_br = input('Введите номер - ')
        if cyclo_br in cyclo_branch_dict.keys():
            return cyclo_branch_dict[cyclo_br]
        print('Введено неверное значение')


def setNsh0Mode():
    print('Включите или отключите контроль НШ0')
    nsh0_mode = {
        '1': 'ВКЛ',
        '2': 'ОТКЛ'
    }
    print(nsh0_mode)
    while True:
        mode = input('Введите номер - ')
        if mode in nsh0_mode.keys():
            return nsh0_mode[mode]
        print('Введено неверное значение')


def setDukZapretKontr():
    print('Включите или отключите контроль запрета ДУК')
    duk_zapret_kontr = {
        '1': 'ВКЛ',
        '2': 'ОТКЛ'
    }
    print(duk_zapret_kontr)
    while True:
        mode = input('Введите номер - ')
        if mode in duk_zapret_kontr.keys():
            return duk_zapret_kontr[mode]
        print('Введено неверное значение')


def setMdkrKontr():
    print('Включите или отключите контроль МДКР')
    mdkr_kontr = {
        '1': 'ВКЛ',
        '2': 'ОТКЛ'
    }
    print(mdkr_kontr)
    while True:
        mode = input('Введите номер - ')
        if mode in mdkr_kontr.keys():
            return mdkr_kontr[mode]
        print('Введено неверное значение')


def setBpkNum():
    print('Выберите ветвь БПК')
    bpk = {
        '1': 'BPK1',
        '2': 'BPK2'
    }
    print(bpk)
    while True:
        bpk_num = input('Введите номер - ')
        if bpk_num in bpk.keys():
            return bpk[bpk_num]
        print('Введено неверное значение')


class DUK(Device):
    cur = None

    @classmethod
    def on(cls, *args, **kwargs):
        kpdu_upr11 = Ex.get('ТМИ', '04.01.beKPDUU11', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_upr12 = Ex.get('ТМИ', '04.01.beKPDUU12', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_upr21 = Ex.get('ТМИ', '04.01.beKPDUU21', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_upr22 = Ex.get('ТМИ', '04.01.beKPDUU22', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_sil11 = Ex.get('ТМИ', '04.01.beKPDUS11', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_sil12 = Ex.get('ТМИ', '04.01.beKPDUS12', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_sil21 = Ex.get('ТМИ', '04.01.beKPDUS21', 'НЕКАЛИБР ТЕКУЩ')
        kpdu_sil22 = Ex.get('ТМИ', '04.01.beKPDUS22', 'НЕКАЛИБР ТЕКУЩ')
        spu_28V1 = Ex.get('ТМИ', '05.01.beSPU11', 'НЕКАЛИБР ТЕКУЩ')
        spu_28V2 = Ex.get('ТМИ', '05.01.beSPU12', 'НЕКАЛИБР ТЕКУЩ')

        if ((kpdu_upr12 == 1) or (kpdu_upr22 == 1)):
            gprint('КПДУ включен')
        else:
            SCPICMD(0xE004, AsciiHex('0x0109 0000 0000 0000'))  # включить КПДУ упр
            #    SCPICMD(UV['КПДУ_УПР_ВКЛ'])
            print('Выдано УВ на включение управляющей шины КПДУ')
            diWait('04.01.beKPDUU12', 1, 10)
            kpdu_state = Ex.wait('ТМИ', '{01.01.KPDU_VREMYa.НЕКАЛИБР} < 5', 60)
            if kpdu_state == 1:
                gprint('КПДУ включен')
            else:
                rprint('КПДУ выключен')

        if ((kpdu_sil12 == 1) or (kpdu_sil22 == 1)):
            gprint('Силовая шина КПДУ включена')
        else:
            #    SCPICMD(0xE004, AsciiHex('0x011D 0000 0000 0000')) #включить КПДУ сил
            SCPICMD(UV['КПДУ_СИЛ_ВКЛ'])
            print('Выдано УВ на включение силовой шины КПДУ')
            diWait('04.01.beKPDUS12', 1, 10)

        if (spu_28V1 == 1) and (spu_28V2 == 1):
            gprint('Шина СПУ 28В включена')
        else:
            SCPICMD(UV['СПУ_28В_ВКЛ'])
            print('Выдано УВ на включение шины СПУ 28В')
            diWait('05.01.beSPU11', 1, 10)
            diWait('05.01.beSPU12', 1, 10)

        yprint('Включите стойку КИБК')
        inputG('Включите стойку КИБК')
        SICCELL('Импульс', out=[0x01, 0x00])  # Исходное ЭИБК1
        time.sleep(5)
        SICCELL('Импульс', out=[0x80, 0x00])  # Исходное ЭИБК2
        pa = input('Выставить опрос ПА 1. 0 - нет, 1 - да')
        if pa == '1':
            PA(1)
            time.sleep(10)
            # TODO: убрать UV['БЦК_ОЧИСТКА_ДИ'] можно поменять скорость на КИС
            SCPICMD(UV['БЦК_ОЧИСТКА_ДИ'])
            sleep(3)
            SCPICMD(UV['БЦК_ЗАПРОС_ПА29'])
            sleep(3)
            SCPICMD(UV['БЦК_СБРОС_ПАМЯТИ'])
        kpdu_mod = Ex.get('ТМИ', '01.01.KPDU_MOD', 'НЕКАЛИБР ТЕКУЩ') + 1
        print('Текущий модуль КПДУ == {}'.format(kpdu_mod))
        print('Перед полной проверкой ДУК рекомендуется начинать проверку с первого модуля')
        print('Переключить модуль? 0 - нет, 1 - да')
        switch_module = input('Введите номер -')
        if switch_module == '1':
            switchModuleKpdu()
        time_pred = 600
        SCPICMD(UV['ХДУК_ТВ_ПРЕД'], AsciiHex('0x{} 0000 0000 0000'.format(s2h(time_pred))))
        print('Установлено предельное время тяги ДУК == {} с'.format(time_pred))
        setTioValue()
        setInitialStateValues()

    @classmethod
    def test3(cls):
        print('Проверка включения ДУК в автоматическом режиме с помощью ХВКЛ_КДУ')
        cyclo_branch = setCycloBranch()
        avtoLaunchDuk(bk, k, bpk, cyclo_branch)

    @classmethod
    def off(cls, *args, **kwargs):
        yprint('ЗАВЕРШЕНИЕ ПМ ДУК', tab=1)
        time_pred = 7200
        SCPICMD(UV['ХДУК_ТВ_ПРЕД'], AsciiHex('0x{} 0000 0000 0000'.format(s2h(time_pred))))
        yprint('Сбросить НШ? 0 - нет, 1 - да')
        nsh_sbros = input('Введите номер -')
        if nsh_sbros == '1':
            clearNsh()
        SCPICMD(0x1051, AsciiHex('0x0000'))  # опрос ДИ2
        SCPICMD(0x1052, AsciiHex('0x100E 0000 0000 0000'))  # Время опроса ДИ3
        SCPICMD(0x1053, AsciiHex('0x0000'))  # Время опроса ДИ4-8
        SCPICMD(0x1054, AsciiHex('0x100E 0000 0000 0000'))  # опрос ДИ27
        SCPICMD(0x1065)  # ХДУК_РАЗР
        SCPICMD(0x104C)  # ХКПДУ_ СБРОС
        SCPICMD(0x1075)  # ХДАТЧИК_СБРОС
        SCPICMD(0x1071, AsciiHex('0x0000 0000 0000 0000'))  # ХКАТОД_СБРОС БК1К1
        SCPICMD(0x1071, AsciiHex('0x0100 0000 0000 0000'))  # ХКАТОД_СБРОС БК1К2
        SCPICMD(0x1071, AsciiHex('0x0200 0000 0000 0000'))  # ХКАТОД_СБРОС БК2К1
        SCPICMD(0x1071, AsciiHex('0x0300 0000 0000 0000'))  # ХКАТОД_СБРОС БК2К2
        yprint('Отключить КПДУ? 0 - нет, 1 - да')
        kpdu_off = input('Введите номер -')
        if kpdu_off == '1':
            #    SCPICMD(0xE005, AsciiHex('0x011D 0000 0000 0000')) #отключить КПДУ сил
            SCPICMD(UV['КПДУ_СИЛ_ОТКЛ'])
            print('Выдано УВ на отключение силовой шины КПДУ')
            diWait('04.01.beKPDUS12', 0, 20)

            SCPICMD(0xE005, AsciiHex('0x0109 0000 0000 0000'))  # отключить КПДУ упр
            #    SCPICMD(UV['КПДУ_УПР_ОТКЛ'])
            print('Выдано УВ на отключение управляющей шины КПДУ')
            diWait('04.01.beKPDUU12', 0, 20)

        yprint('Отключить СПУ 28В? 0 - нет, 1 - да')
        spu_off = input('Введите номер -')
        if spu_off == '1':
            SCPICMD(UV['СПУ_28В_ОТКЛ'])
            print('Выдано УВ на отключение шины СПУ 28В')
            diWait('05.01.beSPU11', 0, 20)
            diWait('05.01.beSPU12', 0, 20)

        yprint('ПМ ДУК ЗАВЕРШЕНА', tab=1)

    @classmethod
    def get_tmi(cls, *args, **kwargs):
        cls.__unrealized__()

# yprint('НАЧАТЬ ПМ ДУК', tab=1)
#
# kpdu_upr11 = Ex.get('ТМИ', '04.01.beKPDUU11', 'НЕКАЛИБР ТЕКУЩ')
# kpdu_upr12 = Ex.get('ТМИ', '04.01.beKPDUU12', 'НЕКАЛИБР ТЕКУЩ')
# kpdu_upr21 = Ex.get('ТМИ', '04.01.beKPDUU21', 'НЕКАЛИБР ТЕКУЩ')
# kpdu_upr22 = Ex.get('ТМИ', '04.01.beKPDUU22', 'НЕКАЛИБР ТЕКУЩ')
#
# kpdu_sil11 = Ex.get('ТМИ', '04.01.beKPDUS11', 'НЕКАЛИБР ТЕКУЩ')
# kpdu_sil12 = Ex.get('ТМИ', '04.01.beKPDUS12', 'НЕКАЛИБР ТЕКУЩ')
# kpdu_sil21 = Ex.get('ТМИ', '04.01.beKPDUS21', 'НЕКАЛИБР ТЕКУЩ')
# kpdu_sil22 = Ex.get('ТМИ', '04.01.beKPDUS22', 'НЕКАЛИБР ТЕКУЩ')
#
# spu_28V1 = Ex.get('ТМИ', '05.01.beSPU11', 'НЕКАЛИБР ТЕКУЩ')
# spu_28V2 = Ex.get('ТМИ', '05.01.beSPU12', 'НЕКАЛИБР ТЕКУЩ')
#
# if ((kpdu_upr12 == 1) or (kpdu_upr22 == 1)):
#     gprint('КПДУ включен')
# else:
#     SCPICMD(0xE004, AsciiHex('0x0109 0000 0000 0000'))  # включить КПДУ упр
#     #    SCPICMD(UV['КПДУ_УПР_ВКЛ'])
#     print('Выдано УВ на включение управляющей шины КПДУ')
#     diWait('04.01.beKPDUU12', 1, 10)
#     kpdu_state = Ex.wait('ТМИ', '{01.01.KPDU_VREMYa.НЕКАЛИБР} < 5', 60)
#     if kpdu_state == 1:
#         gprint('КПДУ включен')
#     else:
#         rprint('КПДУ выключен')
#
# if ((kpdu_sil12 == 1) or (kpdu_sil22 == 1)):
#     gprint('Силовая шина КПДУ включена')
# else:
#     #    SCPICMD(0xE004, AsciiHex('0x011D 0000 0000 0000')) #включить КПДУ сил
#     SCPICMD(UV['КПДУ_СИЛ_ВКЛ'])
#     print('Выдано УВ на включение силовой шины КПДУ')
#     diWait('04.01.beKPDUS12', 1, 10)
#
# if (spu_28V1 == 1) and (spu_28V2 == 1):
#     gprint('Шина СПУ 28В включена')
# else:
#     SCPICMD(UV['СПУ_28В_ВКЛ'])
#     print('Выдано УВ на включение шины СПУ 28В')
#     diWait('05.01.beSPU11', 1, 10)
#     diWait('05.01.beSPU12', 1, 10)
#
# yprint('Включите стойку КИБК')
# input('Для продолжения нажмите Enter')
# SICCELL('Импульс', out=[0x01, 0x00])  # Исходное ЭИБК1
# time.sleep(5)
# SICCELL('Импульс', out=[0x80, 0x00])  # Исходное ЭИБК2
#
# pa = input('Выставить опрос ПА 1. 0 - нет, 1 - да')
# if pa == '1':
#     PA(1)
#     time.sleep(10)
#     SCPICMD(UV['БЦК_ОЧИСТКА_ДИ'])
#     sleep(3)
#     SCPICMD(UV['БЦК_ЗАПРОС_ПА29'])
#     sleep(3)
#     SCPICMD(UV['БЦК_СБРОС_ПАМЯТИ'])
#
# kpdu_mod = Ex.get('ТМИ', '01.01.KPDU_MOD', 'НЕКАЛИБР ТЕКУЩ') + 1
# print('Текущий модуль КПДУ == {}'.format(kpdu_mod))
# print('Перед полной проверкой ДУК рекомендуется начинать проверку с первого модуля')
# print('Переключить модуль? 0 - нет, 1 - да')
# switch_module = input('Введите номер -')
# if switch_module == '1':
#     switchModuleKpdu()
# time_pred = 600
# SCPICMD(UV['ХДУК_ТВ_ПРЕД'], AsciiHex('0x{} 0000 0000 0000'.format(s2h(time_pred))))
# print('Установлено предельное время тяги ДУК == {} с'.format(time_pred))
# setTioValue()
# setInitialStateValues()
#
# while True:
#     print('Выберите проверку:')
#     print('3 -- Проверка включения ДУК в автоматическом режиме с помощью ХВКЛ_КДУ')
#     # print('8 -- Тест')
#     print('0 -- Завершение ПМ ДУК')
#
#     test = input("Введите номер - ")
#
#     if (test == '1') or (test == '3'):
#         bk, k, bpk = setDukConfig()
#
#     # if test == '1':
#     #     nsh = setNSh()
#     #     if nsh == None:
#     #         branch = setBranch()
#     #     elif nsh == 'NSh4':
#     #         branch = 'ПОДЗАПУСК'
#     #     else:
#     #         branch = None
#     #     manualLaunchDuk(bk, k, bpk, nsh, branch)
#     # elif test == '2':
#     #     cyclogram_key = cyclogramChoice()
#     #     if cyclogram_key == 'ХДУК_Ц4':
#     #         cyclo_branch = setCycloBranch()
#     #     else:
#     #         cyclo_branch = None
#     #     cyclogramDuk(cyclogram_key, cyclo_branch)
#     if test == '3':
#         cyclo_branch = setCycloBranch()
#         avtoLaunchDuk(bk, k, bpk, cyclo_branch)
#     # elif test == '4':
#     #     mode = setNsh0Mode()
#     #     duk_ban_control = setDukZapretKontr()
#     #     nsh0Check(mode, duk_ban_control)
#     # elif test == '5':
#     #     mode = setMdkrKontr()
#     #     bpk = setBpkNum()
#     #     emergencyPressureRelease(mode, bpk)
#     # elif test == '6':
#     #     for i in [1, 2]:
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', None)
#     #         manualLaunchDuk('BK2', 'K1', 'BPK2', None)
#     #
#     #         manualLaunchDuk('BK1', 'K2', 'BPK1', None)
#     #         manualLaunchDuk('BK2', 'K2', 'BPK2', None, 'ПОДЗАПУСК')
#     #
#     #         cyclogramDuk('ХДУК_Ц2')
#     #
#     #         avtoLaunchDuk('BK1', 'K1', 'BPK1')
#     #         avtoLaunchDuk('BK2', 'K1', 'BPK2')
#     #
#     #         cyclogramDuk('ХДУК_Ц4', bk='BK1', k='K2', bpk='BPK2')
#     #         '''
#     #         cyclogramDuk('ХДУК_Ц4', 'ПРЕРЫВАНИЕ', bk = 'BK1', k = 'K2', bpk = 'BPK2')
#     #
#     #         avtoLaunchDuk('BK1', 'K2', 'BPK1')
#     #
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', 'NSh1')
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', 'NSh1')
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', 'NSh1')
#     #
#     #         manualLaunchDuk('BK1', 'K2', 'BPK1', 'NSh1')
#     #         manualLaunchDuk('BK1', 'K2', 'BPK1', 'NSh1')
#     #         manualLaunchDuk('BK1', 'K2', 'BPK1', 'NSh1')
#     #
#     #         manualLaunchDuk('BK2', 'K1', 'BPK2', 'NSh1')
#     #         manualLaunchDuk('BK2', 'K1', 'BPK2', 'NSh1')
#     #
#     #         manualLaunchDuk('BK2', 'K1', 'BPK2', 'NSh1')
#     #
#     #         manualLaunchDuk('BK2', 'K2', 'BPK2', 'NSh1')
#     #         manualLaunchDuk('BK2', 'K2', 'BPK2', 'NSh1')
#     #         manualLaunchDuk('BK2', 'K2', 'BPK2', 'NSh1')
#     #
#     #         clearNsh()
#     #
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', 'NSh3')
#     #         manualLaunchDuk('BK1', 'K2', 'BPK1', 'NSh3')
#     #         manualLaunchDuk('BK2', 'K1', 'BPK1', 'NSh3')
#     #         manualLaunchDuk('BK2', 'K2', 'BPK1', 'NSh3')
#     #
#     #         clearNsh()
#     #
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', 'NSh4', 'ПОДЗАПУСК')
#     #         avtoLaunchDuk('BK1', 'K1', 'BPK1', 'НЕВЫПОЛНЕНИЕ')
#     #         manualLaunchDuk('BK2', 'K2', 'BPK2', 'NSh4', 'ПОДЗАПУСК')
#     #
#     #         resetBan()
#     #         clearNsh()
#     #         '''
#     #
#     #         manualLaunchDuk('BK2', 'K1', 'BPK2', None, 'НАРУШЕНИЕ ОБМЕНА', mkpd_kontr='1')
#     #
#     #         manualLaunchDuk('BK2', 'K1', 'BPK1', None, 'НЕВЫПОЛНЕНИЕ')
#     #         cyclogramDuk('ХДУК_Ц4', 'НЕВЫПОЛНЕНИЕ', bk='BK1', k='K2', bpk='BPK2')
#     #         avtoLaunchDuk('BK2', 'K2', 'BPK1', 'НЕВЫПОЛНЕНИЕ')
#     #
#     #         resetBan()
#     #
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', None, 'НАРУШЕНИЕ ОБМЕНА', mkpd_kontr='0')
#     #
#     #         manualLaunchDuk('BK2', 'K1', 'BPK1', None)
#     #         '''
#     #         avtoLaunchDuk('BK2', 'K2', 'BPK2')
#     #         cyclogramDuk('ХДУК_Ц4', bk = 'BK1', k = 'K2', bpk = 'BPK1')
#     #         '''
#     #
#     #         SCPICMD(UV['ХМКПД_ВКЛ'])
#     #         print('Выдано УВ на включение контроля информационного обмена')
#     #         SCPICMD(UV['ХКПДУ_СБРОС'])
#     #         print('Выдано УВ на сброс признака нарушения информационного обмена')
#     #
#     #         nsh0Check('ВКЛ', 'ВКЛ')
#     #
#     #         manualLaunchDuk('BK1', 'K1', 'BPK1', None, 'НЕВЫПОЛНЕНИЕ')
#     #         cyclogramDuk('ХДУК_Ц4', 'НЕВЫПОЛНЕНИЕ', bk='BK1', k='K2', bpk='BPK2')
#     #         avtoLaunchDuk('BK2', 'K1', 'BPK1', 'НЕВЫПОЛНЕНИЕ')
#     #
#     #         clearNsh()
#     #
#     #         nsh0Check('ВКЛ', 'ОТКЛ')
#     #
#     #         clearNsh()
#     #
#     #         nsh0Check('ОТКЛ', 'ВКЛ')
#     #         nsh0Check('ОТКЛ', 'ОТКЛ')
#     #
#     #         emergencyPressureRelease('ВКЛ', 'BPK1')
#     #         emergencyPressureRelease('ВКЛ', 'BPK2')
#     #         emergencyPressureRelease('ОТКЛ', 'BPK1')
#     #         emergencyPressureRelease('ОТКЛ', 'BPK2')
#     #
#     #         switchModuleKpdu()
#     #
#     # elif test == '7':
#     #     clearNsh()
#     # elif test == '8':
#     #     # manualLaunchDuk('BK1', 'K1', 'BPK1', None, 'НАРУШЕНИЕ ОБМЕНА', mkpd_kontr = '1')
#     #     # manualLaunchDuk('BK1', 'K1', 'BPK1', None, 'НАРУШЕНИЕ ОБМЕНА', mkpd_kontr = '0')
#     #     # cyclogramDuk('ХДУК_Ц4', 'ПРЕРЫВАНИЕ', bk = 'BK2', k = 'K2', bpk = 'BPK2')
#     #     manualLaunchDuk('BK1', 'K1', 'BPK1', None, 'НАРУШЕНИЕ ОБМЕНА', mkpd_kontr='0')
#     #     manualLaunchDuk('BK1', 'K1', 'BPK1', None)
#     elif test == '0':
#         break
#     else:
#         print('Введено неверное значение')
#
# yprint('ЗАВЕРШЕНИЕ ПМ ДУК', tab=1)
# time_pred = 7200
# SCPICMD(UV['ХДУК_ТВ_ПРЕД'], AsciiHex('0x{} 0000 0000 0000'.format(s2h(time_pred))))
# yprint('Сбросить НШ? 0 - нет, 1 - да')
# nsh_sbros = input('Введите номер -')
# if nsh_sbros == '1':
#     clearNsh()
# SCPICMD(0x1051, AsciiHex('0x0000'))  # опрос ДИ2
# SCPICMD(0x1052, AsciiHex('0x100E 0000 0000 0000'))  # Время опроса ДИ3
# SCPICMD(0x1053, AsciiHex('0x0000'))  # Время опроса ДИ4-8
# SCPICMD(0x1054, AsciiHex('0x100E 0000 0000 0000'))  # опрос ДИ27
# SCPICMD(0x1065)  # ХДУК_РАЗР
# SCPICMD(0x104C)  # ХКПДУ_ СБРОС
# SCPICMD(0x1075)  # ХДАТЧИК_СБРОС
# SCPICMD(0x1071, AsciiHex('0x0000 0000 0000 0000'))  # ХКАТОД_СБРОС БК1К1
# SCPICMD(0x1071, AsciiHex('0x0100 0000 0000 0000'))  # ХКАТОД_СБРОС БК1К2
# SCPICMD(0x1071, AsciiHex('0x0200 0000 0000 0000'))  # ХКАТОД_СБРОС БК2К1
# SCPICMD(0x1071, AsciiHex('0x0300 0000 0000 0000'))  # ХКАТОД_СБРОС БК2К2
# yprint('Отключить КПДУ? 0 - нет, 1 - да')
# kpdu_off = input('Введите номер -')
# if kpdu_off == '1':
#     #    SCPICMD(0xE005, AsciiHex('0x011D 0000 0000 0000')) #отключить КПДУ сил
#     SCPICMD(UV['КПДУ_СИЛ_ОТКЛ'])
#     print('Выдано УВ на отключение силовой шины КПДУ')
#     diWait('04.01.beKPDUS12', 0, 20)
#
#     SCPICMD(0xE005, AsciiHex('0x0109 0000 0000 0000'))  # отключить КПДУ упр
#     #    SCPICMD(UV['КПДУ_УПР_ОТКЛ'])
#     print('Выдано УВ на отключение управляющей шины КПДУ')
#     diWait('04.01.beKPDUU12', 0, 20)
#
# yprint('Отключить СПУ 28В? 0 - нет, 1 - да')
# spu_off = input('Введите номер -')
# if spu_off == '1':
#     SCPICMD(UV['СПУ_28В_ОТКЛ'])
#     print('Выдано УВ на отключение шины СПУ 28В')
#     diWait('05.01.beSPU11', 0, 20)
#     diWait('05.01.beSPU12', 0, 20)
#
# yprint('ПМ ДУК ЗАВЕРШЕНА', tab=1)
#
#
