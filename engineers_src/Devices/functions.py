from engineers_src.Devices.dictionariesUVDI import DIstorage
from ui.commandsSearcherCMD import DataListUV
from engineers_src.tools.ivk_script_tools import *
from cpi_framework.utils.basecpi_abc import AsciiHex
from ivk import config
Ex = config.get_exchange()
from time import sleep


class DB:
    pause = 8


"""открыть json с SCPICMD и SOTC"""
try:
    dataJSON = DataListUV(path=['engineers_src', 'list_uv.json'])
except Exception as ex:
    try:
        dataJSON = DataListUV(path=['..', 'list_uv.json'])  # для запуска без ИВК
    except Exception as ex:
        raise Exception('Нифига не прочитался json')


def print_start_and_end(string):
    """Декоратор вывод в консоль начала и конца работы функции"""
    def decorator(function):
        def wrapper(*args, **kwargs):
            replace_count = string.count('%s')
            text = string
            if replace_count > 1:
                raise Exception('В print_start_and_end максимум 1 вхождение %s')
            elif replace_count == 1:
                text = text % args[0]
            yprint('ВЫПОЛНИТЬ: ' + text)
            res = function(*args, **kwargs)
            yprint('ЗАВЕРШЕНО: ' + text)
            return res
        return wrapper
    return decorator


###################### FUNCTIONS ##############################
def windowChooser(btnsText, fooDict, labels=None, title=None, ret_btn=None):
    """Cоздает форму с кнопками выбора функции и запускает функцию"""
    btn_name = inputGG(btnsText, labels=labels, title=title, ret_btn=ret_btn)  # получить номер кнопки
    if btn_name is None:
        return
    fooDict[btn_name]()  # вызвать функцию
    return btn_name


def sendFromJson(fun, *args, toPrint=True, describe=None, pause=1):
    """отправить SOTC или РК и вывести в консоль описание JSON"""
    if toPrint:
        obj = None
        if fun.__name__ == 'SOTC':
            obj = dataJSON.sotc_dict[str(args[0])]
        elif fun.__name__ == 'SCPICMD':
            obj = dataJSON.uv_dict['all']['list_uv'].get('0x' + hex(args[0])[2:].upper())
        if obj is None:
            yprint('В json нет обьекта: %s %s' % (fun.__name__, args[0]))
        # описание из json
        if obj is None:
            obj_describe = None
        else:
            obj_describe = obj.description
            # доп описание
            ascihex = [x for x in args if isinstance(x, AsciiHex)]
            if len(ascihex) > 0:
                dop_descripton = obj.args.get('AsciiHex(\'' + str(ascihex[0]) + '\')')
                obj_describe = obj_describe if dop_descripton is None else obj_describe + ' :::' + dop_descripton
        # переданное описание
        describe = obj_describe if describe is None else (
            describe if obj_describe is None else obj_describe + "; \n:::" + describe)
    send(fun, *args, toPrint=toPrint, describe=describe)
    sleep(pause)
    # inputG('УВ:  ' + describe)  # пауза после каждого УВ


def doEquation(cyph, calib, status=None, ref_val=None, all_any=None):
    """Для составления выражения из словаря для executeTMI"""
    if all_any is not None and all_any not in ('all', 'any'):
        raise Exception('Параметр all_any принимает значения только: all, any')
    cyph = cyph.strip()
    calib = calib.strip()
    if ref_val is None:
        ref_val = DIstorage.get(cyph)[calib].strip() if status is None else DIstorage.get(cyph)[calib][status].strip()
    equaton = '{%s}%s==%s' % (cyph, calib, str(ref_val).strip())
    if not all_any:
        return equaton
    equaton = equaton.replace('@all', '')
    equaton = equaton.replace('@any', '')
    return equaton + '@' + all_any


def executeTMI(*args, pause=None, stopFalse=True, **kwargs):
    """Вычислить выражние ТМИ с паузой перед опросом"""
    if 'period' not in kwargs:
        kwargs['period'] = DB.pause
    if pause is None:
        pause = DB.pause
    sleep(pause)
    result, dict_cpyphers = controlGetEQ(*args, **kwargs)
    if stopFalse and not result:
        rprint('НЕ НОРМА: проверь ДИ')
        inputG('Проверь ТМИ')
    return result, dict_cpyphers


def getAndSleep(*args, pause=None, **kwargs):
    """Получить значение ДИ с паузой перед опросом чтобы обновилась БД"""
    if pause is None:
        pause = DB.pause
    sleep(pause)  # пауза перед опросм ДИ чтобы записалось в БД
    return Ex.get(*args, **kwargs)


def executeDI(*args, stopFalse=True, **kwargs):
    """
    Проверка ДИ, здесь без паузы, т.к передается значение ДИ
    используется вместе с getAndSleep для получения значения из базы
    :param stopFalse: bool Пауза выполения если возвращает False
    """
    result = controlGet(*args, **kwargs)
    if stopFalse and not result:
        inputG('Проверь ТМИ')
    return result
