import os, threading, inspect, struct, hashlib

import cpi_framework
from cpi_framework.utils import docparser, basecpi_abc

from ivk import config


def create_pylint_file(script):
    fname = 'pylint_ivkng_script_%d_%s.py' % (threading.get_ident(), hashlib.md5(script.encode('utf-8')).hexdigest())
    file = open(fname, mode='w', encoding='utf-8')
    file.write(script)
    file.close()
    return fname


def get_pdb_file_name(script):
    return 'pdb_ivkng_script_%d_%s.py' % (threading.get_ident(), hashlib.md5(script.encode('utf-8')).hexdigest())


def generate_command_widget_script(text, filename):
    prepend = 'import sys, os, inspect\n'
    prepend += 'sys.path.insert(0, os.getcwd() + "/lib")\n'
    prepend += 'from cpi_framework.utils.basecpi_abc import *\n'
    prepend += 'from ivk import config\n'
    prepend += __get_all_imports('', get_commands_imports())
    prepend += 'Ex = config.get_exchange()\n'
    prepend += 'Ex.ivk_file_name = "%s"\n' % filename
    prepend += 'Ex.ivk_file_path = None\n'

    line_correction = len(prepend.splitlines())
    return prepend + text, line_correction


def is_breakpoint_line(line):
    return line.strip().startswith('__BREAK__')


def generate_pdb_script(text, filename, filepath=None):
    text_with_breakpoints = ''
    for line in text.splitlines():
        if is_breakpoint_line(line):
            text_with_breakpoints += line.replace('__BREAK__', 'sys.stdout.write("") #__BREAK__', 1) + '\n'
        else:
            text_with_breakpoints += line + '\n'

    prepend = 'import sys, os, inspect\n'
    prepend += 'sys.path.insert(0, os.getcwd() + "/lib")\n'
    prepend += 'from cpi_framework.utils.basecpi_abc import *\n'
    prepend += 'from cpi_framework.utils.toolsForCPI import *\n'
    prepend += 'from ivk import config\n'
    prepend += 'from ivk.log_db import DbLog\n'
    prepend += __get_all_imports('', get_commands_imports())
    prepend += 'class CustomStdOut:\n'
    prepend += '    def __init__(self):\n'
    prepend += '        self.real_stdout = sys.stdout\n'
    prepend += '        self.total_buffer = ""\n'
    prepend += '    def write(self, stream):\n'
    prepend += '        self.real_stdout.write(stream)\n'
    prepend += '        self.total_buffer += stream\n'
    prepend += '        if "\\n" in stream:\n'
    prepend += '            self.flush()\n'
    prepend += '    def flush(self):\n'
    prepend += '        self.real_stdout.flush()\n'
    prepend += 'sys.stdout = CustomStdOut()\n'
    prepend += 'def custom_input(inv):\n'
    prepend += '    print(inv)\n'
    prepend += '    inp = sys.stdin.readline()\n'
    prepend += '    return inp[:-1] if inp.rfind("\\n") == len(inp)-1 else inp\n'
    prepend += 'input = custom_input\n'
    prepend += 'Ex = config.get_exchange()\n'
    prepend += 'Ex.ivk_file_name = "%s"\n' % filename
    prepend += 'Ex.ivk_file_path = "%s"\n' % filepath.replace('\\',
                                                              '\\\\') if filepath is not None else 'Ex.ivk_file_path = None\n'
    prepend += 'def endscript_log():\n'
    prepend += '    print("{#ffcd57}Конец выполнения скрипта \\"%s\\"")\n' % filename
    prepend += '    DbLog.log(Ex.ivk_file_name, "Конец выполнения скрипта", False, Ex.ivk_file_path, sys.stdout.total_buffer)\n'
    prepend += 'def exit():\n'
    prepend += '    endscript_log()\n'
    prepend += '    sys.exit()\n'
    prepend += 'sys.stdout.write("я\\n")\n'
    prepend += 'from engineers_src.tools.ivk_script_tools import *\n'  # импорт файл
    prepend += 'print("{#d6ff59}Начало выполнения скрипта \\"%s\\"")\n' % filename
    prepend += 'DbLog.log(Ex.ivk_file_name, "Начало выполнения скрипта", False, Ex.ivk_file_path, inspect.getsource(sys.modules[__name__]))\n'

    append = 'endscript_log()\n'

    line_correction = len(prepend.splitlines())
    return prepend + text_with_breakpoints + append, line_correction


def __get_all_imports(prepend, imports):
    for imp in imports:
        if 'import_string' in imp and imp['import_string']:
            if imp['import_string'] not in prepend:
                prepend += imp['import_string'] + '\n'
        if 'simple_import_string' in imp and imp['simple_import_string']:
            if imp['simple_import_string'] not in prepend:
                prepend += imp['simple_import_string'] + '\n'
        if 'children' in imp:
            prepend = __get_all_imports(prepend, imp['children'])
    return prepend


def get_commands_keywords():
    return __get_commands_keywords('Ex BREAK CPIP AsciiHex ', get_commands_imports())


def __get_commands_keywords(keywords, imports):
    for imp in imports:
        if 'import_string' in imp and imp['import_string']:
            kw = imp['import_string'].split(' ')[-1]
            if kw + ' ' not in keywords:
                keywords += kw + ' '
        if 'simple_import_string' in imp and imp['simple_import_string']:
            kw = imp['simple_import_string'].split(' ')[-1]
            if kw not in keywords:
                keywords += kw + ' '
        if 'name' in imp and imp['name']:
            if imp['name'] not in keywords:
                keywords += imp['name'] + ' '
        if 'children' in imp:
            keywords = __get_commands_keywords(keywords, imp['children'])
    return keywords


def get_autocomplete_jedi_doc(completion):
    doc = completion.docstring()
    if not completion.module_name or doc.startswith('_method'):
        try:
            if completion.type == 'class':
                doc = eval(completion.full_name + '.__init__').__doc__
            else:
                doc = eval(completion.full_name).__doc__
            try:
                parsed = docparser.parse_docstring(doc)
                doc = parsed['description']
            except:
                pass
        except:
            pass

    return doc


def get_autocomplete_jedi_args(completion):
    if not completion.type == 'function':
        return None
    if completion.docstring().startswith('_method'):
        try:
            f = eval(completion.full_name)
            argspec = inspect.getargspec(f)
            return [arg for arg in argspec[0] if arg != 'self']
        except:
            pass
    return [arg.name for arg in completion.params if arg.name != 'self']


###################################################################################################################
############################################### GET IMPORTS #######################################################
###################################################################################################################
commands_imports = None


def get_commands_imports():
    global commands_imports
    if commands_imports:
        return commands_imports

    commands = []
    for member in inspect.getmembers(cpi_framework):
        if inspect.ismodule(member[1]) and member[0] in config.get_exchange().getModuleFilter():
            get_imports(commands, member[1])

    imports = []
    imports.append({
        'category': config.get_exchange().getRootCommandNodeName(),
        'description': config.get_exchange().getRootCommandNodeDescription(),
        'children': commands
    })

    imports.append({
        'category': 'УВ для ' + config.get_exchange().getRootCommandNodeName(),
        'searcher_type': 'SCPICMD',
        'children': '',
        'params': ['cmd', 'obts', 'args'],
        'name': 'SCPICMD',
        'ex_send': False
    })

    imports.append({
        'category': 'РК для ' + config.get_exchange().getRootCommandNodeName(),
        'searcher_type': 'SOTC',
        'children': '',
        'params': ['cmd', 'obts', 'args'],
        'name': 'SOTC',
        'ex_send': False
    })

    imports.append({
        'category': 'Общие',
        'description': 'Команды категории "Общие" расширяют возможности для работы с базовыми фунациями языка.',
        'children': [
            {
                'name': 'sleep',
                'import_string': 'from time import sleep',
                'description': 'Выполняет задержку на указанное число секунд,\nнапример sleep(0.2) выполнит задержку на 200мс.\nПараметры:\n' + \
                               '  - seconds(float): задержка в секундах',
                'example': '#Задрежка на 1.7 секунды\nsleep(1.7)',
                'params': ['seconds'],
                'values': ['0.5'],
                'keyword': [False],
                'translation': 'Задержка',
                'ex_send': False,
                'cat': 'Общие'
            },
            {
                'name': 'exit',
                'import_string': '',
                'description': 'Принудительное завершение программы',
                'example': 'exit()',
                'params': [],
                'values': [],
                'keyword': [],
                'translation': 'Выход',
                'ex_send': False,
                'cat': 'Общие'
            },
            {
                'name': '__BREAK__',
                'import_string': '',
                'description': 'Ставит выполнение скрипта на паузу',
                'example': '''print(123)
__BREAK__ #Тут выполнение программы будет приостановлено
#Дальнейшие команды будут выполнены после 
#нажатия кнопки "Продолжить" или "Далее"
print(124)
print(125)''',
                'params': [],
                'values': [],
                'keyword': [],
                'translation': 'Пауза',
                'ex_send': False,  # True by default
                'is_function': False,  # True by default
                'cat': 'Общие'
            },
            {
                'name': 'crc16_ccitt',
                'import_string': 'from cpi_framework.utils.crc.crc16_ccitt import crc16_ccitt',
                'description': 'Расчет контрольной суммы CRC16 CCITT.\nПараметры:\n' + \
                               '  - data(bytes): бинарные данные, для которых необходимо посчитать CRC,\n' + \
                               '  - len(int): количество байт из data, используемые при расчете',
                'example': '''#Инициализация массива из 10 байт
data = bytes([1,2,3,4,5,6,7,8,9,10])
#Расчет CRC16 для всего массива байт
crc = crc16_ccitt(data, len(data))
#Расчет CRC16 для первых 5 байт массива
crc = crc16_ccitt(data, 5)''',
                'params': ['data', 'len'],
                'values': ['bytes()', '0'],
                'keyword': [False, False],
                'translation': 'Контрольная сумма',
                'ex_send': False,
                'cat': 'Общие'
            },
            {
                'name': 'b2h',
                'import_string': 'from ivk.cpi_framework_connections import b2h',
                'description': 'Преобразует целое число размером до 1 байта в Ascii Hex представление.\nПараметры:\n' + \
                               '  - num(int): положительное число размером до 1 байта',
                'example': 'h = b2h(249)\n#Результат строка h == "f9"',
                'params': ['num'],
                'values': ['0xFF'],
                'keyword': [False],
                'translation': 'ByteToHex',
                'ex_send': False,  # True by default
                'cat': 'Общие'
            },
            {
                'name': 's2h',
                'import_string': 'from ivk.cpi_framework_connections import s2h',
                'description': 'Преобразует целое число размером до 2 байт в Ascii Hex представление.\nПараметры:\n' + \
                               '  - num(int): положительное число размером до 2 байт',
                'example': 'h = s2h(9485)\n#Результат строка h == "0d25"',
                'params': ['num'],
                'values': ['0xFFFF'],
                'keyword': [False],
                'translation': 'ShortToHex',
                'ex_send': False,  # True by default
                'cat': 'Общие'
            },
            {
                'name': 'i2h',
                'import_string': 'from ivk.cpi_framework_connections import i2h',
                'description': 'Преобразует целое число размером до 4 байт в Ascii Hex представление.\nПараметры:\n' + \
                               '  - num(int): положительное число размером до 4 байт',
                'example': 'h = i2h(2353489)\n#Результат строка h == "51e92300"',
                'params': ['num'],
                'values': ['0xFFFFFFFF'],
                'keyword': [False],
                'translation': 'IntToHex',
                'ex_send': False,  # True by default
                'cat': 'Общие'
            }
        ]
    })

    for c in config.get_exchange().getAdditionalCommands():
        append_to = None
        for imp in imports:
            if imp['category'] == c['cat']:
                append_to = imp['children']
                break
        if append_to:
            append_to.append(c)
        else:
            imports.append({
                'category': c['cat'],
                'children': [c],
                'description': c['cat_description'] if 'cat_description' in c else ''
            })

    commands_imports = imports
    return imports


def get_imports(commands, module):
    for member in inspect.getmembers(module):
        if not inspect.isclass(member[1]) and not inspect.isfunction(member[1]) and not inspect.ismethod(
                member[1]) or inspect.isbuiltin(member[1]):
            continue
        if member[0].startswith('_') and member[0] != '__init__':
            continue
        try:
            if inspect.getfile(member[1]) != inspect.getfile(module):
                continue
        except TypeError:
            continue
        if inspect.isclass(member[1]):
            candidate = member[1]
            for m in inspect.getmembers(candidate):
                if m[0] == 'getDescription' and candidate.getDescription() is not None:
                    data = {}
                    data['name'] = candidate.__name__
                    data['import_string'] = 'from %s import %s' % (
                    inspect.getmodule(candidate).__name__, candidate.__name__)
                    data['description'] = candidate.getDescription()['description']
                    data['translation'] = candidate.getDescription()['translation']
                    if 'example' in candidate.getDescription():
                        data['example'] = candidate.getDescription()['example']
                    data['queues'] = config.get_exchange().getCpiFrameworkDestinations()
                    data['params'] = []
                    data['values'] = []
                    data['keyword'] = []
                    for param in candidate.getParamsSpec():
                        data['params'].append(param.name)
                        if param.foldSpec is not None:
                            val = '[CPIP(%s)]' % ', '.join(__unfoldSpec(param.foldSpec))
                            data['values'].append(val)
                        else:
                            data['values'].append(param.defaultValCode)
                        data['keyword'].append(True)

                    commands.append(data)
                    break


def __unfoldSpec(fold_spec):
    params = []
    for param in fold_spec:
        if param.foldSpec is not None:
            params.append('[CPIP(%s)]' % ', '.join(__unfoldSpec(param.foldSpec)))
        else:
            params.append('%s=%s' % (param.name, param.defaultValCode))
    return params


def b2h(sh):
    '''byte to asciihex'''
    return struct.pack("<B", sh).hex()


def s2h(sh):
    '''short to asciihex'''
    return struct.pack("<H", sh).hex()


def i2h(sh):
    '''int to asciihex'''
    return struct.pack("<I", sh).hex()
