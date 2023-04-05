'''
    ДУГ
1) Выполнить вакуумирование магистралей подачи по окончании ЦНФ (для ТВИ это не принципиально, можно забить хуй)
2) Перед первым включением необходимо включить нагреватели камер разложения
   Для последующих включений это не нужно, т.к. они не отключаются
3) Изменить температурные пределы включения отключения нагревателей БХП на пределы для режима работы
4) Далее, ожидать прогрева камер разложения до температуры более 355 градусов Цельсия 
5) Выполнить прожиг двигателей (аналогично пункту 1 можно забить хуй, на терморегулирование это никак не влияет)
6) Выдать УВ на включение автоматического режима КУД1 и КУД2
    ДУГ ГОТОВ К КОРРЕКЦИИ
7.1) Для осуществления коррекции выдать УВ ХВКЛ_КДУ задав конфигурацию и время коррекции
7.2) Или выдать РИК
'''

from cpi_framework.utils.basecpi_abc import *
from cpi_framework.utils.toolsForCPI import *
from cpi_framework.spacecrafts.omka.cpi import CPIRIK
from engineers_src.Devices.Device import Device
from engineers_src.tools.tools import SCPICMD, Ex, sleep, s2h, b2h, Ex, OBTS, ClassInput
from engineers_src.tools.ivk_script_tools import *
input = ClassInput.getInputFoo()


import time
# from cpi_framework.utils.basecpi_abc import *


def dugPreparationCh1():
    print('Включить нагреватели камер разложения')
    yprint('ВНИМАНИЕ! ЗАПРЕЩАЕТСЯ ВКЛЮЧЕНИЕ НАГРЕВАТЕЛЕЙ КАМЕР РАЗЛОЖЕНИЯ ПРИ ДАВЛЕНИИ БОЛЕЕ 1*10^(-5) торр!')
    yprint('ПРОВЕРЬТЕ ПОКАЗАНИЯ ВАКУУМЕТРОВ!')
    ng = input('0 -- НЕТ, 1 -- ДА')

    SCPICMD(0x106A, OBTS(0), AsciiHex('0x 0000 0000')) #Отключение контроля медианной температуры БХП
    sleep(0.1)
    SCPICMD(0x106F, OBTS(2), AsciiHex('0x 0000 0000')) #Открыть клапаны ДБ1 и ДБ2
    sleep(0.1)
    #Вакуумирование 120 с
    SCPICMD(0x1070, OBTS(120), AsciiHex('0x 0000 0000')) #Закрыть клапаны ДБ1 и ДБ2
    sleep(0.1)
    #Включение нагревателей камер разложения
    if ng == '1':
        SCPICMD(0x1004, OBTS(2), AsciiHex('0x 0000 0000')) #Включить нагреватель ЕК ДБ1
        sleep(0.1)
        SCPICMD(0x1010, OBTS(1), AsciiHex('0x 0000 0000')) #Включить нагреватель ЕК ДБ2
        sleep(0.1)
    SCPICMD(0x1021, OBTS(1), AsciiHex('0x1917 1B1B 0000 0000'))


    '''
    SCPICMD(0x2311, AsciiHex('0x 7500 0000')) #18 нижняя уст
    sleep(2)
    SCPICMD(0x2351, AsciiHex('0x 7A00 0000')) #верхн уст
    sleep(2)
    '''
    #Это уже в следующем сеансе сработает
    #Ex.wait('ТМИ', '{01.01.TIO1.КАЛИБР} > 355 and {01.01.TIO2.КАЛИБР} > 355', 2700) #Ожидать прогрева 45 мин
    return

def dugPreparationCh2():
    SCPICMD(0x1066, OBTS(10), AsciiHex('0x 0000 0000')) #Прожиг двигателей
    sleep(0.1)
    #Включение автоматического режима клапанов
    SCPICMD(0x1009, OBTS(50), AsciiHex('0x 0000 0000'))
    sleep(0.1)
    SCPICMD(0x1015, OBTS(1), AsciiHex('0x 0000 0000'))
    sleep(0.1)
    SCPICMD(0x1069, OBTS(1), AsciiHex('0x 0000 0000')) #Включение контроля медианной температуры БХП
    return
    
'''
#ХВКЛ КДУ
xvkl_kdu_t = int(input('Введите время'))
xvkl_kdu_obts =executionTime(xvkl_kdu_t)
thrust_t = int(input('Задайте время коррекции ДУГ'))
SCPICMD(0x1047, OBTS(xvkl_kdu_obts), AsciiHex('0x{} 0E00 0000 0000'.format(s2h(thrust_t))))
'''

#В следующем сеансе
#РИК
rik_number = 1

def setStartTime():
    print('Задайте время начала коррекции')
    print('0 -- абсолютное, 1 -- относительное')
    time_type = input('')
    if time_type == '1':
        print('Введите количество секунд до начала коррекции')
        time = int(input(''))
    if time_type == '0':
        print('Текущее время БШВ == {}'.format(Ex.get('ТМИ', '14.00.obctime', 'КАЛИБР ТЕКУЩ')))
        print('Введите время в формате ГГГГ:М:Д:Ч:МИН:С')
        time = str(input(''))
        
    return time

def setOrienMode():
    print('''
        
        Задайте режим ориентации:
        0 -- повышение  орбиты
        1 -- понижение орбиты
        2 -- увеличение наклонения
        3 -- уменьшение наклонения
        4 -- повышение орбиты с увеличением наклонения
        5 -- повышение орбиты с уменьшением наклонения
        
        ''')
    return int(input(''))

def setDukConfigValue(num):
    duk_config_dict = {
        '0': 1,
        '1': 17,
        '2': 33,
        '3': 49,
        '4': 65,
        '5': 81,
        '6': 97,
        '7': 113
        }
    return duk_config_dict[num]

def setDugConfigValue(num):
    dug_config_dict = {
        '1': 6,
        '2': 10,
        '3': 14
        }
    return dug_config_dict[num]

def dugRik(xvkl_kdu=False):
    global rik_number
    dur_dug = int(input('Введите время коррекции ДУГ (4..1200 с)'))
    print(
        '''
        
        Выберите конфигурацию ДУГ:
        1 -- ДБ1
        2 -- ДБ2
        3 -- ДБ1+ДБ2
        
        ''')
    dug_config = int(input(''))
    if xvkl_kdu is False:
        orientation = setOrienMode()
    start_time = setStartTime()
    if type(start_time) is int:
        kud1_avto_time = start_time - 10
        kud2_avto_time = 1
        xvkl_kdu_time = 9
    else:
        start_time_diff = sec_diff(start_time)[1]
        kud1_avto_time = start_time_diff - 10
        kud2_avto_time = start_time_diff - 9
        xvkl_kdu_time = start_time_diff
    SCPICMD(0x1009, OBTS(kud1_avto_time), AsciiHex('0x0000 0000 0000 0000'))
    sleep(0.1)
    SCPICMD(0x1015, OBTS(kud2_avto_time), AsciiHex('0x0000 0000 0000 0000'))
    sleep(0.1)
    if xvkl_kdu is True:
        dug_config = setDugConfigValue(str(dug_config))
        SCPICMD(0x1047, OBTS(xvkl_kdu), AsciiHex('0x {} {}00 0000'.format(s2h(dur_dug), b2h(dug_config))))
        return
    Ex.send('КПА', CPIRIK(obts=OBTS(start_time),
        number=rik_number, EngineType=1, DBDug=dug_config, BK=0, OrienMode=orientation, duration=dur_dug))
    rik_number += 1
    return

def dukRik(xvkl_kdu=False):
    global rik_number
    dur_duk = int(input('Введите время коррекции ДУК (60..7200 с)'))
    print('''
        
        Выберите конфигурацию ДУК:
        0 -- БК1-К1-БПК1
        1 -- БК1-К2-БПК1
        2 -- БК2-К1-БПК1
        3 -- БК2-К2-БПК1
        4 -- БК1-К1-БПК2
        5 -- БК1-К2-БПК2
        6 -- БК2-К1-БПК2
        7 -- БК2-К2-БПК2
        
        ''')
    duk_config = int(input(''))
    if xvkl_kdu is False:
        orientation = setOrienMode()
    start_time = setStartTime()
    if type(start_time) is int:
        duk_razr_time = start_time - 16
        pa4_freq_vkl = 1
        spu_vkl_time = 1
        duk_avto_time = 1
        xvkl_kdu_time = 13
        spu_otkl_time = dur_duk + 330
        pa4_freq_otkl = 1
    else:
        start_time_diff = sec_diff(start_time)[1]
        duk_razr_time = start_time_diff - 16
        pa4_freq_vkl = start_time_diff - 15
        spu_vkl_time = start_time_diff - 14
        duk_avto_time = start_time_diff - 13
        xvkl_kdu_time = start_time_diff
        spu_otkl_time = start_time_diff + dur_duk + 330
        pa4_freq_otkl = start_time_diff + dur_duk + 332
    if xvkl_kdu is True:
        duk_config = setDukConfigValue(str(duk_config))
    else:   
        Ex.send('КПА', CPIRIK(obts=OBTS(start_time),
            number=rik_number, EngineType=0, DBDug=0, BK=duk_config, OrienMode=orientation, duration=dur_duk))
        sleep(0.1)
        rik_number += 1
        
    SCPICMD(0x1065, OBTS(duk_razr_time), AsciiHex('0x0100 0000 0000 0000')) #опрос ДИ4-8 раз в 1 с
    sleep(0.1)
    SCPICMD(0x1053, OBTS(pa4_freq_vkl), AsciiHex('0x0100 0000 0000 0000')) #опрос ДИ4-8 раз в 1 с
    sleep(0.1)
    SCPICMD(0x5015, OBTS(spu_vkl_time), AsciiHex('0x0000 0000 0000 0000')) # ФКП2 СПУ 28 В ВКЛ
    sleep(0.1)
    SCPICMD(0x1062, OBTS(duk_avto_time), AsciiHex('0x0000 0000 0000 0000')) #ДУК_АВТО
    sleep(0.1)
    if xvkl_kdu is True:
        SCPICMD(0x1047, OBTS(xvkl_kdu_time), AsciiHex('0x {} {}00 0000'.format(s2h(dur_duk), b2h(duk_config))))
        sleep(0.1)
    SCPICMD(0x53FD, OBTS(spu_otkl_time), AsciiHex('0x0000 0000 0000 0000')) # ФКП2 СПУ 28 В ОТКЛ
    sleep(0.1)
    SCPICMD(0x1053, OBTS(pa4_freq_otkl), AsciiHex('0x0000 0000 0000 0000')) #опрос ДИ4-8 раз в 0 с
    
    return


def launch():
    while True:
        print('''
            1 -- Подготовка ДУГ часть 1
            2 -- Подготовка ДУГ часть 2
            3 -- Коррекция ДУГ (РИК)
            4 -- Коррекция ДУГ (ХВКЛ_КДУ)
            5 -- Коррекция ДУК (РИК)
            6 -- Коррекция ДУК (ХВКЛ_КДУ)
            0 -- Выход
        ''')

        test = input("Введите номер - ")
        if test == '1':
            dugPreparationCh1()
        elif test == '2':
            dugPreparationCh2()
        elif test == '3':
            dugRik()
        elif test == '4':
            dugRik(xvkl_kdu=True)
        elif test == '5':
            dukRik()
        elif test == '6':
            dukRik(xvkl_kdu=True)
        elif test == '0':
            break
