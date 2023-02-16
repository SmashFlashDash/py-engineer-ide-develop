# # DEBUG
from time import sleep as sleep2
import time
time.sleep = lambda *args: sleep2(0)
sleep = lambda *args: sleep2(0)
# # Импорт зависимостей
import sys
sys.path.insert(0, 'lib/')
from engineers_src.tools.tools import *
Ex.ivk_file_name = "script.ivkng"
Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"

import traceback
import logging
from datetime import datetime, timedelta
from lib.tabulate.tabulate import tabulate
# Импорт с рабочей директории скрипта
from engineers_src.Devices.functions import windowChooser, sendFromJson, doEquation, executeTMI
from engineers_src.Devices.dictionariesUVDI import DIstorage
from engineers_src.Devices import BCK, M778, RLCI
from engineers_src.Devices.Device import LOGGER
from engineers_src.Devices.functions import DB


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
    yprint('ТЕСТ 1 АФУ-Х БА-О: Остан ШД, Отработка массив, ДКП')
    num = 1
    arrayDescriprion = 'Отправка массива НЗ 0x=4500, 0z=9500'
    array = '0x' \
            '805004509411E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            'A05005501C25E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            '000000000000000000000000000000000000000000000000000000000000000000000000'

    yprint('ПРОВЕРКА УВ ОСТАН ШД')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    sleep(10)
    RLCI.mode('stop SHD', ask_TMI=False)
    RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
    RLCI.EA332.off()

    yprint('ПРОВЕРКА ОТРАБОТКА МАССИВ, ДКП')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    RLCI.isAntennaMoving()  # проверка что антенна движется
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint(arrayDescriprion)
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array), std=2))    # Отправка массива првоерка АФУ в НП
    yprint('Ждать АФУ в НЗ')
    sleep(5)
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ждем когда АФУ в 0гр зоне
    yprint('Проверка координат 0гр зоны, ДИ ДКП')
    executeTMI("{10.01.BA_AFU_IMP_OX}@H==[4200, 4800]" + " and " +
               "{10.01.BA_AFU_IMP_OZ}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
               "{10.01.BA_AFU_DKP_OX}@H==1" + " and " +
               "{10.01.BA_AFU_DKP_OZ}@H==0", count=2, period=8)
    # TODO: пуск ШД и проверить один отработку одного ШД
    RLCI.EA332.off()
    yprint('ТЕСТ 1 ЗАВЕРШЕН', tab=1)


def TEST_2():
    yprint('ТЕСТ 2 АФУ-Х БА-Р: Остан ШД, Отработка массив, ДКП')
    num = 2
    arrayDescriprion = 'Отправка массива НЗ 0x=9500, 0z=4500'
    array = '0x' \
            '805004501C25E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            'A05005509411E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            '000000000000000000000000000000000000000000000000000000000000000000000000'

    yprint('ПРОВЕРКА УВ ОСТАН ШД')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    sleep(10)
    RLCI.mode('stop SHD', ask_TMI=False)
    RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
    RLCI.EA332.off()

    yprint('ПРОВЕРКА ОТРАБОТКА МАССИВ, ДКП')
    RLCI.EA332.on(num, stop_shd=False, ask_TMI=False)
    RLCI.isAntennaMoving()  # проверка что антенна движется
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
    executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
               "{10.01.BA_AFU_DNP_OX}==0")
    yprint(arrayDescriprion)
    array = '0x' \
            '805004501C25E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            'A05005509411E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000' \
            '000000000000000000000000000000000000000000000000000000000000000000000000'
    RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array), std=2))    # Отправка массива првоерка АФУ в НП
    yprint('Ждать АФУ в НЗ')
    sleep(5)
    RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ждем когда АФУ в 0гр зоне
    yprint('Проверка координат 0гр зоны, ДИ ДКП')
    executeTMI("{10.01.BA_AFU_IMP_OX}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
               "{10.01.BA_AFU_IMP_OZ}@H==[4200, 4800]" + " and " +
               "{10.01.BA_AFU_DKP_OX}@H==0" + " and " +
               "{10.01.BA_AFU_DKP_OZ}@H==1", count=2, period=8)
    # TODO: пуск ШД и проверить один отработку одного ШД
    RLCI.EA332.off()
    yprint('ТЕСТ 2 ЗАВЕРШЕН', tab=1)


############################### RLCIV ########################################
def TEST_3():
    yprint('ТЕСТ 3 РЛЦИ-В БА-О: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление')
    num = 1

    RLCI.EA332.on(num)
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur]
    executeTMI(" and ".join(di))
    RLCI.EA331.on(num)
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 0.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.mode('RS485-1')  # RS485-0
    RLCI.PCH.on(num)  # Вкл ПЧ-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 0.9]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.FIP.on(num)  # Вкл ФИП-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.7]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.MOD.on(num)  # Вкл МОД-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 2.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.UM.on(num)  # Вкл УМ-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 3.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    stopTime = datetime.now() + timedelta(minutes=12, seconds=30)

    RLCI.mode('VS1')  # Уст Симв Скор VS1
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1')

    RLCI.mode('RS485-2')  # RS485-Р
    RLCI.mode('VS2')  # Уст Симв Скор VS1
    RLCI.mode('on imFIP')  # Вкл ИМ-ФИП
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2 включен ИМ-ФИП')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2 включен ИМ-ФИП')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2 включен ИМ-ФИП')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2 включен ИМ-ФИП')

    RLCI.mode('on imMOD')  # Вкл ИМ-Мод
    RLCI.mode('off imMOD')  # Откл ИМ-Мод

    # ждать 12 минут
    yprint('Ждать 12 минут отключения по таймеру аппаратуры РЛЦИ')
    while datetime.now() < stopTime:
        sleep(1)
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
    yprint('ТЕСТ 3 ЗАВЕРШЕН', tab=1)


def TEST_4():
    yprint('ТЕСТ 4 РЛЦИ-В БА-Р: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление')
    num = 2

    RLCI.EA332.on(num)
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur]
    executeTMI(" and ".join(di))
    RLCI.EA331.on(num)
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.05, 0.5]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 0.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.mode('RS485-1')  # RS485-0
    RLCI.PCH.on(num)  # Вкл ПЧ-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 0.9]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.FIP.on(num)  # Вкл ФИП-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 1.7]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 1.5]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.MOD.on(num)  # Вкл МОД-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 2.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    RLCI.UM.on(num)  # Вкл УМ-О
    BCK.downBCK()
    di = ["{04.02.VBAEA%s}@K==[25,35]" % RLCI.EA332.cur,
          "{04.02.CBAEA%s}@K==[0.1, 2.0]" % RLCI.EA332.cur,
          "{04.02.VKKEA%s}@K==[25,35]" % RLCI.EA331.cur,
          "{04.02.CKKEA%s}@K==[0.01, 3.0]" % RLCI.EA331.cur]
    executeTMI(" and ".join(di))
    stopTime = datetime.now() + timedelta(minutes=12, seconds=30)

    RLCI.mode('VS1')  # Уст Симв Скор VS1
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS1')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS1')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS1')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS1')

    RLCI.mode('RS485-2')  # RS485-Р
    RLCI.mode('VS2')  # Уст Симв Скор VS1
    RLCI.mode('on imFIP')  # Вкл ИМ-ФИП
    RLCI.mode('M1')  # Уст реж М-1
    inputG('КПА запиши файл режим M1-VS2 включен ИМ-ФИП')
    RLCI.mode('M2')  # Уст реж М-2
    inputG('КПА запиши файл режим M2-VS2 включен ИМ-ФИП')
    RLCI.mode('M3')  # Уст реж М-3
    inputG('КПА запиши файл режим M3-VS2 включен ИМ-ФИП')
    RLCI.mode('M4')  # Уст реж М-4
    inputG('КПА запиши файл режим M4-VS2 включен ИМ-ФИП')

    RLCI.mode('on imMOD')  # Вкл ИМ-Мод
    RLCI.mode('off imMOD')  # Откл ИМ-Мод

    # ждать 12 минут
    yprint('Ждать 12 минут отключения по таймеру аппаратуры РЛЦИ')
    while datetime.now() < stopTime:
        sleep(1)
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
    yprint('ТЕСТ 4 ЗАВЕРШЕН', tab=1)


# def TEST_1():
#     yprint('ТЕСТ 1 АФУ-Х ПРОВЕРКА ОСТАНОВКИ ШД - БА-О')
#     RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
#     sleep(10)
#     RLCI.mode('stop SHD', ask_TMI=False)
#     RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
#     RLCI.EA332.off()
#     yprint('ТЕСТ 1 ЗАВЕРШЕН')
#
#
# def TEST_2():
#     yprint('ТЕСТ 2 АФУ-Х ПРОВЕРКА ОСТАНОВКИ ШД - БА-Р')
#     RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
#     sleep(10)
#     RLCI.mode('stop SHD', ask_TMI=False)
#     RLCI.waitAntennaStop(period=60, toPrint=False)  # ожидание на остановку антенны
#     RLCI.EA332.off()
#     yprint('ТЕСТ 2 ЗАВЕРШЕН')
#
#
# def __TEST_3_4():
#     RLCI.isAntennaMoving()  # проверка что антенна движется
#     RLCI.waitAntennaStop(period=5*60, toPrint=False)  # ожидание на остановку антенны
#     executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка параметров ДНП и имулсьсов НЗ
#                "{10.01.BA_AFU_DNP_OX}==0")
#     # Отправить массив НЗ 500
#     RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0,
#                                          data=AsciiHex(
#                                              '0x'
#                                              '80500450F401F401640064803200C8000A002C01140084830A0000000000000000000000000000000000000000000000000000000000000000000000000000000000'
#                                              'A0500550F40158026400C88032002C01140064001E008483140000000000000000000000000000000000000000000000000000000000000000000000000000000000'
#                                              '000000000000000000000000000000000000000000000000000000000000000000000000'),
#                                          std=2))
#     sleep(5)
#     RLCI.waitAntennaStop(period=60 + 40, toPrint=False)  # ожидание когда антенна остановится в 0 градусной зоне
#     executeTMI("{10.01.BA_AFU_IMP_OZ}@H==500" + " and " +  # проверка координат 0 градуснйо зоны
#                "{10.01.BA_AFU_IMP_OX}@H==500" + " and " +
#                "{10.01.BA_AFU_NP_OZ}@H==0" + " and " +
#                "{10.01.BA_AFU_NP_OX}@H==0")
#     # Запустить отработку массива
#     RLCI.mode('start SHD')
#     RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание когда антенна остановится, или sleep(посчитать время)
#     executeTMI("{10.01.BA_AFU_IMP_OZ}@H==@same@all" + " and " +  # Проверка НП и ДНП после остановки
#                "{10.01.BA_AFU_IMP_OX}@H==@same@all" + " and " +
#                "{10.01.BA_AFU_NP_OZ}@H==0" + " and " +
#                "{10.01.BA_AFU_NP_OX}@H==0" + " and " +
#                "{10.01.BA_AFU_DNP_OZ}@H==0" + " and " +
#                "{10.01.BA_AFU_DNP_OX}@H==0", count=2, period=8)
#
#
# def TEST_3():
#     yprint('ТЕСТ 3 АФУ-Х ПРОВЕРКА ОТРАБОТКИ МАССИВА, ДНП, НП - БА-О')
#     RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
#     __TEST_3_4()
#     RLCI.EA332.off()
#     yprint('ТЕСТ 3 ЗАВЕРШЕН', tab=1)
#
#
# def TEST_4():
#     yprint('ТЕСТ 4 АФУ-Х ПРОВЕРКА ОТРАБОТКИ МАССИВА, ДНП, НП - БА-Р')
#     RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
#     __TEST_3_4()
#     RLCI.EA332.off()
#     yprint('ТЕСТ 4 ЗАВЕРШЕН')
#
#
# def __TEST_5_6(text, array):
#     RLCI.isAntennaMoving()  # проверка что антенна движется
#     yprint('Ждем остановки антены в НП')
#     RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ожидание на остановку антенны
#     executeTMI("{10.01.BA_AFU_DNP_OZ}==0" + " and " +  # првоерка АФУ в НП
#                "{10.01.BA_AFU_DNP_OX}==0")
#     yprint('Отправка массива НЗ ' + text)
#     RLCI.sendArrayToAntenna('КПА', CPIMD(addr=0x0, data=AsciiHex(array), std=2))
#     yprint('Ждать АФУ в НЗ')
#     sleep(5)
#     RLCI.waitAntennaStop(period=5 * 60, toPrint=False)  # ждем когда АФУ в 0гр зоне
#
#
# def TEST_5():
#     """4500 - ось 0x; 9500 - ось 0z"""
#     yprint('ТЕСТ 5 АФУ-Х ПРОВЕРКА ДИ ДКП oZ - БА-О')
#     RLCI.EA332.on(1, stop_shd=False, ask_TMI=False)
#     __TEST_5_6('0x=4500, 0z=9500', '0x'
#                                    '805004509411E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000'
#                                    'A05005501C25E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
#                                    '000000000000000000000000000000000000000000000000000000000000000000000000')
#     yprint('Проверка координат 0гр зоны, ДИ ДКП')
#     executeTMI("{10.01.BA_AFU_IMP_OX}@H==[4200, 4800]" + " and " +
#                "{10.01.BA_AFU_IMP_OZ}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
#                "{10.01.BA_AFU_DKP_OX}@H==1" + " and " +
#                "{10.01.BA_AFU_DKP_OZ}@H==0", count=2, period=8)
#     RLCI.EA332.off()
#     yprint('ТЕСТ 5 ЗАВЕРШЕН')
#
#
# def TEST_6():
#     """9500 - ось 0x; 4500 - ось 0z"""
#     yprint('ТЕСТ 6 АФУ-Х ПРОВЕРКА ДИ ДКП oX - БА-Р')
#     RLCI.EA332.on(2, stop_shd=False, ask_TMI=False)
#     __TEST_5_6('0x=9500, 0z=4500', '0x'
#                                    '805004501C25E8030A00D0870A00F4011400C4890A00000000000A000000000000000000000000000000000000000000000000000000000000000000000000000000'
#                                    'A05005509411E8030A00D0870A00F4011400C4890A000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
#                                    '000000000000000000000000000000000000000000000000000000000000000000000000')
#     yprint('Проверка координат 0гр зоны, ДИ ДКП')
#     executeTMI("{10.01.BA_AFU_IMP_OX}@H==[9200, 9800]" + " and " +  # проверка координат 0гр зоны, ДИ ДКП
#                "{10.01.BA_AFU_IMP_OZ}@H==[4200, 4800]" + " and " +
#                "{10.01.BA_AFU_DKP_OX}@H==0" + " and " +
#                "{10.01.BA_AFU_DKP_OZ}@H==1", count=2, period=8)
#     RLCI.EA332.off()
#     yprint('ТЕСТ 6 ЗАВЕРШЕН')
############################## DESCRIPTION ###############################
def TEST_DESCRIPTION():
    # АФУ
    print(Text.yellow + "ТЕСТ 1" + Text.default + ": АФУ-Х БА-О: Остан ШД, Отработка массив, ДКП;")
    print(Text.yellow + "ТЕСТ 2" + Text.default + ": АФУ-Х БА-Р: Остан ШД, Отработка массив, ДКП;")
    # РЛЦИ
    print(Text.yellow + "ТЕСТ 3" + Text.default + ": РЛЦИ-В БА-О: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление;")
    print(Text.yellow + "ТЕСТ 4" + Text.default + ": РЛЦИ-В БА-Р: VS1, VS2, M1, M2, M3, M4, Откл УМ 12 мин, Потребление;")


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
            'ОТКЛ ЭА332': lambda: RLCI.EA332.off(),
            'ВКЛ ЭА331-1': lambda: RLCI.EA331.on(1),
            'ВКЛ ЭА331-2': lambda: RLCI.EA331.on(2),
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
    'ОПИСАНИЕ ТЕСТОВ': lambda: TEST_DESCRIPTION()
}
# кнопки
btns = (('ТЕСТ 1', 'ТЕСТ 2'),       # афу
        ('ТЕСТ 3', 'ТЕСТ 4'),       # рлци
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
        windowChooser(btnsText=btns, fooDict=foo, labels=['АФУ-Х', 'РЛЦИ-В', 'Упр РЛЦИ-В', 'ФКП', ''])
    except Exception as ex:
        rprint("ОШИБКА В ТЕСТЕ")
        rprint(traceback.format_exc())
