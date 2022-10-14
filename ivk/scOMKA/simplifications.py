from ivk import config
from cpi_framework.utils.basecpi_abc import AsciiHex, CPIP
from cpi_framework.spacecrafts.omka.cpi import OBTS, CPICMD
from cpi_framework.spacecrafts.omka.otc import OTC
from ivk.scOMKA.controll_kpa import KPA
from ivk.scOMKA.controll_iccell import ICCELL


def getSimpleCommandsCPI():
    commands = [
        {
            'name': 'SCPICMD',
            'translation': 'КПИ УВ одинарная (только команда)',
            'import_string': 'from ivk.scOMKA.simplifications import SCPICMD',
            'description': 'Отправка одной КПИ УВ в КПА с заданием только номера команды (моментальное исполнение).\nПараметры:\n' + \
                           '  - cmd(int): номер команды',
            'example': 'SCPICMD(14)',
            'params': ['cmd'],
            'values': ['14'],
            'keyword': [False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        },
        {
            'name': 'SCPICMD',
            'translation': 'КПИ УВ одинарная (команда + время)',
            'import_string': 'from ivk.scOMKA.simplifications import SCPICMD',
            'description': 'Отправка одной КПИ УВ в КПА с заданием номера команды и времени.\nПараметры:\n' + \
                           '  - cmd(int): номер команды,\n' + \
                           '  - obts(OBTS): время по БШВ (объект БШВ)',
            'example': "SCPICMD(14, OBTS('2020:05:07:14:10:09'))",
            'params': ['cmd', 'obts'],
            'values': ['14', "OBTS('2021:1:2:3:4:5')"],
            'keyword': [False, False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        },
        {
            'name': 'SCPICMD',
            'translation': 'КПИ УВ одинарная (команда + данные)',
            'import_string': 'from ivk.scOMKA.simplifications import SCPICMD',
            'description': 'Отправка одной КПИ УВ в КПА с заданием номера команды и данных (моментальное исполнение).\nПараметры:\n' + \
                           '  - obts(OBTS): время по БШВ (объект БШВ),\n' + \
                           '  - args(AsciiHex): агрументы команды',
            'example': "SCPICMD(14, AsciiHex('0x8800000000000000'))",
            'params': ['cmd', 'args'],
            'values': ['14', "AsciiHex('0x8800000000000000')"],
            'keyword': [False, False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        },
        {
            'name': 'SCPICMD',
            'translation': 'КПИ УВ одинарная (команда + время + данные)',
            'import_string': 'from ivk.scOMKA.simplifications import SCPICMD4',
            'description': 'Отправка одной КПИ УВ в КПА с заданием номера команды, времени и данных.\nПараметры:\n' + \
                           '  - cmd(int): номер команды,\n' + \
                           '  - obts(OBTS): время по БШВ (объект БШВ),\n' + \
                           '  - args(AsciiHex): агрументы команды',
            'example': "SCPICMD(14, OBTS('2020:05:07:14:10:09'), AsciiHex('0x0000000000000000'))",
            'params': ['cmd', 'obts', 'args'],
            'values': ['14', "OBTS('2000:1:1:0:0:0')", "AsciiHex('0x0000000000000000')"],
            'keyword': [False, False, False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        },
        {
            'name': 'SCPICMD4',
            'translation': 'КПИ 4 УВ (команда + время + данные)',
            'import_string': 'from ivk.scOMKA.simplifications import SCPICMD4',
            'description': 'Отправка одной КПИ УВ в КПА с заданием номера команды, времени и данных.\nПараметры:\n' + \
                           '  - cmd(int): номер команды,\n' + \
                           '  - obts(OBTS): время по БШВ (объект БШВ),\n' + \
                           '  - args(AsciiHex): агрументы команды',
            'example': "SCPICMD(14, OBTS('2020:05:07:14:10:09'), AsciiHex('0x8800000000000000'))",
            'params': ['cmd1', 'obts1', 'args1', 'cmd2', 'obts2', 'args2', 'cmd3', 'obts3', 'args3', 'cmd4', 'obts4',
                       'args4'],
            'values': ['0', "OBTS('2000:1:1:0:0:0')", "AsciiHex('0x0000000000000000')",
                       '0', "OBTS('2000:1:1:0:0:0')", "AsciiHex('0x0000000000000000')",
                       '0', "OBTS('2000:1:1:0:0:0')", "AsciiHex('0x0000000000000000')",
                       '0', "OBTS('2000:1:1:0:0:0')", "AsciiHex('0x0000000000000000')"],
            'keyword': [False, False, False, False, False, False, False, False, False, False, False, False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        },
    ]
    return commands


def SCPICMD(*args, **kwargs):
    if len(args) + len(kwargs) > 4:
        raise Exception('Задано слишком много параметров (макс. 3)')

    _cmd = None
    _obts = OBTS(obts="2000:1:1:0:0:0")
    _args = AsciiHex('0x0000000000000000')

    for arg in args:
        if isinstance(arg, int):
            _cmd = arg
        elif isinstance(arg, OBTS):
            _obts = arg
        elif isinstance(arg, AsciiHex):
            _args = arg
        else:
            raise Exception('Задан неверный тип данных параметра %s : %s' % (repr(arg), repr(type(arg))))

    for k, v in kwargs.items():
        if k == 'cmd':
            if isinstance(v, int):
                _cmd = v
            else:
                raise Exception('Неверный тип данных для параметра "cmd"')
        elif k == 'obts':
            if isinstance(v, OBTS):
                _obts = v
            else:
                raise Exception('Неверный тип данных для параметра "obts"')
        elif k == 'args' and isinstance(v, AsciiHex):
            _args = v
        else:
            raise Exception('Задано неверное имя параметра: %s' % k)

    if _cmd is None:
        raise Exception('Параметр "cmd" должен быть обязательно задан')

    config.get_exchange().send('КПА', CPICMD(cmds=[CPIP(obts=_obts, cmd=_cmd, args=_args)]))


def SCPICMD4(*args, **kwargs):
    if len(args) + len(kwargs) > 13:
        raise Exception('Задано слишком много параметров (макс. 13)')

    _cmd = []
    _obts = []
    _args = []

    for arg in args:
        if isinstance(arg, int):
            _cmd.append(arg)
        elif isinstance(arg, OBTS):
            _obts.append(arg)
        elif isinstance(arg, AsciiHex):
            _args.append(arg)
        else:
            raise Exception('Задан неверный тип данных параметра %s : %s' % (repr(arg), repr(type(arg))))

    for k, v in kwargs.items():
        if k == 'cmd':
            if isinstance(v, int):
                _cmd = v
            else:
                raise Exception('Неверный тип данных для параметра "cmd"')
        elif k == 'obts':
            if isinstance(v, OBTS):
                _obts = v
            else:
                raise Exception('Неверный тип данных для параметра "obts"')
        elif k == 'args':
            if isinstance(v, AsciiHex):
                _args = v
            else:
                raise Exception('Неверный тип данных для параметра "args"')
        else:
            raise Exception('Задано неверное имя параметра: %s' % k)

    if _cmd is None:
        raise Exception('Параметр "cmd" должен быть обязательно задан')

    if len(_cmd) == len(_args) and len(_cmd) == len(_obts):
        paramsCPI = [CPIP(obts=_obts[i], cmd=_cmd[i], args=_args[i]) for i in range(len(_cmd))]
        config.get_exchange().send('КПА', CPICMD(cmds=paramsCPI))
    else:
        raise Exception('Заданы не все параметры в одной из УВ')


def getSimpleCommandsOTC():
    commands = [
        {
            'name': 'SOTC',
            'translation': 'РК (только команда)',
            'import_string': 'from ivk.scOMKA.simplifications import SOTC',
            'description': 'Отправка одной РК в КПА с заданием только номера команды.\nПараметры:\n' + \
                           '  - otc(int): номер команды',
            'example': 'SOTC(174)',
            'params': ['otc'],
            'values': ['1'],
            'keyword': [False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        },
        {
            'name': 'SOTC',
            'translation': 'РК (команда + аргумент)',
            'import_string': 'from ivk.scOMKA.simplifications import SOTC',
            'description': 'Отправка одной РК в КПА с заданием номера команды и аргументов.\nПараметры:\n' + \
                           '  - otc(int): номер команды,\n' + \
                           '  - args(AsciiHex): агрументы команды',
            'example': "SOTC(17, AsciiHex('0x8800000000000000'))",
            'params': ['otc', 'args'],
            'values': ['1', "AsciiHex('0x0000000000000000000000000000')"],
            'keyword': [False, False],
            'cat': config.get_exchange().getRootCommandNodeName(),
            'ex_send': False
        }
    ]
    return commands


def SOTC(otc, args=AsciiHex('0x00000000000000000000'), recv=0):
    config.get_exchange().send('КПА', OTC(otc, args, recv))


def SKPA(name, data=None):
    config.get_exchange().send('КПА', KPA(name, data))


def SICCELL(name, **kwargs):
    config.get_exchange().send('Ячейка ПИ', ICCELL(name, **kwargs))
