# # DEBUG
# from time import sleep as sleep2
# import time
# time.sleep = lambda *args: sleep2(0)
# sleep = lambda *args: sleep2(0)
# # Импорт зависимостей
# import sys
# sys.path.insert(0, 'lib/')
# from engineers_src.tools.tools import *
# Ex.ivk_file_name = "script.ivkng"
# Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"

import traceback
import logging
from lib.tabulate.tabulate import tabulate
# Импорт с другой папки
# sys.path.insert(0, 'F:/VMShared/ivk-scripts/')  # путь к программе испытаний абсолютный
# DIstorage = None
# windowChooser = None
# sendFromJson = None
# doEquation = None
# executeTMI = None
# exec('from Dictionaries_UVDI import DIstorage')
# exec('from EMSRLCI_foos import windowChooser, sendFromJson, doEquation, executeTMI')
# Импорт с рабочей директории скрипта
from engineers_src.Devices.functions import windowChooser, sendFromJson, doEquation, executeTMI
from engineers_src.Devices.dictionariesUVDI import DIstorage
from engineers_src.Devices import BCK, M778, RLCI
from engineers_src.Devices.Device import LOGGER
from engineers_src.Devices.functions import DB

# TODO:
#  - поток на продление сеанса при запуске проги, должен не вседа продлевать
#    а предлагать переключить комплект
#  - переделать команды ВКЛ ЭА331 ЭА332 на команды БЦК
#  - сеансы в БД с тестом РЛЦИ 6182, 6223, 6181
#    SELECT * FROM dbo.tm
#    WHERE value->>'name' IN ('10.01.BA_FIP1', '10.01.BA_MOD1', '10.01.BA_PCH1', '10.01.BA_UM1') AND value->'value' = '0'
#    ORDER BY tmid ASC LIMIT 100

##################### LOGGER ##################################
"""
file_logger = logging.StreamHandler(open('engineers_src/for_RLCI_EMS/rlci.log', 'a', encoding='UTF8'))
file_logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(bshv)s  - %(message)s'))
LOGGER.addHandler(file_logger)
LOGGER.info('\n')
LOGGER.info('Начало скрипта ' + sys.argv[0])
"""

##################### COMMUTATIONS ############################
DIstorage.commute('M778B', False)
# Кнопки опрос ДИ
btn_ask_di = True
# пауза на опросБД
DB.pause = 10
# паузы БЦК
BCK.clc_pause = 10
BCK.down_pause = 20
# Включенные блоки
M778.cur = None
RLCI.EA332.cur = None
RLCI.EA331.cur = None
RLCI.PCH.cur = None
RLCI.FIP.cur = None
RLCI.MOD.cur = None
RLCI.UM.cur = None


############################### FUNCTIONS ####################################
def ACDC():
    """ДИ ФКП"""
    BCK.clcBCK()
    BCK.downBCK()
    res = Ex.get('ТМИ', {'04.02.VKKEA1': 'КАЛИБР',
                         '04.02.VKKEA2': 'КАЛИБР',
                         '04.02.VBAEA1': 'КАЛИБР',
                         '04.02.VBAEA2': 'КАЛИБР',
                         '04.02.CKKEA1': 'КАЛИБР',
                         '04.02.CKKEA2': 'КАЛИБР',
                         '04.02.CBAEA1': 'КАЛИБР',
                         '04.02.CBAEA2': 'КАЛИБР'}, 'ТЕКУЩ')
    strings = []
    for key in sorted(res.keys()):
        row = [key]
        val = res[key]
        row.extend([str(x) for x in val]) if isinstance(val, list) else row.append(str(val))
        strings.append(row)
    print(tabulate(strings, tablefmt='simple'))


def FKP_RLCI_DR():
    """ДИ ФКП дежурный режим РЛЦИ"""
    if RLCI.EA332.cur is None or RLCI.EA331.cur is None:
        raise Exception('Нет данных о включенных блоках')
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.24]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.1, 1.24]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))


def FKP_RLCI_SR():
    """ДИ ФКП сеансный режим РЛЦИ"""
    if RLCI.EA332.cur is None or RLCI.EA331.cur is None:
        raise Exception('Нет данных о включенных блоках')
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[1.0, 2.93]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[1.0, 3.45]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))


############################## ANTENNA TEST ###############################
def TEST_1():
    yprint('ТЕСТ 1 АФУ-Х ПРОВЕРКА ОСТАНОВКИ ШД - БА-О')
    RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
    sleep(10)
    RLCI.mode('stop SHD', ask_TMI=False)
    RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
    RLCI.EA332.off()
    yprint('ТЕСТ 1 ЗАВЕРШЕН')


def TEST_2():
    yprint('ТЕСТ 2 АФУ-Х ПРОВЕРКА ОСТАНОВКИ ШД - БА-Р')
    RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
    sleep(10)
    RLCI.mode('stop SHD', ask_TMI=False)
    RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
    RLCI.EA332.off()
    yprint('ТЕСТ 2 ЗАВЕРШЕН')


def __TEST_3_4():
    RLCI.isAntennaMoving()  # проверка что антенна движется
    RLCI.waitAntennaStop(period=5*60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка параметров ДНП и имулсьсов НЗ
               "{10.01.BA_AFU_DNP_OX}==0")
    # Отправить массив НЗ 500
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0,
                                         data=AsciiHex(
                                             '0x'
                                             '80500450F401F401640064803200C8000A002C01140084830A0000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                             'A0500550F40158026400C88032002C01140064001E008483140000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                             '000000000000000000000000000000000000000000000000000000000000000000000000'),
                                         std=2))
    sleep(5)
    RLCI.waitAntennaStop(period=60 + 40, toPrint=False)  # ожидание когда антенна остановится в 0 градусной зоне
    executeTMI("{10.01.BA_AFU_IMP_OZ}@H==500" + " and " +  # проверка координат 0 градуснйо зоны
               "{10.01.BA_AFU_IMP_OX}@H==500" + " and " +
               "{10.01.BA_AFU_NP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_NP_OX}@H==0")
    # Запустить отработку массива
    RLCI.mode('start SHD')
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание когда антенна остановится, или sleep(посчитать время)
    executeTMI("{10.01.BA_AFU_IMP_OZ}@H==@same@all" + " and " +  # Проверка НП и ДНП после остановки
               "{10.01.BA_AFU_IMP_OX}@H==@same@all" + " and " +
               "{10.01.BA_AFU_NP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_NP_OX}@H==0" + " and " +
               "{10.01.BA_AFU_DNP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_DNP_OX}@H==0", count=2, period=8)


def TEST_3():
    yprint('ТЕСТ 3 АФУ-Х ПРОВЕРКА ОТРАБОТКИ МАССИВА, ДНП, НП - БА-О')
    RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
    __TEST_3_4()
    RLCI.EA332.off()
    yprint('ТЕСТ 3 ЗАВЕРШЕН', tab=1)


def TEST_4():
    yprint('ТЕСТ 4 АФУ-Х ПРОВЕРКА ОТРАБОТКИ МАССИВА, ДНП, НП - БА-Р')
    RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
    __TEST_3_4()
    RLCI.EA332.off()
    yprint('ТЕСТ 4 ЗАВЕРШЕН')


def __TEST_5_6(text, array):
    RLCI.isAntennaMoving()  # проверка что антенна движется
    yprint('Ждем остановки антены в НП')
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint('Отправка массива НЗ ' + text)
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array), std=2))
    yprint('Ждать АФУ в НЗ')
    sleep(5)
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ждем когда АФУ в 0гр зоне


def TEST_5():
    """4500 - ось 0x; 9500 - ось 0z"""
    yprint('ТЕСТ 5 АФУ-Х ПРОВЕРКА ДИ ДКП oZ - БА-О')
    RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
    __TEST_5_6('0x=4500, 0z=9500', '0x'
                                   '805004509411E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                   'A05005501C25E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                   '000000000000000000000000000000000000000000000000000000000000000000000000')
    yprint('Проверка координат 0гр зоны, ДИ ДКП')
    executeTMI("{10.01.BA_AFU_IMP_OX}@H==[4200, 4800]" + " and " +
               "{10.01.BA_AFU_IMP_OZ}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
               "{10.01.BA_AFU_DKP_OX}@H==1" + " and " +
               "{10.01.BA_AFU_DKP_OZ}@H==0", count=2, period=8)
    RLCI.EA332.off()
    yprint('ТЕСТ 5 ЗАВЕРШЕН')


def TEST_6():
    """9500 - ось 0x; 4500 - ось 0z"""
    yprint('ТЕСТ 6 АФУ-Х ПРОВЕРКА ДИ ДКП oX - БА-Р')
    RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
    __TEST_5_6('0x=9500, 0z=4500', '0x'
                                   '805004501C25E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                   'A05005509411E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                   '000000000000000000000000000000000000000000000000000000000000000000000000')
    yprint('Проверка координат 0гр зоны, ДИ ДКП')
    executeTMI("{10.01.BA_AFU_IMP_OX}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
               "{10.01.BA_AFU_IMP_OZ}@H==[4200, 4800]" + " and " +
               "{10.01.BA_AFU_DKP_OX}@H==0" + " and " +
               "{10.01.BA_AFU_DKP_OZ}@H==1", count=2, period=8)
    RLCI.EA332.off()
    yprint('ТЕСТ 6 ЗАВЕРШЕН')


'''
def __TEST_11_12():
    RLCI.isAntennaMoving()  # проверка что антенна движется
    yprint('Ждем остановки антены в НП')
    RLCI.waitAntennaStop(period=5*60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка параметров ДНП и имулсьсов НЗ
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint('Отправка массива НЗ 0x=1200, 0z=12000')
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0,
                                         data=AsciiHex(
                                             '0x'
                                             '80500450E02E00000000000000000000000000000000000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                             'A0500550E02E000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
                                             '000000000000000000000000000000000000000000000000000000000000000000000000'),
                                         std=2))
    comm_print('Зафиксировать максимальное значение Импульсов 10.01.BA_AFU_IMP_OZ, 10.01.BA_AFU_IMP_OX')
    comm_print('Зафиксировать срабатывание датчиков ДКП 10.01.BA_AFU_DKP_OZ, 10.01.BA_AFU_DKP_OX')
    yprint('Ждать 90с АФУ дойдет до ДКП')
    sleep(90)  # время когда антенна дойдет до ДКП
    # executeTMI("{10.01.BA_AFU_IMP_OZ}@H==[8500, 9300]" + " and " +  # проверка координат и ДКП
    #            "{10.01.BA_AFU_IMP_OX}@H==[8500, 9300]", count=2, period=8)
    impulses = Ex.get('ТМИ', {'10.01.BA_AFU_IMP_OZ': 'НЕКАЛИБР',  # получить значения с момента последнего запроса
                              '10.01.BA_AFU_IMP_OX': 'НЕКАЛИБР'}, 'ИНТЕРВАЛ')
    x = max(impulses['10.01.BA_AFU_IMP_OX'])
    z = max(impulses['10.01.BA_AFU_IMP_OZ'])
    if 8500 < x < 9300:
        gprint('Max 0x: %s' % x)
    else:
        rprint('Max 0x: %s' % x)
        inputG()
    if 8500 < z < 9300:
        gprint('Max 0z: %s' % z)
    else:
        rprint('Max 0z: %s' % z)
        inputG()
    yprint('Ждать возврат АФУ в НП')
    RLCI.waitAntennaStop(period=60 * 5, toPrint=False)              # ждем 5 минут пока антенная вернется в ДНП
    executeTMI("{10.01.BA_AFU_IMP_OZ}@H==@same@all" + " and " +     # Проверка антенна не Движ и ДНП
               "{10.01.BA_AFU_IMP_OX}@H==@same@all" + " and " +
               "{10.01.BA_AFU_DNP_OZ}@H==0" + " and " +
               "{10.01.BA_AFU_DNP_OX}@H==0", count=2, period=8)
    # comm_print("Проверь максимальное значение Импульсов 10.01.BA_AFU_IMP_OZ, 10.01.BA_AFU_IMP_OX")


def TEST_11():
    yprint('ТЕСТ 11 АФУ-Х ПРОВЕРКА ОТРАБОТКИ ДКП, КОЛ_ВО ИМПУЛЬСОВ - БА-О', tab=1)
    RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
    __TEST_11_12()
    RLCI.EA332.off()
    yprint('ТЕСТ 9 ЗАВЕРШЕН', tab=1)


def TEST_12():
    yprint('ТЕСТ 12 АФУ-Х ПРОВЕРКА ОТРАБОТКИ ДКП, КОЛ_ВО ИМПУЛЬСОВ - БА-Р', tab=1)
    RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
    __TEST_11_12()
    RLCI.EA332.off()
    yprint('ТЕСТ 10 ЗАВЕРШЕН', tab=1)
'''


############################### TESTS ########################################
def TEST_7():
    yprint('ТЕСТ 7: БА-О(ЭА332), ПЧ-О(ЭА331), ФИП-О(ЭА330), МОД-О(ЭА331), УМ-О(ЭА331)')
    RLCI.EA332.on(1)
    RLCI.EA331.on(1)
    RLCI.mode('RS485-1')    # RS485-0
    RLCI.PCH.on(1)          # Вкл ПЧ-О
    RLCI.FIP.on(1)          # Вкл ФИП-О
    RLCI.MOD.on(1)          # Вкл МОД-О
    RLCI.UM.on(1)           # Вкл УМ-О
    RLCI.mode('VS1')        # Уст Симв Скор VS1
    RLCI.mode('M1')         # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1')
    RLCI.mode('M2')         # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1')
    RLCI.mode('M3')         # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1')
    RLCI.mode('M4')         # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1')
    RLCI.mode('RS485-2')    # RS485-Р
    RLCI.mode('on imFIP')   # Вкл ИМ-ФИП
    RLCI.mode('M1')         # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1 включен ИМ-ФИП')
    RLCI.mode('M2')         # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1 включен ИМ-ФИП')
    RLCI.mode('M3')         # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1 включен ИМ-ФИП')
    RLCI.mode('M4')         # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1 включен ИМ-ФИП')
    RLCI.UM.off()           # Откл УМ
    RLCI.MOD.off()          # Откл Мод
    RLCI.FIP.off()          # Откл Фип
    RLCI.PCH.off()          # Откл Пч
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 7 ЗАВЕРШЕН')


def TEST_8(ea332=1):
    yprint('ТЕСТ 8: БА-О(ЭА332), ПЧ-Р(ЭА331), ФИП-Р(ЭА330), МОД-Р(ЭА331), УМ-Р(ЭА331)')
    RLCI.EA332.on(ea332)
    RLCI.EA331.on(2)
    RLCI.mode('RS485-1')    # RS485-0
    RLCI.PCH.on(2)  # Вкл ПЧ-Р
    RLCI.FIP.on(2)  # Вкл ФИП-Р
    RLCI.MOD.on(2)  # Вкл МОД-Р
    RLCI.UM.on(2)  # Вкл УМ-Р
    RLCI.mode('VS2')  # Уст Симв Скор VS2
    RLCI.mode('M1')         # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2')
    RLCI.mode('M2')         # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2')
    RLCI.mode('M3')         # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2')
    RLCI.mode('M4')         # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2')
    RLCI.mode('RS485-2')    # RS485-Р
    RLCI.mode('on imFIP')   # Вкл ИМ-ФИП
    RLCI.mode('M1')         # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2 включен ИМ-ФИП')
    RLCI.mode('M2')         # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2 включен ИМ-ФИП')
    RLCI.mode('M3')         # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2 включен ИМ-ФИП')
    RLCI.mode('M4')         # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2 включен ИМ-ФИП')
    RLCI.UM.off()           # Откл УМ
    RLCI.MOD.off()          # Откл Мод
    RLCI.FIP.off()          # Откл Фип
    RLCI.PCH.off()          # Откл Пч
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 8 ЗАВЕРШЕН')


def TEST_9():
    yprint('ТЕСТ 9: БА-Р(ЭА332), ПЧ-О(ЭА331), ФИП-О(ЭА330), МОД-Р(ЭА331), УМ-Р(ЭА331)')
    RLCI.EA332.on(2)
    RLCI.EA331.on(2)
    RLCI.mode('RS485-1')        # RS485-0
    RLCI.PCH.on(1)              # Вкл ПЧ-О
    RLCI.FIP.on(1)              # Вкл ФИП-О
    RLCI.MOD.on(2)              # Вкл МОД-Р
    RLCI.UM.on(2)               # Вкл УМ-Р
    RLCI.mode('VS1')            # Уст Симв Скор VS1
    RLCI.mode('M1')             # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1')
    RLCI.mode('M2')             # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1')
    RLCI.mode('M3')             # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1')
    RLCI.mode('M4')             # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1')
    RLCI.mode('on imFIP')       # Вкл ИМ-ФИП
    RLCI.mode('RS485-1')        # RS485-0
    RLCI.mode('off imFIP')      # Откл ИМ-Фип
    RLCI.mode('on imMOD')       # Вкл ИМ-Мод
    RLCI.mode('off imMOD')      # Откл ИМ-Мод
    RLCI.UM.off()               # Откл УМ
    RLCI.MOD.off()              # Откл Мод
    RLCI.FIP.off()              # Откл Фип
    RLCI.PCH.off()              # Откл Пч
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 9 ЗАВЕРШЕН')


def TEST_10():
    yprint('ТЕСТ 10: БА-Р(ЭА332), ПЧ-Р(ЭА331), ФИП-Р(ЭА330), МОД-О(ЭА331), УМ-О(ЭА331)')
    RLCI.EA332.on(2)
    RLCI.EA331.on(2)
    RLCI.mode('RS485-1')    # RS485-0
    RLCI.PCH.on(2)          # Вкл ПЧ-Р
    RLCI.FIP.on(2)          # Вкл ФИП-Р
    RLCI.MOD.on(1)          # Вкл МОД-О
    RLCI.UM.on(1)           # Вкл УМ-О
    RLCI.mode('VS2')        # Уст Симв Скор VS2
    RLCI.mode('M1')         # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2')
    RLCI.mode('M2')         # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2')
    RLCI.mode('M3')         # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2')
    RLCI.mode('M4')         # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2')
    RLCI.mode('on imFIP')  # Вкл ИМ-ФИП
    RLCI.mode('RS485-1')    # RS485-0
    RLCI.mode('off imFIP')  # Откл ИМ-Фип
    RLCI.mode('on imMOD')   # Вкл ИМ-Мод
    RLCI.mode('off imMOD')  # Откл ИМ-Мод
    RLCI.UM.off()           # Откл УМ
    RLCI.MOD.off()          # Откл Мод
    RLCI.FIP.off()          # Откл Фип
    RLCI.PCH.off()          # Откл Пч
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 10 ЗАВЕРШЕН')


def TEST_11():
    yprint('ТЕСТ 11: Отключение 12мин БА-О(ЭА332), ПЧ-О(ЭА331), ФИП-О(ЭА330), МОД-О(ЭА331), УМ-О(ЭА331)')
    RLCI.EA332.on(1)
    RLCI.EA331.on(1)
    RLCI.PCH.on(1)      # Вкл ПЧ-О
    RLCI.FIP.on(1)      # Вкл ФИП-О
    RLCI.MOD.on(1)      # Вкл МОД-О
    RLCI.UM.on(1)       # Вкл УМ-О
    RLCI.mode('VS1')    # Уст Симв Скор VS1
    RLCI.mode('M1')     # Уст реж М-1
    yprint('Ждать 12 минут отключения РЛЦИ')
    sleep(12 * 60 + 30)
    yprint('Проверка ДИ что РЛЦИ отключен')
    executeTMI(doEquation('10.01.BA_FIP1', '@K', 'off') + " and " +
               doEquation('10.01.BA_MOD1', '@K', 'off') + " and " +
               doEquation('10.01.BA_PCH1', '@K', 'off') + " and " +
               doEquation('10.01.BA_UM1', '@K', 'off') + " and " +
               doEquation('10.01.FIP1_BS', '@K', 'off') + " and " +
               doEquation('10.01.FIP_MOD1_CONNECT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_MOD1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_P_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_F_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH1_F', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM1_P_Out', '@K', 'off'), count=1)
    RLCI.PCH.cur = None
    RLCI.FIP.cur = None
    RLCI.MOD.cur = None
    RLCI.UM.cur = None
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 11 ЗАВЕРШЕН')


def TEST_12():
    """"""
    yprint('ТЕСТ 12: Отключение 12мин БА-Р(ЭА332), ПЧ-Р(ЭА331), ФИП-Р(ЭА330), МОД-Р(ЭА331), УМ-Р(ЭА331)')
    RLCI.EA332.on(2)
    RLCI.EA331.on(2)
    RLCI.PCH.on(2)      # Вкл ПЧ-Р
    RLCI.FIP.on(2)      # Вкл ФИП-Р
    RLCI.MOD.on(2)      # Вкл МОД-Р
    RLCI.UM.on(2)       # Вкл УМ-Р
    RLCI.mode('VS2')    # Уст Симв Скор VS2
    RLCI.mode('M1')     # Уст реж М-1
    yprint('Ждать 12 минут отключения РЛЦИ')
    sleep(12 * 60 + 30)
    yprint('Проверка ДИ что РЛЦИ отключен')
    executeTMI(doEquation('10.01.BA_FIP2', '@K', 'off') + " and " +
               doEquation('10.01.BA_MOD2', '@K', 'off') + " and " +
               doEquation('10.01.BA_PCH2', '@K', 'off') + " and " +
               doEquation('10.01.BA_UM2', '@K', 'off') + " and " +
               doEquation('10.01.FIP2_BS', '@K', 'off') + " and " +
               doEquation('10.01.FIP_MOD2_CONNECT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_MOD2_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH2_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH2_P_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH2_F_SYNT', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH2_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_PCH2_F', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM2_BS', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM2_P', '@K', 'off') + " and " +
               doEquation('10.01.PRD_UM2_P_Out', '@K', 'off'), count=1)
    RLCI.PCH.cur = None
    RLCI.FIP.cur = None
    RLCI.MOD.cur = None
    RLCI.UM.cur = None
    RLCI.EA331.off()
    RLCI.EA332.off()
    yprint('ТЕСТ 12 ЗАВЕРШЕН')


def TEST_13():
    yprint('ТЕСТ 13 аварийное отключение БА-О(ЭА332)')
    RLCI.EA332.on(1)
    RLCI.EA331.on(1)
    RLCI.mode('RS485-1')    # RS485-0
    RLCI.PCH.on(1)          # Вкл ПЧ-О
    RLCI.FIP.on(1)          # Вкл ФИП-О
    RLCI.MOD.on(1)          # Вкл МОД-О
    RLCI.UM.on(1)           # Вкл УМ-О
    sleep(10)
    yprint('СНЯТЬ ПИТАНИЕ ФКП - АВАРИЙНОЕ ОТКЛЮЧЕНИE')
    inputG('Снять питание?')
    RLCI.PCH.cur = None
    RLCI.FIP.cur = None
    RLCI.MOD.cur = None
    RLCI.UM.cur = None
    RLCI.EA331.off()
    RLCI.EA332.off()
    sleep(10)
    yprint('ПРОВЕРКА ВКЛЮЧЕНИЯ')
    inputG('Начать проверку?')
    TEST_7()
    yprint('ТЕСТ 13 ЗАВЕРШЕН')


def TEST_14():
    yprint('ТЕСТ 14 аварийное отключение БА-Р(ЭА332)')
    RLCI.EA332.on(2)
    RLCI.EA331.on(2)
    RLCI.mode('RS485-1')  # RS485-0
    RLCI.PCH.on(2)  # Вкл ПЧ-Р
    RLCI.FIP.on(2)  # Вкл ФИП-Р
    RLCI.MOD.on(2)  # Вкл МОД-Р
    RLCI.UM.on(2)  # Вкл УМ-Р
    sleep(10)
    yprint('СНЯТЬ ПИТАНИЕ ФКП - АВАРИЙНОЕ ОТКЛЮЧЕНИE')
    inputG('Снять питание?')
    RLCI.PCH.cur = None
    RLCI.FIP.cur = None
    RLCI.MOD.cur = None
    RLCI.UM.cur = None
    RLCI.EA331.off()
    RLCI.EA332.off()
    sleep(10)
    yprint('ПРОВЕРКА ВКЛЮЧЕНИЯ')
    inputG('Начать проверку?')
    TEST_8(ea332=2)
    yprint('ТЕСТ 14 ЗАВЕРШЕН')


def TEST_15(num=1):
    yprint('ТЕСТ %s Проверка потребления %s' % (14+num, 'БА-О(ЭА332)' if num == 1 else 'БА-Р(ЭА332)'), tab=1)
    RLCI.EA332.on(num, stop_shd=True)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur]
    executeTMI(" and ".join(di))

    RLCI.EA331.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 0.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))

    RLCI.PCH.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 0.9]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))

    RLCI.FIP.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.7]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))

    RLCI.MOD.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 2.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))

    RLCI.UM.on(num)
    BCK.clcBCK()
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 3.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))

    RLCI.off()
    yprint('ТЕСТ %s ЗАВЕРШЕН' % (14+num), tab=1)


def TEST_16():
    TEST_15(2)


############################## DESCRIPTION ###############################
def TEST_DESCRIPTION():
    # АФУ
    print(Text.yellow + "ТЕСТ 1" + Text.default + ": АФУ-Х ПРОВЕРКА ОСТАНОВКИ ШД - БА-О;")
    print(Text.yellow + "ТЕСТ 2" + Text.default + ": АФУ-Х ПРОВЕРКА ОСТАНОВКИ ШД - БА-Р;")
    print(Text.yellow + "ТЕСТ 3" + Text.default + ": АФУ-Х ПРОВЕРКА ОТРАБОТКИ МАССИВА, ДНП, НП - БА-О;")
    print(Text.yellow + "ТЕСТ 4" + Text.default + ": АФУ-Х ПРОВЕРКА ОТРАБОТКИ МАССИВА, ДНП, НП - БА-Р;")
    print(Text.yellow + "ТЕСТ 5" + Text.default + ": АФУ-Х ПРОВЕРКА ДИ ДКП oZ - БА-О;")
    print(Text.yellow + "ТЕСТ 6" + Text.default + ": АФУ-Х ПРОВЕРКА ДИ ДКП oX - БА-Р;")
    # РЛЦИ
    print(Text.yellow + "ТЕСТ 7" + Text.default + ": БА-О, все -О блоки, VS1;")
    print(Text.yellow + "ТЕСТ 8" + Text.default + ": БА-О, все -Р блоки, VS2;;")
    print(Text.yellow + "ТЕСТ 9" + Text.default + ": БА-Р, ПЧ_ФИП-О, МОД_УМ-Р, VS1;")
    print(Text.yellow + "ТЕСТ 10" + Text.default + ": БА-Р, ПЧ_ФИП-Р, МОД_УМ-О, VS2;")
    print(Text.yellow + "ТЕСТ 11" + Text.default + ": РЛЦИ - ОСНОВНОЙ отключение по 12 минут отключение;")
    print(Text.yellow + "ТЕСТ 12" + Text.default + ": РЛЦИ - РЕЗЕРВНЫЙ отключение по 12 минут отключение;")
    print(Text.yellow + "ТЕСТ 13" + Text.default + ": РЛЦИ - ОСНОВНОЙ АВАРИЙНОЕ ОТКЛЮЧЕНИЕ;")
    print(Text.yellow + "ТЕСТ 14" + Text.default + ": РЛЦИ - РЕЗЕРВНЫЙ АВАРИЙНОЕ ОТКЛЮЧЕНИЕ;")
    print(Text.yellow + "ТЕСТ 15" + Text.default + ": РЛЦИ - ОСНОВНОЙ ВКЛЮЧЕНИЕ ПРОВЕРКА ПОТРЕБЛЕНИЯ;")
    print(Text.yellow + "ТЕСТ 16" + Text.default + ": РЛЦИ - РЕЗЕРВНЫЙ ВКЛЮЧЕНИЕ ПРОВЕРКА ПОТРЕБЛЕНИЯ;")
    # ТЕХ
    # print(Text.yellow + "ТЕСТ 11" + Text.default + ": тех - АФУ-Х ПРОВЕРКА ОТРАБОТКИ ДКП, КОЛ_ВО ИМПУЛЬСОВ - БА-О;")
    # print(Text.yellow + "ТЕСТ 12" + Text.default + ": тех - АФУ-Х ПРОВЕРКА ОТРАБОТКИ ДКП, КОЛ_ВО ИМПУЛЬСОВ - БА-Р;")


####################################################
################### MAIN ###########################
####################################################
foo = {
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
    'ФКП ОПРОС KV': ACDC,
    'ФКП УСТ ДИ1с': lambda: sendFromJson(SCPICMD, 0x4258, AsciiHex('0x0100 0000')),  # уставка на опрос ДИ
    'ФКП УСТ ДИ10с': lambda: sendFromJson(SCPICMD, 0x4258, AsciiHex('0x0A00 0000')),  # уставка на опрос ДИ
    'ФКП РЛЦИ ДР': FKP_RLCI_DR,
    'ФКП РЛЦИ СР': FKP_RLCI_SR,
    'ТЕСТ 1': lambda: TEST_1(),
    'ТЕСТ 2': lambda: TEST_2(),
    'ТЕСТ 3': lambda: TEST_3(),
    'ТЕСТ 4': lambda: TEST_4(),
    'ТЕСТ 5': lambda: TEST_5(),
    'ТЕСТ 6': lambda: TEST_6(),
    'ТЕСТ 7': lambda: TEST_7(),
    'ТЕСТ 8': lambda: TEST_8(),
    'ТЕСТ 9': lambda: TEST_9(),
    'ТЕСТ 10': lambda: TEST_10(),
    'ТЕСТ 11': lambda: TEST_11(),
    'ТЕСТ 12': lambda: TEST_12(),
    'ТЕСТ 13': lambda: TEST_13(),
    'ТЕСТ 14': lambda: TEST_14(),
    'ТЕСТ 15': lambda: TEST_15(),
    'ТЕСТ 16': lambda: TEST_16(),
    'ОПИСАНИЕ ТЕСТОВ': lambda: TEST_DESCRIPTION()
}
# кнопки
btns = (('ТЕСТ 1', 'ТЕСТ 2', 'ТЕСТ 3', 'ТЕСТ 4', 'ТЕСТ 5', 'ТЕСТ 6'),       # афу
        ('ТЕСТ 7', 'ТЕСТ 8', 'ТЕСТ 9', 'ТЕСТ 10'),       # рлци
        ('ТЕСТ 11', 'ТЕСТ 12', 'ТЕСТ 13', 'ТЕСТ 14'),
        ('ТЕСТ 15', 'ТЕСТ 16'),
        # ('ТЕСТ 11', 'ТЕСТ 12'),                          # тех афу
        # 'M778',
        ('РЛЦИ ЭА', 'РЛЦИ ПЧ', 'РЛЦИ ФИП', 'РЛЦИ МОД', 'РЛЦИ УМ', 'РЛЦИ РЕЖИМ', 'РЛЦИ ВСЕ БЛОКИ'),
        ('ФКП ОПРОС KV', 'ФКП УСТ ДИ1с', 'ФКП УСТ ДИ10с', 'ФКП РЛЦИ ДР', 'ФКП РЛЦИ СР'),
        'ОПИСАНИЕ ТЕСТОВ')


print()
yprint('РЛЦИВ ПМ1')
sendFromJson(SCPICMD, 0x4258, AsciiHex('0x0100 0000')),  # уставка на опрос ДИ ФКП
while True:
    print()
    try:
        windowChooser(btnsText=btns, fooDict=foo, labels=['АФУ-Х', 'РЛЦИ-В', '', '', 'РЛЦИ-В', 'ФКП', ''])
    except Exception as ex:
        rprint("ОШИБКА В ТЕСТЕ")
        rprint(traceback.format_exc())
