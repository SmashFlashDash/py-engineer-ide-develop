def Test_Input():
    from engineers_src.tools.tools import ClassInput
    input = ClassInput.getInputFoo()
    # print('Печатай что написал: ' + input('напиши'))
    input('напиши')

if __name__ == '__main__':
    from time import sleep as sleep2
    import time
    time.sleep = lambda *args: sleep2(0)
    sleep = lambda *args: sleep2(0)
    # Импорт зависимостей на винде
    import sys
    sys.path.insert(0, 'lib/')
    sys.path.insert(0, 'engineers_src/Devices/')
    from engineers_src.tools.tools import *
    Ex.ivk_file_name = "script.ivkng"
    Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"
    from engineers_src.Devices import Device
    from engineers_src.Devices.BCK import BCK
    from engineers_src.Devices.M778 import M778
    from engineers_src.Devices.KIS import KIS
    from engineers_src.Devices.RLCI import RLCI

    try:
        a = BCK()
    except Exception:
        print("Класс не создался")
    try:
        BCK.on()
    except Exception:
        print("Нереализованый метод")
    if BCK.cur is not None:
        raise Exception('Не работает ининт cur в блоке')

    # BCK.cur = 1
    # print('Сделать 1 класс: %s' % BCK.cur)
    # BCK.cur = 0
    # print('Изменили 1 класс: %s' % BCK.cur)
    # M778.cur = 2
    # print('Сделать 2 класс: %s' % M778.cur)
    # print('1 класс: %s' % BCK.cur)
    # print(Device.cur)
    # M778.on(1)
    # M778.off()

    BCK.clc_BCK()
    BCK.downBCK()
    M778.on(1)

    # Тест КИС
    KIS.on(1)
    KIS.print_BARL_levels()
    KIS.get_tmi()
    KIS.sensitive_prm(10)
    KIS.conn_test(1)
    KIS.off()

    # Тест РЛЦИ
    # Тест АСН
    # Тест КСО

    # TODO:
    #  - как сделать from devices import *, можно вынести в __init__
    #  - вынести импорты в этот файл а в тех подхватить что заимпортили
    #  from engineers_src.Devices.dictionariesUVDI import DIstorage изи functions
    #  from engineers_src.Devices.Device import Device изи каждого класса
    #  from engineers_src.Devices.functions import *
    #  from engineers_src.tools.tools import *
