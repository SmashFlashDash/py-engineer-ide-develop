from ivk import config
from cpi_framework.utils.basecpi_abc import AsciiHex, CPIP
from cpi_framework.spacecrafts.omka.cpi import OBTS, CPICMD
from cpi_framework.spacecrafts.omka.otc import OTC

def getSimpleCommandsCPI():
    commands = [
        {
            'name' : 'SCPICMD',
            'import_string' : 'from ivk.scBRK.simplifications import SCPICMD',
            'description' : 'Отправка одной КПИ УВ в КПА с заданием только номера команды',                                 
            'params' : ['cmd'],
            'values' : ['14'],
            'keyword' : [False],
            'translation' : 'КПИ УВ одинарная (только команда)',
            'cat' : 'БРК',
            'queues': ['БРК'],
            'ex_send' : False
        },
        {
            'name' : 'SCPICMD',
            'import_string' : 'from ivk.scBRK.simplifications import SCPICMD',
            'description' : 'Отправка одной КПИ УВ в КПА с заданием номера команды и времени',                               
            'params' : ['cmd', 'obts'],
            'values' : ['14', "OBTS('2021:1:2:3:4:5')"],
            'keyword' : [False, False],
            'translation' : 'КПИ УВ одинарная (команда + время)',
            'cat' : 'БРК',
            'queues': ['БРК'],
            'ex_send' : False
        },
        {
            'name' : 'SCPICMD',
            'import_string' : 'from ivk.scBRK.simplifications import SCPICMD',
            'description' : 'Отправка одной КПИ УВ в КПА с заданием номера команды и данных',                                  
            'params' : ['cmd', 'args'],
            'values' : ['14', "AsciiHex('0x8800000000000000')"],
            'keyword' : [False, False],
            'translation' : 'КПИ УВ одинарная (команда + данные)',
            'cat' : 'БРК',
            'queues': ['БРК'],
            'ex_send' : False
        },
        {
            'name' : 'SCPICMD',
            'import_string' : 'from ivk.scBRK.simplifications import SCPICMD',
            'description' : 'Отправка одной КПИ УВ в КПА с заданием номера команды, времени и данных',                                
            'params' : ['cmd', 'obts', 'args'],
            'values' : ['14', "OBTS('2021:1:2:3:4:5')", "AsciiHex('0x8800000000000000')"],
            'keyword' : [False, False, False],
            'translation' : 'КПИ УВ одинарная (команда + время + данные)',
            'cat' : 'БРК',
            'queues': ['БРК'],
            'ex_send' : False
        },
    ]
    return commands

def SCPICMD(*args, **kwargs):
    if len(args) + len(kwargs) > 3:
        raise Exception('Задано слишком много параметров (макс. 3)')
    
    _cmd = None
    _obts = OBTS(0)
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
        elif k == 'args':
            if isinstance(v, AsciiHex):
                _args = v
            else:
                raise Exception('Неверный тип данных для параметра "args"')
        else:
            raise Exception('Задано неверное имя параметра: %s' % k)
    
    if _cmd is None:
        raise Exception('Параметр "cmd" должен быть обязательно задан')
    config.get_exchange().send('БРК', CPICMD(cmds=[CPIP(obts=_obts, cmd=_cmd, args=_args)]))