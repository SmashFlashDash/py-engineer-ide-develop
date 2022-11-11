'''После добавления функции в модуль прописать ее в ivk_script_tools.py'''
'''Импорт зависимостей ИВК'''
import sys, os, inspect
from cpi_framework.utils.basecpi_abc import *
from ivk import config
from ivk.log_db import DbLog
from cpi_framework.spacecrafts.omka.cpi import CPIBASE
from cpi_framework.spacecrafts.omka.cpi import CPICMD
from cpi_framework.spacecrafts.omka.cpi import CPIKC
from cpi_framework.spacecrafts.omka.cpi import CPIMD
from cpi_framework.spacecrafts.omka.cpi import CPIPZ
from cpi_framework.spacecrafts.omka.cpi import CPIRIK
from cpi_framework.spacecrafts.omka.cpi import OBTS
from ivk.scOMKA.simplifications import SCPICMD
from cpi_framework.spacecrafts.omka.otc import OTC
from ivk.scOMKA.simplifications import SOTC
from ivk.scOMKA.controll_kpa import KPA
from ivk.scOMKA.simplifications import SKPA
from ivk.scOMKA.controll_iccell import ICCELL
from ivk.scOMKA.simplifications import SICCELL
from ivk.scOMKA.controll_scpi import SCPI
Ex = config.get_exchange()
redis_dp_get = config.getData     # вторая бд redis
redis_dp_set = config.updData     # вторая бд redis
redis_dp_inc = config.incData     # вторая бд redis
from time import sleep

'''Остальные импорты'''
from datetime import datetime, timedelta
from enum import Enum
import re
import threading
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton, QDialogButtonBox, QSizePolicy, QBoxLayout, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


################ IMITATION ###############
from random import randint
def get(*args):
    randint(0, 10)
    calibs = ('включен', 'отключен', 'Есть', 'Нет', 0, 100, None)
    uncalibs = (0, 1, 100, -100, 0.01, 1000, None)
    if isinstance(args[1], dict):
        result = args[1]
        for k, v in result.items():
            # result[k] = 'Включено' if v in 'КАЛИБР' else 0.1
            result[k] = calibs[randint(0, len(calibs)-1)] if v in 'КАЛИБР' else uncalibs[randint(0, len(uncalibs)-1)]
        return result
    if args[2] == 'КАЛИБР ТЕКУЩ':
        return calibs[randint(0, len(calibs)-1)]    # 'Включено'   #   calibs[randint(0, len(calibs)-1)]
    elif args[2] == 'НЕКАЛИБР ТЕКУЩ':
        return uncalibs[randint(0, len(uncalibs)-1)]    # 0.1          #   uncalibs[randint(0, len(uncalibs)-1)]
    elif args[2] == 'КАЛИБР ИНТЕРВАЛ':
        return ['Включено', 'Включено']
    elif args[2] == 'НЕКАЛИБР ИНТЕРВАЛ':
        return [1, 1]
Ex.get = get
KPA = lambda *args: ' '.join([str(x) for x in args])
Ex.send = lambda *args: print('Отправка ' + ' '.join([str(x) for x in args]))
Ex.wait = lambda *args: False if randint(0, 1) == 0 else True
Ex.ivk_file_name = "script.ivkng"
Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"


################ TEXT ###################
class Text:
    """класс с методами покраски текста"""
    print = print
    colors = {
        'default': '{#ffffff}',  # #FFFFFF
        'red': '{#FF0000}',
        'green': '{#4CBB17}',  # #00FF00
        'yellow': '{#FFFF00}',
        'blue': '{#00ffff}',
        'blue_lined': '{#00ffff}'
    }
    _tab = '      '
    default = colors['default']
    green = colors['green']
    red = colors['red']
    blue = colors['blue']
    yellow = colors['yellow']
    cur_color = default
    cur_tab = 0

    @classmethod
    def help(cls):
        print('Цвета в Colors: %s' % cls.colors)

    @classmethod
    def _get_format(cls, tab, color):
        """Получить стиль форматирования"""
        tab = cls.cur_tab if tab is None else tab
        color_get = cls.cur_color if color is None else cls.colors.get(color)
        if color_get is None:
            print(cls.colors['blue_lined'] + 'Err: Нет цевета %s в class.Text, используется default' % color)
            return tab, cls.default
        return tab, color_get

    @classmethod
    def text(cls, text, color=None, tab=None):
        """применить стиль к тексту цвет и смещение"""
        tab, color = cls._get_format(tab, color)
        text = text.replace('\n', '%s\n%s' % (Text.default, color))
        return color + cls._tab * tab + text + cls.default

    @classmethod
    def title(cls, text, color='yellow', tab=None, ):
        """ заголовок
            param text:     text
            param color:    цвет по умолчанию yellow
            param tab:      > 0 - установить смещения
                            <= 0 - смещение влево от текущего
                            None - предыдущий уровень смещений
        """
        if tab is None:
            tab = cls.cur_tab
        elif tab < 0:
            tab = cls.cur_tab - 1 if cls.cur_tab > 0 else 0
        cls.cur_tab = tab
        return cls.text(text, color=color, tab=tab)

    @staticmethod
    def color_bool(text, flag):
        if flag is None:
            colored = Text.colors['default']
        elif flag:
            colored = Text.colors['green']
        else:
            colored = Text.colors['red']
        colored += str(text) + Text.default
        return colored


def cprint(text, color=None, tab=0):
    print(Text.text(text, color, tab))


def gprint(text, tab=0):
    print(Text.text(text, 'green', tab))


def rprint(text, tab=0):
    print(Text.text(text, 'red', tab))


def bprint(text, tab=0):
    print(Text.text(text, 'blue', tab))


def yprint(text, tab=0):
    print(Text.text(text, 'yellow', tab))


def tprint(text, tab=None, color='default', ):
    print(Text.title(text, color, tab))


def proc_print(text):
    print(Text.default + 'Исполение: ' + Text.text(text, 'blue', 0))


def comm_print(text, color='yellow'):
    print(Text.default + 'Комметарий: ' + Text.text(text, 'yellow', 0))


################ INPUT ###################
class ClassInput:
    '''класс для исп input ivk'''
    input = None

    @staticmethod
    def set(foo):
        ClassInput.input = foo

    @staticmethod
    def isInputSet():
        if ClassInput.input is None:
            raise Exception('\ndef inp(quest):'
                            '\n\treturn input(quest)'
                            '\nClassInput.set(inp)')

    @staticmethod
    def input_break():
        while True:
            answer = ClassInput.input('Нажать [y]/[n]: ')
            if answer == 'y':
                bprint(':::Продолжить')
                return
            elif answer == 'n':
                bprint(':::Завершить')
                sys.exit()
            else:
                bprint('НЕВЕРНЫЙ ВВОД:::')


def inputM(args):
    ClassInput.isInputSet()
    ClassInput.input(args)


def breakM():
    ClassInput.isInputSet()
    ClassInput.input_break()


########### QT ###################
# для всплывающих окон
app = QApplication(sys.argv)


def inputG(text=None, parent=None):
    """вариант breakM без внешней функции"""
    if text is None:
        text = 'Скрипт остановлен'
    # app = QApplication(sys.argv)
    box = QMessageBox(QMessageBox.Warning, 'Пауза', text, QMessageBox.NoButton, parent)
    box.setWindowIcon(QIcon("res/mainicon.png"))
    box.setAttribute(Qt.WA_DeleteOnClose)
    box.addButton('Продолжить', QMessageBox.YesRole)
    box.addButton('Завершить', QMessageBox.NoRole)
    res = box.exec()
    if res == 0:
        bprint(':::Продолжить')
        # app.quit()    # если вызвать с внешним app то бдует беск цикл с первой кнопкой
    else:
        bprint(':::Завершить')
        sys.exit()


# TODO: заменить на собственный виджет с Buttons в GridLayouy а то размер кнопоко не изменяется
#  тогда show при включении и deleteOnClose, в кнопке вызывать window.close()
#  сделать все в одну фому
def inputGG(btnsList, title=None, parent=None, labels=None, ret_btn=None):
    """кнопки дял выбора действия"""

    class CustomMessageBox(QMessageBox):
        def __init__(self, parent=None):
            QMessageBox.__init__(self, parent)
            self.box = self.findChild(QDialogButtonBox)
            self.layout().removeWidget(self.box)
            self.clickedCustomButton = None

        def buttonFoo(self):
            self.clickedCustomButton = self.sender().accessibleName()
            self.setResult(-1)
            self.close()

        def addButtons(self, buttons_rows, labels):
            def newButton(text_btn):
                btn = QPushButton()
                btn.setAccessibleName(text_btn)
                btn.setMinimumWidth(120)
                # btn.setMaximumWidth(200)
                btn_label = QLabel()
                btn_label.setText(text_btn)
                btn_label.setWordWrap(True)
                lay = QBoxLayout(QBoxLayout.TopToBottom)
                lay.addWidget(btn_label)
                lay.setContentsMargins(10, 5, 10, 5)
                btn.setLayout(lay)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                btn.clicked.connect(self.buttonFoo)
                return btn

            def newLabel(textLabel):
                label = QLabel()
                label.setText(textLabel)
                label.setWordWrap(True)
                label.setMinimumWidth(80)
                # label.setMaximumWidth(100)
                label.setStyleSheet('font: bold large "Arial"')
                return label

            row = self.layout().rowCount()
            bl = self.layout()
            for idx_row, item in enumerate(buttons_rows):
                column = 0
                if isinstance(item, (tuple, list)):
                    bl.addWidget(newLabel(labels[idx_row]), row + idx_row, column)
                    column += 1
                    for btn_text in item:
                        bl.addWidget(newButton(btn_text), row + idx_row, column)
                        column += 1
                else:
                    bl.addWidget(newLabel(labels[idx_row]), row + idx_row, column)
                    column += 1
                    btn = newButton(item)
                    bl.addWidget(btn, row + idx_row, column)

            # вернуть в лэйоут QDialogButtonBox
            self.layout().addWidget(self.box, self.layout().rowCount(), 0, 1, self.layout().columnCount())

    if title is None:
        title = 'Выбор Действия'
        text = 'Выберите действие'
    else:
        text = title
    if labels is not None and (not isinstance(labels, (tuple, list)) or len(labels) != len(btnsList)):
        rprint('В функции inputGG параметр labels должен быть tuple размером = btnsList или None')
        sys.exit()
    elif labels is None:
        labels = ['']*len(btnsList)
    box = CustomMessageBox()
    box.setStandardButtons(QMessageBox.NoButton)
    box.setWindowIcon(QIcon("./res/mainicon.png"))
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(title)
    box.setText(text)
    box.addButtons(btnsList, labels)
    if ret_btn is not None:
        box.addButton('Отмена', QMessageBox.YesRole)
    box.addButton('Завершить', QMessageBox.NoRole)
    btn_code = box.exec()
    box.deleteLater()
    if box.clickedCustomButton:
        return box.clickedCustomButton
    elif ret_btn is not None and btn_code == 0:
        bprint(':::Отмена')
        return None
    else:
        bprint(':::Завершить')
        sys.exit()


############ THREAD LOCKS ###############
cmdLock = threading.Lock()
getLock = threading.Lock()

translate = {
        'SOTC': 'РК',
        'SCPICMD': 'УВ',
        'CPIBASE': 'Непонятно',
        'CPICMD': 'Непонятно',
        'CPIKC': 'Непонятно',
        'CPIMD': 'Непонятно',
        'CPIPZ': 'Непонятно',
        'CPIRIK': 'Непонятно',
        'OBTS': 'Непонятно',
        'SCPI': 'Непонятно',
        'SICCELL': 'Непонятно',
        'ICCELL': 'Непонятно',
        'SKPA': 'КПА',
        'KPA ': 'Непонятно',
        'OTC': 'Непонятно'
    }
def send(func, *args, toPrint=False, describe=None):
    """оболочка send для потока отправки УВ и т.д. с выводом
    :param func: обьект функции например SCPICMD без скобок
    :param args: аргументы функции через запятую
    :param toPrint: True - напечатать описание
    :param describe: describe='str' - доп описание отправленной комманды
    :return: None
    """
    cmdLock.acquire()
    try:
        func(*args)
    finally:
        cmdLock.release()
    if toPrint:
        if func.__name__ == 'SCPICMD':
            num = '0x' + hex(args[0]).upper()[2:]
        else:
            num = args[0]
        title = 'Отправка %s %s' % (translate[func.__name__], num)
        proc_print(title if describe is None else title + ';\n:::' + describe)


def ExGet(*args):
    """оболочка get для потока запроса"""
    getLock.acquire()
    try:
        val = Ex.get(*args)
        return val
    finally:
        getLock.release()


################ OTHERS ###################
# def sec_diff_2000(date, order='LE', type='u_int'):
#     """ функция пересчета даты для БЦК
#     :param date: дата в формате d.m.YYYY HH:mm:ss
#     :param order: 'LE' или 'BE'
#     :param type: u_short, u_int, u_long, u_longlong
#     :return:
#     """
#     _ord = {'LE': '<', 'BE': '>'}
#     _type = {'u_short': 'H', 'u_int': 'I', 'u_long': 'L', 'u_longlong': 'Q'}
#     dt_start = datetime(2000, 1, 1, 0, 0, 0)
#     try:
#         dt_end = datetime.strptime(date, "%d.%m.%Y %H:%M:%S")
#         if dt_end < dt_start:
#             raise Exception('sec_diff_2000 принимает дату больше 2000 года')
#     except Exception as ex:
#         print(ex)
#         return
#     dt_diff = int((dt_end - dt_start).total_seconds())
#     dt_diff_bytes = '0x'
#     dt_diff_bytes += struct.pack("%s%s" % (_ord[order], _type[type]), dt_diff).hex()
#     print('Секунд с 2000: %s\nВ байтах %s %s: %s' % (dt_diff, type, order, dt_diff_bytes))
#     return dt_diff_bytes


# TODO: добавить тестов на поле value_ref
#  бросить исключение если в eval поадает int==str в expression или простро вернет False
def controlGet(value_get, value_ref, cypher=None, text=None, toPrint=True):
    """ Проверка параметра запрашиваемого из БД
    ВНИМАНИЕ: если val: int сравнивается с 'КАЛИБР' :return False

    :param value_get: Ex.get() запрос к БД, должен совпадать по калибру с сравнение в expression
    :param value_ref: int|float - x==20, str - x=='Включено', list|tuple - 0 <= x <= 1
    :param cypher: шифр для вывода, если None шифр заменяется на НОРМА, НЕНОРМА
    :param text: типо передать сообщение ('str', 'str') для true false соответсвенно
    :param toPrint: печатать сообщение или нет
    :return: bool результат выражения
    """
    if isinstance(value_ref, (list, tuple)) and len(value_ref) == 2:
        equation = '%s <= %s <= %s' % (value_ref[0], value_get, value_ref[1])
    elif isinstance(value_ref, (int, float)):
        equation = '%s == %s' % (value_ref, value_get)
    elif isinstance(value_ref, str):
        pattern = re.compile(r"""\s?(is\snot|is|[=><!]*)                                 # the _operator  == > < <= >= != is is not
                                    \s?(None|True|False|\'[^\']+\'|\"[^\s]+\"|[\[+\-\d\.\,\s\]]*)   # the value [-0.0, +0.0] 0.0 'Включено' @same @unsame None
                                    """, re.X)
        parsed = re.search(pattern, value_ref).groups()
        if parsed[0] == '':
            equation = '\'%s\' == \'%s\'' % (value_ref, value_get)
        elif parsed[1].startswith(('\'', '\"')) and parsed[1].endswith(('\'', '\"')):
            equation = '\'%s\' %s \'%s\'' % (value_get,  parsed[0], parsed[1])
        else:
            equation = '%s %s %s' % (value_get, parsed[0], parsed[1])
    else:
        raise Exception('Невозможно прочитать выражение')
    res = eval(equation)
    if toPrint:
        if cypher is None:
            cypher = 'НОРМА ДИ' if res else 'НЕНОРМА ДИ'
        print(Text.color_bool('%s==%s: %s' % (cypher, value_ref, value_get), res))
    if isinstance(text, (tuple, list)) and len(text) == 2:
        bprint(text[0] if res else text[1])
    return res


def controlGetEQ(equation, count=1, period=0, toPrint=True, downBCK=False):
    """
    Опрос выражения ТМИ сетом через потоки, автоматом определяет КАЛИБР запрашиваемого значения
    @same, @unsame - фичи сравнить что значени такие же как предыдущие

    :param equation: [str] - принимает  выражение вида
        "not ({20.RCLIV.PCH}==1000 and {20.RCLIV.PCH2}==-1000) and {20.RCLIV.PCH1}==[-1000.0, +1000.0] and {20.RCLIV.PCH2} is not None and {20.RCLIV.PCH1}=='Включено' and {20.RCLIV.PCH2}==@same"
    :param count: int - кол-во опросов БД
    :param period: int - секунд между опросами не менее, не точный параметр зависит от скорости ответа БД
    :param toPrint: bool - печатать ли вывод
    :param downBCK: int - 0 - не печатает, 1 - минимум, 2 - полный вывод
    :return: bool - результат выражения
    """
    class PrimType(Enum):
        NUM_CONST = 0
        NUM_RANGE = 1
        STRING_CONST = 2
        NONE = 3
        BOOLEAN = 4

    class SameType(Enum):
        SAME = 0
        UNSAME = 1

    class AnyAllType(Enum):
        ALL = 0
        ANY = 1

    class SimpleEquation:
        def __init__(self, part):
            self.caliber = None
            self.type = None
            self.all_any_operator = None
            self.fromDB = []
            self.eq_title = None
            self.eq_eval = None
            self._open_backw = None
            self._operat_not = None
            self._cypher = None
            self._value = None
            self._cls_backw = None
            self._log_operator = None
            self.parse(part)

        def parse(self, part):
            """распарсить part"""
            # полученные значения в соответсвии с используемой регуляркой
            if part[0].endswith('not'):
                self._open_backw = part[0][:-3]
                self._operat_not = 'not'
            else:
                self._open_backw = part[0]
                self._operat_not = None
            self._cypher = part[1]
            caliber_sign = part[2]
            self._operator = part[3]
            value_text = part[4].strip()
            if value_text.strip('\"\'').endswith(('@all', '@any')):
                raise Exception('Ошибка в выражении:\n', part, 'нет разделителя @all @any')
            self.all_any_operator = part[5].lower()
            self._cls_backw = part[6]
            self._log_operator = part[7]

            # проверка на ошибки
            error_text = 'Ошибка в выражении: %s' % ' '.join(part)
            if '' in [self._cypher, self._operator, value_text]:
                raise ValueError(error_text)

            self._value = value_text
            if self.all_any_operator == '' or self.all_any_operator == '@all':
                self.all_any_operator = AnyAllType.ALL
            elif self.all_any_operator == '@any':
                self.all_any_operator = AnyAllType.ANY

            if re.fullmatch(r'[+\-\d\.]+', value_text):
                if self._operator not in ['>=', '<=', '>', '<', '==', '!=']:
                    raise ValueError(error_text)
                self.eq_eval = '%s' + ' %s %s' % (self._operator, value_text)
                self.type = PrimType.NUM_CONST
            elif value_text.startswith('[') and value_text.endswith(']') and self._operator in ['==', '!=']:
                values = re.findall(r"[+\-\d\.]+", value_text)
                if len(values) != 2:
                    raise ValueError(error_text)
                if self._operator == '==':
                    self.eq_eval = ('(%s <= ' % values[0]) + '%s' + (' <= %s)' % values[1])
                else:
                    self.eq_eval = ('not (%s <= ' % values[0]) + '%s' + (' <= %s)' % values[1])
                self.type = PrimType.NUM_RANGE
            elif value_text.startswith(('\'', '\"')) and value_text.endswith(('\'', '\"')):
                self.eq_eval = '%s' + ' == %s' % value_text
                self.type = PrimType.STRING_CONST
            elif value_text == 'None' and self._operator in ('==', '!='):
                self.eq_eval = '%s' + ' %s %s' % (self._operator, value_text)
                self.type = PrimType.NONE
            elif value_text in ['True', 'False']:
                self.eq_eval = '%s' + ' == %s' % value_text
                self.type = PrimType.BOOLEAN
            elif value_text.startswith('@same'):
                self.type = SameType.SAME
                self.eq_eval = '%s == %s'
            elif value_text.startswith('@unsame'):
                self.type = SameType.UNSAME
                self.eq_eval = '%s != %s'
            else:
                raise ValueError(error_text)

            if self._operat_not:
                self.eq_eval = 'not (' + self.eq_eval + ')'
            else:
                self._operat_not = ''

            title = self.eq_eval
            if isinstance(self.type, PrimType):
                self.eq_title = (title % self._cypher) + ' ' + ('@all' if self.all_any_operator is AnyAllType.ALL else '@any')
            else:
                self.eq_title = title % (self._cypher, self._value + ' ' + ('@all' if self.all_any_operator is AnyAllType.ALL else '@any'))

            if caliber_sign != '':
                if caliber_sign[1] in ('К', 'K'):
                    self.caliber = 'КАЛИБР ТЕКУЩ'
                else:
                    self.caliber = 'НЕКАЛИБР ТЕКУЩ'
            else:
                if self.type is PrimType.STRING_CONST:
                    self.caliber = 'КАЛИБР ТЕКУЩ'
                else:
                    self.caliber = 'НЕКАЛИБР ТЕКУЩ'

        def calculate_db_values(self):
            """
            обрабатывает значение в поле fromDB, формирует текст, возвращает значением вып
            простого выражения
            :return: rowbool, rowtext
            """
            row_text = []
            row_bool = []
            for idx, valDB in enumerate(self.fromDB):
                eval_eq = self.eq_eval
                if isinstance(valDB, str):
                    eval_eq = eval_eq.replace('%s', '\'%s\'')
                    eval_eq = eval_eq.lower()
                    valDB = valDB.lower()
                else:
                    valDB = str(valDB)

                if self.type is PrimType.BOOLEAN:
                    eval_eq = eval_eq.split('==')[1].strip()
                elif isinstance(self.type, PrimType):
                    eval_eq = eval_eq % valDB
                elif isinstance(self.type, SameType):
                    if idx == 0:
                        eval_eq = 'None'
                    else:
                        eval_eq = eval_eq % (self.fromDB[idx - 1], valDB)

                try:
                    res = eval(eval_eq)
                except Exception as ex:
                    res = None
                    rprint('eval::: %s --- error: %s' % (eval_eq, ex))

                row_bool.append(res)
                row_text.append(valDB)

            # значение по всем значениям из fromDB
            if self.all_any_operator is AnyAllType.ANY:
                row_result = any(row_bool)
            elif isinstance(self.type, SameType):
                row_result = all(row_bool[1:])
            else:
                row_result = all(row_bool)

            row_bool.insert(0, row_result)
            row_text.insert(0, self.eq_title)
            return row_bool, row_text

    def parse_equation(equations_all, equations_dict):
        """
        парсин гвыражения на обьекты подвыражений SimpleEquation в спиоок equations_all
        и словарь equations_dict куда по ключам будут записаны значения из БД
        :return: gotSameType
        """
        gotSameType = False
        for part in cyphers:
            eq = SimpleEquation(part)
            key = (eq._cypher, eq.caliber)
            equations_all.append((key, eq))
            equations_dict[key] = None
            if isinstance(eq.type, SameType):
                gotSameType = True
        return gotSameType

    def execute_db():
        """
        опрос БД словарем, значения fromDB подставляет в обьекты equations_all
        """
        query = {}
        for item in equations_dict.items():
            key = item[0]
            query[key[0][1:-1]] = key[1].split()[0]     # шифр без скобок, и слово калибровки
        fromDB = Ex.get('ТМИ', query, '')
        # запись значений из БД в equations_all
        for x in equations_all:
            constrait_key = x[0]
            key = constrait_key[0][1:-1]
            eq = x[1]
            eq.fromDB.append(fromDB[key])
            # для словаря на выходе из всей функции
            if equations_dict[constrait_key] is None:
                equations_dict[constrait_key] = [fromDB[key]]
            else:
                equations_dict[constrait_key].append(fromDB[key])

    """ПАРСИНГ"""
    bprint('ОПРОС ТМИ')
    pattern = re.compile(r"""\s?([not\s(]*)?                                        # _operator not and bacwards        
                            \s?({.+?})                                              # the _cypher
                            \s?(@[КKНH])?                                           # the _caliber
                            \s?(is\snot|is|[=><!]*)                                 # the _operator  == > < <= >= != is is not
                            \s?(None|@[uns]+ame|True|False|\'[^\']+\'|\"[^\s]+\"|[\[+\-\d\.\,\s\]]*)   # the value [-0.0, +0.0] 0.0 'Включено' @same @unsame None
                            \s?(@[alyn]+)?                                           # all any type
                            \s?(\)*)?                                               # bacwards        
                            \s?(and|or)?\s?                                         # logical _operator
                            """, re.X)
    cyphers = re.findall(pattern, equation)
    equations_all = []  # список с обьектами [(_cypher, SimpleEquarion)] в порядке их в выражении
    equations_dict = {}  # cлвоарь с составными ключами {(_cypher, caliber): ''} чобы не запрашивать из бд те же знач
    gotSameType = parse_equation(equations_all, equations_dict)
    if gotSameType and count < 2:
        raise Exception('Шифры с параметром same должны быть опрошены не менее чем 2 раза')

    """ЗАПРОСЫ ИЗ БД"""
    count_passed = 0
    started_query = None
    started_query_full = datetime.now()
    while count_passed < count:
        waiter = 0
        if started_query:
            waiter = (started_query + timedelta(seconds=period) - datetime.now()).total_seconds()
        if waiter > 0.1:
            sleep(waiter)
        started_query = datetime.now()
        if downBCK:
            bprint('Очистка и сброс БЦК')
            SCPICMD(0xE107)     # очистит БЦК
            sleep(5)
            SCPICMD(0xE060)     # сброс БЦК
            sleep(15)
        execute_db()
        count_passed += 1
    time_duration = datetime.now() - started_query_full

    """ВЫЧИСЛИТЬ ОБЩИЙ РЕЗУЛЬТАТ ВЫРАЖЕНИЯ"""
    rows_text = []
    rows_bools = []
    main_equation = []
    main_equation_reparsed = []
    for simple_eq in equations_all:
        simple_eq = simple_eq[1]
        bools, texts = simple_eq.calculate_db_values()
        rows_text.append(texts)
        rows_bools.append(bools)
        # Восстановленное спарсенное выражение
        main_equation_reparsed.append(' '.join([x for x in (simple_eq._open_backw, simple_eq._operat_not,
                                                            simple_eq._cypher, simple_eq._operator,
                                                            simple_eq._value, simple_eq._cls_backw,
                                                            simple_eq._log_operator) if x != '']))
        # Выражение дял вычисления общего результата
        main_equation.append(' '.join(
            (simple_eq._open_backw, str(bools[0]), simple_eq._cls_backw, simple_eq._log_operator)))
    # составить главное выражение и результат по строке
    main_equation_reparsed = ' '.join(main_equation_reparsed)
    main_equation = ' '.join(main_equation)
    main_eq_result = eval(main_equation)

    """ФОРМАТИРОВАНИЕ ЦВЕТА ТЕКСТА"""
    # вариант с tabulate модулем
    # вариант с подсчетом добавлением separtors ' ' или '\t'
    rows_count = len(rows_text[0])
    for idx_col in range(0, rows_count):
        max_column_len = max([len(x[idx_col]) for x in rows_text])
        sep_symb = ';' if idx_col == rows_count - 1 else ','
        for idx_row, row in enumerate(rows_text):
            sep = sep_symb + ' ' * (max_column_len + 1 - len(row[idx_col])) if sep_symb == ',' else sep_symb
            res = rows_bools[idx_row][idx_col]
            new_text = Text.color_bool(rows_text[idx_row][idx_col], res)
            rows_text[idx_row][idx_col] = new_text + sep

    """ВЫВОД В ТРЕМИНАЛ"""
    if toPrint:
        out = ''
        if toPrint == 2:
            out += '%-25s%s\n' % ('Исходное выражение:', equation)
            out += '%-25s%s\n' % ('Вычисленное выражение:', main_equation_reparsed)
            out += '%-25s%s\n' % ('Время опроса БД:', time_duration.total_seconds())
            out += '%-25s%s\n' % ('Время опроса БД + вычисления:', (datetime.now() - started_query_full).total_seconds())
            out += '%s%s %s\n' % (Text.default, 'Результат:', Text.color_bool(main_eq_result, main_eq_result))
        for x in rows_text:
            out += ''.join(x)
            out += '\n'
        print(out[:-1])
    # TODO: вернуть число ошибок
    errors = sum([1 for x in rows_bools if not x[0]])
    return main_eq_result, equations_dict