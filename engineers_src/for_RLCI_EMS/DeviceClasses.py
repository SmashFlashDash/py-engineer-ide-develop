# Импорт зависимостей
from engineers_src.tools.tools import *
from threading import Thread
from datetime import datetime, timedelta

# Импорт с рабочей директории скрипта
from engineers_src.for_RLCI_EMS.Dictionaries_UVDI import *
from engineers_src.for_RLCI_EMS.EMSRLCI_foos import sendFromJson, doEquation, executeTMI, print_start_and_end
from lib.tabulate.tabulate import *

# TODO: чтобы хранить информацию по включенным блокам можно класть в редис
# redis_dp_set('KA_status', {
#     'KIS': {
#         'cur': None,
#         'is_sotc_thread': False
#     },
#     'M778': {
#         'cur': None,
#     },
#     'RLCIV': {
#         'cur': None,    # BA
#         'PCH': None,
#         'FIP': None,
#         'MOD': None,
#         'UM': None,
#         'modeM': None,
#         'modeVS': None,
#         'modeRS': None,
#     },
#     'ASN': {
#         'cur': None
#     },
#     'BSK-P': {
#         'cur': None
#     },
#     'BSK-KU': {
#         'cur': None
#     },
#     'BSPA': {
#         'cur': None
#     },
#     'KSO': {
#         'cur': None
#     },
#     'DUK': {
#         'cur': None
#     },
#     })
# s = redis_dp_get('KA_status')
##################### COMMONS ######################
forma = "%-20s --> %s"  # вывод шифр --> значение

# TODO:
#  - сделать абстрактрный класс, и подключать блоки RLCI.PCH, RLCI.EA332 и т.д.
#  - разбить программу на классы по файлам выннести одну общую папку из этих ПМ
#    в классе есть текущий включенный блок, эксепшен или ретурн на вкл если блок включен
#    функция опроса тока, опрос телеметрии блока в массив, функция сбросить массив накопленной тми
#  - сделать global параметр для пере определения параметров пауз в EMSRLCI_foos
#  - дописать в скрипт ПМ где определяются включенные блоки устройств


###################### BCK ##############################
class BCK:
    """Класс описывающий состояние аппарата, некотоыре включенные устройства"""

    @staticmethod
    @print_start_and_end(string='БЦК: ОЧИСТ НАКОП')
    def clc_BCK():
        """Очистить весь накопитель БЦК"""
        sendFromJson(SCPICMD, 0xE107, describe='Ждать 10 сек', pause=10)

    @staticmethod
    @print_start_and_end(string='БЦК: СБРОС НАКОП')
    def downBCK():
        """Сброс ДИ с БЦК в БА КИС-Р всего накопителя"""
        sendFromJson(SCPICMD, 0xE060, describe='Ждать 30 сек', pause=20)


# TODO: при включении СР если есть заранее определнынй уровень установить эт урвоень в КПА
#  заменит '1/2' на int номера барлов
###################### KIS ##############################
class KIS:
    # TODO: заменить barl_cur на barl_running
    barls_uncaliber = {'1/2': 1, '2/2': 2, '3/4': 3, '4/4': 4}
    barl_names = {'1/2': None, '2/2': None, '3/4': None, '4/4': None}  # номера БАРЛ и урвоень настроенный КПА
    barl_cur = None
    thread_running = False
    barl_thread = None
    barls_cmd = {
        'DR 1/2': ((SOTC, 1), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'DR 2/2': ((SOTC, 2), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'DR 3/4': ((SOTC, 3), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'DR 4/4': ((SOTC, 4), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'standby': (SOTC, 73),
        'continue': (SOTC, 95),
        'uncog': (SOTC, 41),
        'fx': (SOTC, 87)
    }

    # @staticmethod
    # def __run_barls_cmd(cmd):
    #     for cmd in cmd:  # перебор команд
    #         if isinstance(cmd, int):
    #             sleep(cmd)
    #         elif isinstance(cmd, tuple):
    #             sendFromJson(*cmd)

    # TODO: подебажить есть параметр на таймер отключения и можно автоматом запустить поток
    #  т.к. когда определили уровень КПА, надо работать на комплектах на этом уровне
    @staticmethod
    def _barl_run():
        """Запустить поток для выдачи команды продлить СР"""
        def continute_session(minutes=10):
            KIS.thread_running = True
            trigger = None
            while KIS.thread_running:
                if trigger is None or trigger < datetime.now():
                    send(*KIS.barls_cmd['continue'], toPrint=True, describe='КИС::: продлить СР\n')
                    trigger = datetime.now() + timedelta(minutes=minutes)
                sleep(10)
            print('Завершен продления сеанса БАРЛ')  # DEBUG

        if KIS.thread_running:
            KIS._barl_stop()
        yprint('ПОТОК SOTC ПРОД')
        KIS.barl_thread = Thread(target=continute_session, daemon=True)
        KIS.barl_thread.start()

    @staticmethod
    def _barl_stop():
        """Остановить поток продлить СР и вернуть переменные в ДР"""
        if KIS.thread_running:
            KIS.thread_running = False
            KIS.barl_cur = None
            KIS.barl_thread.join()  # мб убрать

    @staticmethod
    def __valid_KPA_power(ref_power):
        PowKpa = Ex.get('КПА', 'ДИ_КПА', 'мощн_ПРД')
        if PowKpa is not None and ref_power - 0.1 <= PowKpa <= ref_power + 0.1:
            gprint('Мощность КПА: %s' % PowKpa)
            return True
        else:
            rprint('Мощность КПА: %s' % PowKpa)
            inputG("Проверь Мощность КПА")
            return False

    @staticmethod
    def print_BARL_levels():
        yprint('УРОВНИ БАРЛ:')
        yprint('\n'.join(["\tБАРЛ %s: %s" % (x, KIS.barl_names[x]) for x in ("1/2", "2/2", "3/4", "4/4")]))

    @staticmethod
    @print_start_and_end(string='КИС: ПРЕЙТИ В СР БАРЛ %s')
    def mode_SR(nbarl):
        """
        перевод БАРЛ в СР
        :param nbarl: номер БАРЛ - требуется при БРАЛ в СР
        :return: None
        """
        if nbarl not in KIS.barl_names:
            raise Exception('Недопустимый параметр nbarl=\'%s\'' % nbarl)
        KIS.barl_cur = nbarl
        for cmd in KIS.barls_cmd['DR ' + nbarl]:  # перебор команд
            if isinstance(cmd, int):
                sleep(cmd)
            elif isinstance(cmd, tuple):
                sendFromJson(*cmd)
        # KIS.conn_DI()

    @staticmethod
    @print_start_and_end(string='КИС: ПРЕЙТИ В ДР')
    def mode_DR():
        """
        перевод БАРЛ в ДР
        :return: None
        """
        sendFromJson(*KIS.barls_cmd['standby'])  # одна команда
        KIS._barl_stop()

    @staticmethod
    @print_start_and_end(string='КИС: УСТАНОВИТЬ ИЗМ УРОВЕНЬ ПРД КПА')
    def set_KPA_level():
        """
        Установить найденный ранее уровень мощности КПА КИС для текущего БАРЛ
        """
        if KIS.barl_cur is None:
            raise Exception("Чобы установить уровень КПА необходимо включить БАРЛ")
        if KIS.barl_names[KIS.barl_cur] is None:
            raise Exception("Уровень мощности прд КПА не измерен")
        bprint("Устаовить уровень мощности прд КПА...")
        Ex.send('КПА', KPA('Мощность-уст', KIS.barl_names[KIS.barl_cur]))  # установить заданую мощность КПА
        sleep(8)
        KIS.__valid_KPA_power(KIS.barl_names[KIS.barl_cur])

    @staticmethod
    @print_start_and_end(string='КИС: ПОИСК МИН УР МОЩ КПА КИС ДЛЯ ТЕК БАРЛ')
    def sens(n_cmd):
        """
        Поиск минимального уровня мощности КПА КИС, чтобы проходили команды на БАРЛ
        :param n_cmd: кол-во раз сколько будет выдана комманда
        """
        # Установим минимальную мощность КПА и долбим команды пока не пройдут все
        if KIS.barl_cur not in KIS.barl_names:
            raise Exception("Замер чувствит ПРМ производится при включенном БАРЛ")
        yprint('КИС замер чувствительности БАРЛ %s' % KIS.barl_cur, tab=1)
        power_count = 0
        powers_tx = [x * 1.0 for x in tuple(range(-60, -85, -2)) + tuple(range(-85, -110, -2))]  # значения мощности КПА
        # -60 -62 ... -84 -85 -87 ... -109
        run_setting = True
        while run_setting and power_count < len(powers_tx):
            power_transmitter = powers_tx[power_count]
            bprint('Уст Мощность КПА %s dbm...' % power_transmitter)
            Ex.send('КПА', KPA('Мощность-уст', power_transmitter))  # установить заданую мощность КПА
            sleep(8)
            # првоерить телеметрию мощность КПА
            KIS.__valid_KPA_power(power_transmitter)
            errors_count = KIS.conn_test(n_cmd)     # протестить соединение
            # решение оператор установить уровень, предыдущий или продолжить настройку
            btn_name = inputGG(title='Настройка мощности КПА КИС', btnsList=([('Продолжить', 'ЗАВ НАСТ ИСП ПРЕД УРОВЕНЬ')]))
            if btn_name != 'Продолжить':
                run_setting = False
            power_count += 1
        power_count -= 1
        power_count = power_count if power_count in (0, len(powers_tx)-1) else power_count - 1   # крайние индексы не менять
        bprint('Настроенный уровень сигнала КПА: %s dbm' % powers_tx[power_count])
        # добавить в словарь урвоень сигнала
        KIS.barl_names[KIS.barl_cur] = powers_tx[power_count]
        Ex.send('КПА', KPA('Мощность-уст', KIS.barl_names[KIS.barl_cur]))

    @staticmethod
    @print_start_and_end(string='КИС: ПРОВЕРКА ПРОХОЖДЕНИЯ КОММАНД')
    def conn_test(n_cmd):
        """
        Проверка прохождения команд
        :param n_cmd: кол-во раз сколько будет выданы комманды
        """
        result = []
        for cmd_count in range(0, n_cmd):
            sendFromJson(*KIS.barls_cmd['uncog'])
            result.append(executeTMI(doEquation('15.00.NRK%s' % KIS.barl_cur, '@H', ref_val=KIS.barls_cmd['uncog'][1]),
                                     pause=8, count=1, stopFalse=False)[0])
            sendFromJson(*KIS.barls_cmd['fx'])
            result.append(executeTMI(doEquation('15.00.NRK%s' % KIS.barl_cur, '@H', ref_val=KIS.barls_cmd['fx'][1]),
                                     pause=8, count=1, stopFalse=False)[0])
        errors_count = result.count(False)
        comm_print('Ошибок приема %s из %s' % (errors_count, 2 * n_cmd))
        return errors_count

    @staticmethod
    @print_start_and_end(string='КИС: ПРОВЕРКА СР ДЛЯ ТЕК БАРЛ')
    def conn_DI():
        if KIS.barl_cur not in KIS.barl_names:
            raise Exception("Провека СР производится при включенном БАРЛ")
        bprint('ПРОВЕРКА ОБМЕНА ПО МКПД. ДИ = 1 - РАБОТАЕТ')
        bprint('ПРОВЕРКА НОМЕРА АКТИВНОГО КОМПЛЕКТА БАРЛ')
        bprint('ПРОВЕРКА УРОВНЯ ПРИНИМАЕМОГО СИГНАЛА (норма 90-210)')
        executeTMI(' and '.join((doEquation('15.00.MKPD%s' % KIS.barl_cur, '@H', ref_val=1),
                                 doEquation('15.00.NBARL', '@H', ref_val=KIS.barls_uncaliber[KIS.barl_cur]-1),
                                 doEquation('15.00.UPRM%s' % KIS.barl_cur, '@H', ref_val='[80,255]'))), count=1)


##################### MB #################################
class MB:
    cur = None

    @staticmethod
    @print_start_and_end(string='М778: М778')
    def power_on(num):
        """КСО подать питание на блок MB"""
        if MB.cur is not None:
            raise Exception('Выключи текущий M778b')    # MB.off
        if num == 1:
            sendFromJson(SCPICMD, 0x40CB, describe='Вкл M778B1', pause=1)
        elif num == 2:
            sendFromJson(SCPICMD, 0x4193, describe='Вкл M778B2', pause=1)
        else:
            raise Exception('Номер блока только 1 и 2')
        MB.cur = num

    @staticmethod
    @print_start_and_end(string='М778: ВКЛ')
    def off():
        sendFromJson(SCPICMD, 0x43EB, describe='Отключить M778B', pause=1)
        MB.cur = None


##################### RLCIV ##############################
class RLCI:
    """Управлние РЛЦИ, ПЧ ФИП, УМ, БА, включаются по отдельности"""
    cur_EA332 = None
    cur_EA331 = None
    cur_PCH = None
    cur_FIP = None
    cur_MOD = None
    cur_UM = None
    uv = {
        'M1': lambda: sendFromJson(SCPICMD, 0xA00E),
        'M2': lambda: sendFromJson(SCPICMD, 0xA00F),
        'M3': lambda: sendFromJson(SCPICMD, 0xA010),
        'M4': lambda: sendFromJson(SCPICMD, 0xA011),
        'VS1': lambda: sendFromJson(SCPICMD, 0xA01A),
        'VS2': lambda: sendFromJson(SCPICMD, 0xA01B),
        'RS485-1': lambda: sendFromJson(SCPICMD, 0xA014),
        'RS485-2': lambda: sendFromJson(SCPICMD, 0xA016),
        'on imFIP': lambda: sendFromJson(SCPICMD, 0xA00C),
        'off imFIP': lambda: sendFromJson(SCPICMD, 0xA00D),
        'on imMOD': lambda: sendFromJson(SCPICMD, 0xA012, pause=5),
        'off imMOD': lambda: sendFromJson(SCPICMD, 0xA013, pause=5),
        'stop SHD': lambda: sendFromJson(SCPICMD, 0xA018),
        'start SHD': lambda: sendFromJson(SCPICMD, 0xA017)
    }
    uv_di = {
        'M1': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M1'), count=1),
        'M2': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M2'), count=1),
        'M3': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M3'), count=1),
        'M4': lambda: executeTMI(doEquation('10.01.PRD_MOD_M', '@K', 'M4'), count=1),
        'VS1': lambda: executeTMI(doEquation('10.01.MOD_VS', '@K', 'VS1'), count=1),
        'VS2': lambda: executeTMI(doEquation('10.01.MOD_VS', '@K', 'VS2'), count=1),
        'RS485-1': lambda: '',
        'RS485-2': lambda: '',
        'on imFIP': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'imit') + " and " +
                                       doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5),
        'off imFIP': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                                        doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5),
        'on imMOD': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                                       doEquation('10.01.PRD_MOD_INFO', '@K', 'imit') + " and " +
                                       doEquation('10.01.PRD_MOD_FIP_INF', '@K', 'off') + " and " +
                                       doEquation('10.01.FIP_M778B_INF', '@K', 'off'), count=5, period=5),
        'off imMOD': lambda: executeTMI(doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                                        doEquation('10.01.PRD_MOD_INFO', '@K', 'cele') + " and " +
                                        doEquation('10.01.PRD_MOD_FIP_INF', '@K', 'on') + " and " +
                                        doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5),
        'stop SHD': lambda: RLCI.waitAntennaStop(period=60, toPrint=False),
        'start SHD': lambda: RLCI.isAntennaMoving(),
        'all_off': lambda: executeTMI(doEquation('10.01.BA_FIP1', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_FIP2', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_MOD1', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_MOD2', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_PCH1', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_PCH2', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_UM1', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_UM2', '@K', 'off') + " and "
                                      + doEquation('10.01.BA_TEMP_CARD', '@K') + " and "
                                      + doEquation('10.01.BA_TEMP_CONTR', '@K') + " and "
                                      + doEquation('10.01.BA_U_Ret1', '@K') + " and "
                                      + doEquation('10.01.BA_U_Ret2', '@K') + " and "
                                      + doEquation('10.01.BA_Sec', '@K') + " and "
                                      + doEquation('10.01.BA_NUMB_LAST_UV', '@H') + " and "
                                      + doEquation('10.01.BA_FRAME_COUNTER_DI', '@K') + " and "
                                      + doEquation('10.01.PRD_MOD1_U_SIT1_Temp', '@K') + " and "
                                      + doEquation('10.01.PRD_MOD2_U_SIT5_Temp', '@K') + " and "
                                      + doEquation('10.01.PRD_KONV_U_SIT6_Temp', '@K') + " and "
                                      + doEquation('10.01.BA_AFU_IMP_OX', '@K') + " and "
                                      + doEquation('10.01.BA_AFU_IMP_OZ', '@K'), count=2)
    }

    @staticmethod
    def isAntennaMoving():
        bprint('Проверка что антенна движется...')
        executeTMI("{10.01.BA_AFU_IMP_OZ}@H==@unsame@all" + " and " +
                   "{10.01.BA_AFU_IMP_OX}@H==@unsame@all", count=2, toPrint=True)

    @staticmethod
    def waitAntennaStop(period=0, toPrint=False, query_period=8):
        """ Ожидаие остановки антенны
        @param int period:
        @param bool toPrint:
        @param int query_period:
        """
        bprint('Ожидание остановки антенны')
        start = datetime.now()
        while True:
            res, values = controlGetEQ("{10.01.BA_AFU_IMP_OZ}@H==@same@all" + " and " +
                                       "{10.01.BA_AFU_IMP_OX}@H==@same@all", count=2, period=query_period,
                                       toPrint=toPrint)
            if res:
                bprint('Антенна остановлена')
                break
            elif (datetime.now() - start).total_seconds() >= period:
                inputG('Антенна не остановилась')
                break

    @staticmethod
    def sendArrayToAntenna(*sendArgs):
        inputG('Выдать массива на Антенну?')
        print('ВЫДАЧА МАССИВА')
        Ex.send(*sendArgs)
        sleep(5)
        sendFromJson(SCPICMD, 0xE051, AsciiHex('0x0000 0000 0200 0000'), pause=0)

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ПОДАТЬ ПИТАНИЕ ЭА332 %s')
    def power_on_ea332(ea332, stop_shd=True, ask_TMI=True):
        """КСО подать питание на блоки РЛЦИ ВКЛ ОПР и остановить антенну"""
        if RLCI.cur_EA332 is not None:
            raise Exception('ЭА332 включен!')
        if ea332 == 1:
            # sendFromJson(SCPICMD, 0x40DB, pause=1)  # ЭА332-О
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0113010000000000'), pause=1)  # ЭА332-О
        elif ea332 == 2:
            # sendFromJson(SCPICMD, 0x41A3, pause=1)  # ЭА332-Р
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0113020000000000'), pause=1)  # ЭА332-Р
        else:
            raise Exception('Неверный параметр')
        if stop_shd:
            sendFromJson(SCPICMD, 0xA018)  # Остан ШД
        # sendFromJson(SCPICMD, 0xE06F, AsciiHex('0x0A01 0000 0000 0000'), describe='ВКЛ ОПР РЛЦИ-В')
        RLCI.cur_EA332 = ea332
        if ask_TMI:
            RLCI.uv_di['all_off']()

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ПОДАТЬ ПИТАНИЕ ЭА331 %s')
    def power_on_ea331(ea331):
        """КСО подать питание на блоки РЛЦИ ВКЛ ОПР и остановить антенну"""
        if RLCI.cur_EA331 is not None:
            raise Exception('ЭА331 включен!')
        if ea331 == 1:  # ЭА331-О
            # sendFromJson(SCPICMD, 0x40D9, pause=1)  # ЭА331-О
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0111010000000000'))
        elif ea331 == 2:
            # sendFromJson(SCPICMD, 0x41A1, pause=1)  # ЭА331-Р
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0111020000000000'))
        else:
            raise Exception('Неверный параметр')
        RLCI.cur_EA331 = ea331

    @staticmethod
    @print_start_and_end(string='РЛЦИ: СНЯТЬ ПИТАНИЕ ЭА332')
    def power_off_ea332():
        """КСО снять питание РЛЦИ"""
        # sendFromJson(SCPICMD, 0x43FB, pause=1)  # Снять питание ЭА332
        # sendFromJson(SCPICMD, 0xE06F, AsciiHex('0x0A00 0000 0000 0000'), describe='ОТКЛ ОПР РЛЦИ-В')
        sendFromJson(SCPICMD, 0xE005, AsciiHex('0113000000000000'), pause=1)  # Снять питание ЭА332
        RLCI.cur_EA332 = None

    @staticmethod
    @print_start_and_end(string='РЛЦИ: СНЯТЬ ПИТАНИЕ ЭА331')
    def power_off_ea331(ea331):
        """КСО снять питание РЛЦИ"""
        # sendFromJson(SCPICMD, 0x43F9, pause=1)  # Снять питание ЭА331
        sendFromJson(SCPICMD, 0xE005, AsciiHex('0111000000000000'), pause=1)  # Снять питание ЭА331
        RLCI.cur_EA331 = None

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ВКЛ ПЧ %s')
    def on_PCH(block_num):
        """Включени РЛЦИ ПЧ"""
        if RLCI.cur_PCH is not None:
            raise Exception('РЛЦИ ПЧ включен!')
        if block_num == 1:
            sendFromJson(SCPICMD, 0xA000)  # Вкл ПЧ-О
        elif block_num == 2:
            sendFromJson(SCPICMD, 0xA001)  # Вкл ПЧ-Р
        else:
            raise Exception('Неверный параметр')
        executeTMI(doEquation('10.01.BA_PCH%s' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_PCH%s_BS' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_PCH%s_P_SYNT' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_PCH%s_F_SYNT' % block_num, '@K', 'on'), count=1)  # Добавить 10.01.PRD_PCH1_F как в ТЕСТ 3
        RLCI.cur_PCH = block_num

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ОТКЛ ПЧ')
    def off_PCH():
        sendFromJson(SCPICMD, 0xA002)  # Откл Пч
        executeTMI(doEquation('10.01.BA_PCH%s' % RLCI.cur_PCH, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_PCH%s_BS' % RLCI.cur_PCH, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_PCH%s_P_SYNT' % RLCI.cur_PCH, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_PCH%s_F_SYNT' % RLCI.cur_PCH, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_PCH%s_F' % RLCI.cur_PCH, '@K', 'off'), count=1)
        RLCI.cur_PCH = None

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ВКЛ ФИП %s')
    def on_FIP(block_num):
        """Включени РЛЦИ ФИП"""
        if RLCI.cur_FIP is not None:
            raise Exception('РЛЦИ ФИП включен!')
        if block_num == 1:
            sendFromJson(SCPICMD, 0xA003)  # Вкл ФИП-О
        elif block_num == 2:
            sendFromJson(SCPICMD, 0xA004)  # Вкл ФИП-Р
        else:
            raise Exception('Неверный параметр')
        executeTMI(doEquation('10.01.BA_FIP%s' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.FIP%s_BS' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.FIP%s_U' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.FIP_INFO', '@K', 'cele') + " and " +
                   doEquation('10.01.FIP_M778B%s_CONNECT' % MB.cur, '@K', 'on') + " and " +
                   doEquation('10.01.FIP_PLL1', '@K', 'on') + " and " +
                   doEquation('10.01.FIP_PLL2', '@K', 'on') + " and " +
                   doEquation('10.01.FIP_TEMP_IP', '@K') + " and " +
                   doEquation('10.01.FIP_TEMP_PLIS', '@K'), count=1)
        RLCI.cur_FIP = block_num

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ОТКЛ ФИП')
    def off_FIP():
        sendFromJson(SCPICMD, 0xA005)  # Откл Фип
        executeTMI(doEquation('10.01.BA_FIP%s' % RLCI.cur_FIP, '@K', 'off') + " and " +
                   doEquation('10.01.FIP%s_BS' % RLCI.cur_FIP, '@K', 'off') + " and " +
                   doEquation('10.01.FIP%s_U' % RLCI.cur_FIP, '@K', 'off') + " and " +
                   # doEquation('10.01.FIP_M778B%s_CONNECT' % MB.cur, '@K', 'off') + " and " +  # не должен приходить?
                   # doEquation('10.01.FIP_M778B_INF', '@K', 'off') + " and " +  # не должен приходить?
                   doEquation('10.01.FIP_PLL1', '@K', 'off') + " and " +
                   doEquation('10.01.FIP_PLL2', '@K', 'off'), count=1)
        RLCI.cur_FIP = None

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ВКЛ МОД %s')
    def on_MOD(block_num):
        """Включени РЛЦИ МОД"""
        if RLCI.cur_MOD is not None:
            raise Exception('РЛЦИ МОД включен!')
        if block_num == 1:
            sendFromJson(SCPICMD, 0xA006)  # Вкл МОД-О
        elif block_num == 2:
            sendFromJson(SCPICMD, 0xA007)  # Вкл МОД-Р
        else:
            raise Exception('Неверный параметр')
        executeTMI(doEquation('10.01.BA_MOD%s' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.FIP_MOD%s_CONNECT' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_MOD%s_BS' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_MOD%s_U' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_MOD_INFO', '@K', 'cele') + " and " +
                   doEquation('10.01.PRD_MOD_M', '@K', 'M4') + " and " +
                   doEquation('10.01.PRD_MOD_FIP%s_CONNECT' % RLCI.cur_FIP, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_MOD_STAT_FREQ_PLL', '@K', 'on') + " and " +
                   doEquation('10.01.PRD_MOD_TEMP_CARD', '@K') + " and " +
                   doEquation('10.01.PRD_MOD_TEMP_PLIS', '@K') + " and " +
                   doEquation('10.01.PRD_PCH%s_P' % RLCI.cur_PCH, '@K', 'on'), count=1)
        executeTMI(doEquation('10.01.PRD_MOD_FIP_INF', '@K', 'on') + " and " +
                   doEquation('10.01.FIP_M778B_INF', '@K', 'on'), count=5, period=5)
        RLCI.cur_MOD = block_num

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ОТКЛ МОД')
    def off_MOD():
        sendFromJson(SCPICMD, 0xA008)  # Откл Мод
        executeTMI(doEquation('10.01.BA_MOD%s' % RLCI.cur_MOD, '@K', 'off') + " and " +
                   doEquation('10.01.FIP_MOD%s_CONNECT' % RLCI.cur_MOD, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_MOD%s_BS' % RLCI.cur_MOD, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_MOD%s_U' % RLCI.cur_MOD, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_MOD_STAT_FREQ_PLL', '@K', 'off') + " and " +
                   doEquation('10.01.PRD_PCH%s_P' % RLCI.cur_PCH, '@K', 'off'), count=1)
        RLCI.cur_MOD = None

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ВКЛ УМ %s')
    def on_UM(block_num):
        """Включени РЛЦИ УМ"""
        if RLCI.cur_UM is not None:
            raise Exception('РЛЦИ УМ включен!')
        if block_num == 1:
            sendFromJson(SCPICMD, 0xA009)  # Вкл УМ-О
        elif block_num == 2:
            sendFromJson(SCPICMD, 0xA00A)  # Вкл УМ-Р
        else:
            raise Exception('Неверный параметр')
        executeTMI(doEquation('10.01.BA_UM%s' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_UM%s_BS' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_UM%s_P' % block_num, '@K', 'on') + " and " +
                   doEquation('10.01.PRD_UM%s_P_Out' % block_num, '@K', 'on'), count=1)
        RLCI.cur_UM = block_num

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ОТКЛ УМ')
    def off_UM():
        sendFromJson(SCPICMD, 0xA00B)  # Откл УМ
        executeTMI(doEquation('10.01.BA_UM%s' % RLCI.cur_UM, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_UM%s_BS' % RLCI.cur_UM, '@K', 'off') + " and " +
                   doEquation('10.01.PRD_UM%s_P' % RLCI.cur_UM, '@K', 'off'), count=1)
        RLCI.cur_UM = None

    @staticmethod
    @print_start_and_end(string='РЛЦИ: РЕЖИМ')
    def mode(mode, valid_di=True):
        """ЗАпустить режим M1 M2 M3 M4 имитатор МОД ИМ ФИП, MOD_VS"""
        RLCI.uv[mode]()
        if valid_di:
            RLCI.uv_di[mode]()

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ОПРОСИТЬ ВСЕ')
    def di_full():
        """Опросить телеметрию по всем блокам"""
        pass

    @staticmethod
    @print_start_and_end(string='РЛЦИ: ОТКЛ ВСЕ БЛОКИ')
    def off_all():
        """ОТКЛ ВСЕ БЛОКИ РЛЦИ"""
        sendFromJson(SCPICMD, 0xA00B),  # Откл УМ
        sendFromJson(SCPICMD, 0xA008),  # Откл Мод
        sendFromJson(SCPICMD, 0xA005),  # Откл Фип
        sendFromJson(SCPICMD, 0xA002),  # Откл Пч
        sleep(1)
        RLCI.power_off_ea331()
        RLCI.power_off_ea332()


##################### ASN ##############################
class ASN:
    """ ПЕРЕД ЗАПУСУКОМ АСН ЗАПУСТИТЬ К2-100 и сценарий какойт"""
    cur_block = None
    cur_syst = None
    

    @staticmethod
    def __validate_block_num(num):
        if num is None:
            raise Exception('Необходимо включить АСН')
        elif not isinstance(num, int) or not (0 < num < 3):
            raise Exception('Неверный параметр')

    @staticmethod
    def __get_syst_num(num):
        return {1: 11, 2: 12}[num]

    @staticmethod
    @print_start_and_end(string='АСН: ВКЛ %s')
    def on(block_num):
        """Включение АСН и проверка телеметри"""
        if ASN.cur_block is not None:
            raise Exception('АСН включен')
        ASN.__validate_block_num(block_num)
        if block_num == 1:
            # sendFromJson(SCPICMD, 0x4005, pause=1)   # Вкл АСН1 через канал 5
            # sendFromJson(SCPICMD, 0xE219, pause=1)   # Вкл обмен АСН1
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0106010000000000'), pause=1)  # Включить АСН1
        elif block_num == 2:
            # sendFromJson(SCPICMD, 0x4195, pause=1)  # Вкл АСН2 через канал 6
            # sendFromJson(SCPICMD, 0xE230, pause=1)  # Вкл обмен АСН2
            sendFromJson(SCPICMD, 0xE004, AsciiHex('0109000000000000'), pause=1)  # Включить АСН2
            sendFromJson(SCPICMD, 0xE22D, pause=1)  # Выключить приоритет АСН1
            sendFromJson(SCPICMD, 0xE243, pause=1)  # Включить приоритет АСН2
        ASN.cur_block = block_num
        ASN.cur_syst = ASN.__get_syst_num(block_num)
        bprint("Проверка состояния АСН")
        # BCK.clc_BCK()
        # sendFromJson(SCPICMD, 0xE0A0, pause=5)   # Запрос ДИ2 ФКП-1 (КПТ)
        # BCK.downBCK()
        # DI_BA = ad_dict_DI_BA(block_num)
        # res, cyphs = executeTMI(doEquation(DI_BA["ASN_key2_state"], "@K", ref_val='\'включено\'') + " and " +
        #                         doEquation(DI_BA["CASN"], "@K", ref_val='[0.5, 2.0]') + " and " +
        #                         doEquation(DI_BA["VASN"], "@K", ref_val='[23.0, 34.0]'), pause=8)
        # if res:
        #     gprint('НОРМА ВКЛЮЧЕНИЕ АСН')
        # else:
        #     rprint("НЕ НОРМА ОТКЛЮЧИ АСН")
            # ASN.off(block_num)
            # rprint('АСН не норма ТЕСТ ЗАВРЕШЕН')
        # sleep(5)
        # ASN.res_control(block_num)

    @staticmethod
    @print_start_and_end(string='АСН: ОТКЛ %s')
    def off(block_num):
        """Отключение АСН"""
        ASN.__validate_block_num(block_num)
        if block_num == 1:
            print("УВ: Отключить обмены с АСН1")
            # sendFromJson(SCPICMD, 0xE21A, pause=1)  # Отключить обмены с АСН1 0xE21A EXCH_OFF_ASN1
            sendFromJson(SCPICMD, 0xE005, AsciiHex('0106000000000000'), pause=1)  # Отключить АСН1
        else:
            print("УВ: Отключить обмены с АСН2")
            # sendFromJson(SCPICMD, 0xE231, pause=1)  # Отключить обмены с АСН1 0xE21A EXCH_OFF_ASN1
            sendFromJson(SCPICMD, 0xE005, AsciiHex('0109000000000000'), pause=1)  # Отключить АСН2
        # sendFromJson(SCPICMD, 0x43ED, pause=1)   # Отключить АСН  (Каналы 5 и 6)
        ASN.cur_block = None
        ASN.cur_syst = None
        # bprint("Проверка состояния АСН")
        # sleep(25)
        # BCK.clc_BCK()
        # sendFromJson(SCPICMD, 0xE0A0, pause=5)  # # Запрос ДИ2 ФКП-1 (КПТ)
        # BCK.downBCK()
        # DI_BA = ad_dict_DI_BA(block_num)
        # executeTMI(doEquation(DI_BA["ASN_key2_state"], "@K", ref_val='\'отключен\'') + " and " +
        #            doEquation(DI_BA["CASN"], "@K", ref_val='[0, 0.06]') + " and " +
        #            doEquation(DI_BA["VASN"], "@K", ref_val='[0, 0.4]'), pause=0)

    @staticmethod
    def __di_form(block_num, di_num):
        """Функция формирования (заполнения) ИОКов АСН из запрашиваемых ПА и их запрос"""

        def out_single_asn(asciihex):
            for i in range(0, 2):
                sendFromJson(SCPICMD, UV["OUT_SINGLE_ASN" + str(block_num)], AsciiHex(asciihex))

        if di_num == 2:
            bprint('Запрос ДИ-2: ПА1 "РезКонтроль" и ПА2 "ГотВывод" --- АСН' + str(block_num))
            out_single_asn('0x0100 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА1
            sendFromJson(SCPICMD, UV["TLM2_ASN" + str(block_num)])                              # Запрос ДИ2 АСН
        elif di_num == 3:
            bprint('Запрос ДИ-3: ПА3 "ТлмРабота" (ИСД1…ИСД25) и ПА=22, ДН=11 "ВыводДвиж" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 031C 0000 0000'))  # Периодический запрос ПА3 с выдачей по изменению
            out_single_asn('0x7601 0000 0000 0000')                                                 # Запрос одноразовой выдачи ПА22 ДН11
            sendFromJson(SCPICMD, UV["TLM3_ASN" + str(block_num)], AsciiHex('0x0200 031C 0000 0000'))        # Запрос ДИ3 АСН
        elif di_num == 4:
            bprint('Запрос ДИ-4: ПА3 "ТлмРабота" (ИСД26…ИСД30), ПА=4 "ДаНетВвод", ПА=6 "ПриемСНП", ПА=13, ДН=4 "ТекВывод" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 031C 0000 0000'))  # Периодический запрос ПА3 с выдачей по изменению
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 041C 0000 0000'))  # Периодический запрос ПА4 с выдачей по изменению
            out_single_asn('0x0600 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА6
            out_single_asn('0x8D00 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА13 ДН4
            sendFromJson(SCPICMD, UV["TLM4_ASN" + str(block_num)])                              # Запрос ДИ4 АСН
        elif di_num == 5:
            bprint('Запрос ДИ-5: ПА=5, ДН=10 "ВыводПарам" и  ПА=12, ДН=5 "ТекРежим" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 451D 0000 0000'))  # Периодический запрос ПА5 ДН10 с выдачей по изменению  (вывод 1 раз в 10 секунд)
            out_single_asn('0xAC00 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА12 ДН5
            sendFromJson(SCPICMD, UV["TLM5_ASN" + str(block_num)])                              # Запрос ДИ5 АСН
        elif di_num == 6:
            bprint('Запрос ДИ-6: ПА=22, ДН=5 "ВыводДвиж", ПА=22, ДН=10 "ВыводДвиж", ПА=12, ДН=3 "ТекРежим" --- АСН' + str(block_num))
            out_single_asn('0xB600 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА22 ДН5
            out_single_asn('0x5601 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА22 ДН10
            out_single_asn('0x06C0 0000 0000 0000')                                             # Запрос одноразовой выдачи ПА12 ДН3
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 451D 0000 0000'))  # Периодический запрос ПА5 ДН10 с выдачей по изменению
            sendFromJson(SCPICMD, UV["TLM6_ASN" + str(block_num)])                                           # Запрос ДИ6 АСН
        elif di_num == 7:
            bprint('Запрос ДИ-7: ПА=9 "КоордПолюс", ПА=24 "ОцифрШВ", ПА=5, ДН=8 "ВыводПарам" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 0904 0000 0000'))  # Периодический запрос ПА9 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 1804 0000 0000'))  # Периодический запрос ПА24 с периодом опроса 1 раз в секунду
            out_single_asn('0x0501 0000 0000 0000')                                                 # Запрос одноразовой выдачи ПА5 ДН8
            sendFromJson(SCPICMD, UV["TLM7_ASN" + str(block_num)])                                  # Запрос ДИ7 АСН
        elif di_num == 8:
            bprint('Запрос ДИ-8: ПА=5, ДН=2 "ВыводПарам" и ПА=5, ДН=6 "ВыводПарам" --- АСН' + str(block_num))
            out_single_asn('0x4500 0000 0000 0000')                             # Запрос одноразовой выдачи ПА5 ДН2
            out_single_asn('0xC500 0000 0000 0000')                             # Запрос одноразовой выдачи П5 ДН6
            sendFromJson(SCPICMD, UV["TLM8_ASN" + str(block_num)])              # Запрос ДИ8 АСН
        elif di_num == 9:
            bprint('Запрос ДИ-9: ПА=5, ДН=7 "ВыводПарам" --- АСН' + str(block_num))
            out_single_asn('0xE500 0000 0000 0000')                             # Запрос одноразовой выдачи ПА5 ДН7
            sendFromJson(SCPICMD, UV["TLM9_ASN" + str(block_num)])              # Запрос ДИ9 АСН
        elif di_num == 10:
            bprint('Запрос ДИ-10: ПА=5, ДН=5 "ВыводПарам", ПА=12, ДН=2 "ТекРежим",  ПА=12, ДН=1 "ТекРежим" --- АСН' + str(block_num))
            out_single_asn('0xA500 0000 0000 0000')                         # Запрос одноразовой выдачи ПА5 ДН5
            out_single_asn('0x2C00 0000 0000 0000')                         # Запрос одноразовой выдачи ПА12 ДН1
            out_single_asn('0x4C00 0000 0000 0000')                         # Запрос одноразовой выдачи ПА12 ДН2
            sendFromJson(SCPICMD, UV["TLM10_ASN" + str(block_num)])         # Запрос ДИ10 АСН
        elif di_num == 11:
            bprint('Запрос ДИ-11: ПА=19, ДН=1 "КСВЧобщее" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 3304 0000 0000'))  # Периодический запрос ПА19 ДН1 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["TLM11_ASN" + str(block_num)])                  # Запрос ДИ11 АСН
        elif di_num == 12:
            bprint('Запрос ДИ-12: ПА=19, ДН=1 "КСВЧобщее" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 3304 0000 0000'))  # Периодический запрос ПА19 ДН1 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["TLM12_ASN" + str(block_num)])                  # Запрос ДИ12 АСН
        elif di_num == 13:
            bprint('Запрос ДИ-13: ПА18 "УслМгнКСВЧ" --- АСН' + str(block_num))
            sendFromJson(SCPICMD, UV["OUT_PERIOD_ASN" + str(block_num)], AsciiHex('0x0200 1204 0000 0000'))  # Периодический запрос ПА18 с периодом опроса 1 раз в секунду
            sendFromJson(SCPICMD, UV["TLM13_ASN" + str(block_num)])                  # Запрос ДИ12 АСН
        else:
            raise Exception('Некорректный номер ДИ')
        return

    @staticmethod
    @print_start_and_end(string='АСН: ПРОВЕРКА РЕЗУЛЬТАТОВ САМОКОНТРОЛЯ АСН')
    def res_control(block_num):
        """Проверка результатов самоконтроля АСН"""
        ASN.__validate_block_num(block_num)
        syst_num = ASN.__get_syst_num(block_num)
        SS = ad_dict_SS(syst_num)
        DI_2 = ad_dict_DI_2(syst_num)
        DI_3 = ad_dict_DI_3(syst_num)
        DI_4 = ad_dict_DI_4(syst_num)
        DI_10 = ad_dict_DI_10(syst_num)
        control_result = Ex.get('ТМИ', SS["ResControl"], 'КАЛИБР ТЕКУЩ')
        failure_flag = Ex.get('ТМИ', SS["FailureFlag"], 'КАЛИБР ТЕКУЩ')
        state_ASN = Ex.get('ТМИ', SS["PrgStateSvUS"], 'КАЛИБР ТЕКУЩ')
        state_PN = Ex.get('ТМИ', SS["PrgStateSvPN"], 'КАЛИБР ТЕКУЩ')
        if control_result == 'АСН исправна' and failure_flag == "сбои не зафиксированы":
            # Достаточно считать 5 основных параметров самоконтроля и режимов работы УС и ПН
            tprint(forma % ('Суммарный результат контроля АСН', Text.green + 'АСН исправна, сбои не зафиксированы') + Text.default)
            keys = list(SS.keys())  # список шифров
            for cypher in keys[0:5]:
                tprint(forma % (cypher, Ex.get('ТМИ', SS[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
        elif control_result == 'АСН неисправна':
            # 	Неисправным называется такое состояние аппаратной части, при котором АСН в состоянии выполнять
            #   основные функции, но с некоторым ухудшением требуемых характеристик
            bprint("Суммарный результат контроля АСН: %s" % control_result)
            tprint("Наличие сбоев в процессе тестирования: %s" % failure_flag)
            tprint("Программное состояние АСН (СВ УС): %s" % state_ASN)
            tprint("Программное состояние АСН (СВ ПН): %s" % state_PN)
            BCK.clc_BCK()
            ASN.__di_form(block_num, 2)  # Запрос ДИ2 АСН
            ASN.__di_form(block_num, 3)  # Запрос ДИ3 АСН
            sleep(20)
            BCK.downBCK()
            for cypher in tuple(DI_2.keys())[0:-20]:  # Вывод расширенных результатов самоконтроля АСН (96 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_2[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_3.keys())[0:-3]:  # Описание сбоев АСН (43 параметра)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_3[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_4.keys())[0:8]:  # Описание сбоев АСН. Продолжение (8 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_4[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
        elif control_result == 'отказ-ПН':
            bprint('Произошел отказ ПН. АСН может использоваться только как источник МВ, управляемой по УВ')
            for cypher in tuple(DI_2.keys())[5:9] + tuple(DI_2.keys())[31:-20]:
                # Вывод расширенных результатов самоконтроля АСН (96 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_2[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_3.keys())[0:-3]:                 # Описание сбоев АСН (43 параметра)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_3[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_4.keys())[0:8]:                  # Описание сбоев АСН. Продолжение (8 параметров)
                tprint(forma % (cypher, Ex.get('ТМИ', DI_4[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            AN_mode = Ex.get('ТМИ', DI_10["ASN_Mode"], 'НЕКАЛИБР ТЕКУЩ')
            print('АСН в режиме "Автономная навигация"' if AN_mode == 101 else
                  'АСН не переведена в режим "Автономная навигация"\nТекущий режим работы АСН: ' + AN_mode)
        else:
            bprint('Произошел отказ АСН (критическое нарушение в УС)', tab=1)
            for cypher in tuple(DI_2.keys())[9:31]:
                tprint(forma % (cypher, Ex.get('ТМИ', DI_2[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_3.keys())[0:-3]:
                tprint(forma % (cypher, Ex.get('ТМИ', DI_3[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
            for cypher in tuple(DI_4.keys())[0:8]:
                tprint(forma % (cypher, Ex.get('ТМИ', DI_4[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)

    @staticmethod
    @print_start_and_end(string='АСН: ПРОВЕРКА ПРИЗНАКА ДОСТОВЕРНОСТИ КСВЧ-РЕШЕНИЯ')
    def __KSVCH_check(syst_num):
        """Функция проверки достоверности КСВЧ-решения"""
        DI_7 = ad_dict_DI_7(syst_num)
        DI_13 = ad_dict_DI_13(syst_num)
        Valid_KSVCh = Ex.get('ТМИ', DI_13["ValidKSVCh"], 'КАЛИБР ТЕКУЩ')
        bprint('Достоверность координатно-скоростного решения: %s' % Valid_KSVCh)
        for cypher in tuple(DI_7.keys())[15:19]:
            tprint(forma % (cypher, Ex.get('ТМИ', DI_7[cypher], 'КАЛИБР ТЕКУЩ')), tab=1)
        controlGet(Valid_KSVCh, 'решение достоверно')

    @staticmethod
    @print_start_and_end(string='АСН: ПРОВЕРКА ВЫДАЧИ СМ В БЦК %s')
    def check_sm_output(block_num):
        """Функция проверки корректной выдачи СМ из АСН"""
        ASN.__validate_block_num(block_num)
        syst_num = ASN.__get_syst_num(block_num)
        ASN.__KSVCH_check(syst_num)
        DI_7 = ad_dict_DI_7(syst_num)
        confirm_MV = Ex.get('ТМИ', DI_7["ConfirmMV"], 'КАЛИБР ТЕКУЩ')
        bprint('Подтверждение выдачи импульса МВ: ' + confirm_MV)
        controlGet(confirm_MV, 'импульс МВ выведен',
                   text=('', 'Проверьте, что на Имитаторе К2-100 запущен сценарий имитации!'))


##################### IMITATORS ##############################
class Imitators:
    @staticmethod
    @print_start_and_end(string='ЗД ИМИТАТОР ВКЛ')
    def on_imitators_ZD():
        Ex.send('Ячейка ПИ', ICCELL('ВыходЗД', out=0x0F))  # Включение имитаторов ЗД
        sleep(3)

    @staticmethod
    @print_start_and_end(string='ЗД ИМИТАТОР ОТКЛ')
    def off_imitators_ZD():
        Ex.send('Ячейка ПИ', ICCELL('ВыходЗД', out=0x00))  # Имитаторы ЗД отключены

    @staticmethod
    @print_start_and_end(string='ДС ИМИТАТОР ВКЛ')
    def on_imitators_DS():
        Ex.send('Ячейка ПИ', ICCELL('ВыходДС', out=0xFF))  # Включение имитаторов ДС
        sleep(3)

    @staticmethod
    @print_start_and_end(string='ДС ИМИТАТОР ОТКЛ')
    def on_imitators_DS():
        Ex.send('Ячейка ПИ', ICCELL('ВыходДС', out=0x00))  # Включение имитаторов ДС


##################### BSK-P ##############################
class BSK_P:
    @staticmethod
    def on():
        pass
    @staticmethod
    def off():
        pass
    @staticmethod
    def foo():
        pass


##################### BSK-Ku ##############################
class BSK_KU:
    @staticmethod
    def on():
        pass
    @staticmethod
    def off():
        pass
    @staticmethod
    def foo():
        pass


##################### BSPA ##############################
class BSPA:
    @staticmethod
    def on():
        pass
    @staticmethod
    def off():
        pass
    @staticmethod
    def foo():
        pass


##################### KSO ##############################
# TODO: включить КИС
#  включить КСО
#  отключить КИС
#  чтобы КСО набрал измерения
#  включить КИС
#  сбросить БЦК
#  посмотреть тми
#
class KSO:
    cur = None
    _tmi = config.odict(('00.01.PPS1', []), ('00.01.PPS2', []),
                        ('00.02.Sat_Bx', []), ('00.02.Sat_By', []), ('00.02.Sat_Bz', []),
                        ('00.02.Sat_Bx_2', []), ('00.02.Sat_By_2', []), ('00.02.Sat_Bz_2', []),
                        ('00.01.FT1_FD1', []), ('00.01.FT1_FD2', []), ('00.01.FT1_FD3', []), ('00.01.FT1_FD4', []),
                        ('00.01.FT2_FD1', []), ('00.01.FT2_FD2', []), ('00.01.FT2_FD3', []), ('00.01.FT2_FD4', []),
                        ('00.05.BIUS1MeasX', []), ('00.05.BIUS1MeasY', []), ('00.05.BIUS1MeasZ', []),
                        ('00.05.BIUS2MeasX', []), ('00.05.BIUS2MeasY', []), ('00.05.BIUS2MeasZ', []),
                        ("00.08.Q_ST1_0", [],), ("00.08.Q_ST1_1", [],), ("00.08.Q_ST1_2", [],), ("00.08.Q_ST1_3", [],),
                        ("00.08.Q_ST2_0", [],), ("00.08.Q_ST2_1", [],), ("00.08.Q_ST2_2", [],), ("00.08.Q_ST2_3", [],),
                        ("00.08.Q_ST3_0", [],), ("00.08.Q_ST3_1", [],), ("00.08.Q_ST3_2", [],), ("00.08.Q_ST3_3", [],),
                        ("00.08.Q_ST4_0", [],), ("00.08.Q_ST4_1", [],), ("00.08.Q_ST4_2", [],), ("00.08.Q_ST4_3", [],))
    quaternions = {
        1: (round(0.497978, 2), round(-0.599586, 2), round(-0.419021, 2), round(-0.465764, 2)),
        2: (round(0.526215, 2), round(-0.625533, 2), round(-0.380668, 2), round(-0.432317, 2)),
        3: (round(0.528514, 2), round(-0.625921, 2), round(-0.373003, 2), round(-0.43562, 2)),
        4: (round(0.666464, 2), round(-0.722384, 2), round(-0.072327, 2), round(-0.169576, 2)),
    }
    # TODO: сделать функции условий для каждого шифра
    #  в из нормал прогонять по условию последнее значение и печатаь
    #  в гет тми просто печатать

    @staticmethod
    @print_start_and_end(string='Включить КСО')
    def on():
        if KSO.cur is True:
            raise Exception("КСО включен")
        sendFromJson(SCPICMD, 0xE114, AsciiHex('0x4400 0000 0000 0000'), describe='Отключить ЦНФ')    # Отключить ЦНФ
        sendFromJson(SCPICMD, 0xE004, AsciiHex('0x0209 0000 0000 0000'))    # Включить КСО + обмен
        bprint(':::Ждем 60 сек 00.01.ARO == 15200 ')
        if not Ex.wait('ТМИ', '{00.01.ARO.НЕКАЛИБР} == 15200', 60):                  # ждем КСО включился
            rprint('00.01.ARO == 15200')
            inputG('00.01.ARO не == 15200')
        else:
            gprint('00.01.ARO == 15200')
        sendFromJson(SCPICMD, 0x0082, AsciiHex('0x0100 0000'), describe='Фейк мод', pause=10)  # Фейк мод
        executeTMI("{00.01.fakeAocsMode}@H == 1")    # Ex.wait('ТМИ', '{00.01.fakeAocsMode} == 1', 10)
        sendFromJson(SCPICMD, 0x0064, AsciiHex('0x0300 0000'), describe='Перейти 2ЗКТ', pasuse=10)  # перейти в 2ЗКТ для ЗД
        executeTMI("{00.01.mode}@H == 1 and {00.01.submode}@H == 31")   # Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10)
        KSO.cur = True
        # TODO: проверить какой КСО включн
        # if executeTMI("{05.01.beKSOA2}@H==1")[0]:   # == 1 Состояние коммутатора КСО Коммутатор А Ключевой элемент 2
        #     BCK.clc_BCK()
        #     BCK.downBCK()
        #     executeTMI(' and '.join(("{05.02.VKSOA}@H>100",     # Напряжение канала коммутатора КСО Коммутатор А Ключевой элемент 1
        #                              "{05.02.CKSOA}@H>3",       # Ток коммутатора КСО Коммутатор А Ключевой элемент 2
        #                              "{00.01.ARO}@H>1")))       # Счётчик реконфигурации
        #     KSO.isOn = True
        # else:
        #     rprint("КСО КСО НЕ ЗАМКНУТ")
        #     inputG()

        # первичный опрос ТМИ
        prevLength = len(KSO._tmi)
        KSO._get_tmi()    # опросить ТМИ
        if prevLength != len(KSO._tmi):
            raise Exception("Ошибка KSO._tmi")
        KSO._printTmi(KSO._tmi)

    @staticmethod
    @print_start_and_end(string='Отключить КСО')
    def off():
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0001 0000'))  # Установка статусов отказа для устройств БИУС1
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0101 0000'))  # БИУС2
        sendFromJson(SCPICMD, 0x006E, AsciiHex('0x8100 0000'))  # Установка режима управления ДМ
        sendFromJson(SCPICMD, 0x0071)  # Остановка всех ДМ
        sleep(10)   # пауза на остановку ДМ
        BCK.clc_BCK()
        BCK.downBCK()
        bprint('Ждем остановки ДМ 60 сек')
        if not Ex.wait('{00.02.MeasuredSpeed1.НЕКАЛИБР} < 10 and {00.02.MeasuredSpeed2.НЕКАЛИБР} < 10 and '
                       '{00.02.MeasuredSpeed3.НЕКАЛИБР} < 10 and {00.02.MeasuredSpeed4.НЕКАЛИБР} < 10', 60):
            rprint('ДМ не остановлен')
            inputG('ДМ не остановлен')
        else:
            gprint('ДМ остновлен')
        # executeTMI(' and '.join(("{00.02.MeasuredSpeed1}@H<10",  # Измеренная скорость ДМ1
        #                          "{00.02.MeasuredSpeed2}@H<10",  # Измеренная скорость ДМ2
        #                          "{00.02.MeasuredSpeed3}@H<10",  # Измеренная скорость ДМ3
        #                          "{00.02.MeasuredSpeed4}@H<10")))  # Измеренная скорость ДМ4
        sendFromJson(SCPICMD, 0x53F1)  # Отключить КСО
        KSO.cur = None
        for key in KSO._tmi.keys():
            KSO._tmi[key] = []
        # TODO: этот параметр нужно сбрасывать БЦК?
        BCK.clc_BCK()
        BCK.downBCK()
        if executeTMI("{05.01.beKSOA2}@H==0")[0]:   # == 1 Состояние коммутатора КСО Коммутатор А Ключевой элемент 2
            executeTMI(' and '.join(("{05.02.VKSOA}@H<10",      # Напряжение канала коммутатора КСО Коммутатор А Ключевой элемент 1
                                     "{05.02.CKSOA}@H<4")))     # Ток коммутатора КСО Коммутатор А Ключевой элемент 2
            sendFromJson(SCPICMD, 0x53ED)  # Остановка БИУС1
            sendFromJson(SCPICMD, 0x53EE)  # Остановка БИУС1
            sendFromJson(SCPICMD, 0x53E9)  # Остановка ММ
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0000 0000'))  # Остановка ЗД1
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0100 0000'))  # Остановка ЗД2
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0200 0000'))  # Остановка ЗД3
            sendFromJson(SCPICMD, 0x0033, AsciiHex('0x0300 0000'))  # Остановка ЗД4
            sendFromJson(SCPICMD, 0x5401)  # Остановка ДМ1
            sendFromJson(SCPICMD, 0x5402)  # Остановка ДМ2
            sendFromJson(SCPICMD, 0x5403)  # Остановка ДМ3
            sendFromJson(SCPICMD, 0x5404)  # Остановка ДМ4
        else:
            rprint("КСО КСО ЗАМКНУТ")
            inputG()

    @staticmethod
    def _get_tmi():
        # if KSO.cur is None:
        #     raise Exception("КСО должен быть включен")

        # проверить секундную от АСН, что меняется в КСО счетчи
        res, values = executeTMI(doEquation('00.01.PPS1', '@H', ref_val='@unsame') + " or " +
                   doEquation('00.01.PPS2', '@Y', ref_val='@unsame'), count=2, period=8)
        if res:
            print('Есть связь с АСН')



        # Сброс БЦК чтобы опросить занчения БИУС
        BCK.clc_BCK()
        BCK.downBCK()
        # sleep(8)


        # Опрос ММ1, 2ДС, 2БИУС
        tmi = Ex.get('ТМИ', {"00.02.Sat_Bx": 'КАЛИБР',
                             "00.02.Sat_By": 'КАЛИБР',
                             "00.02.Sat_Bz": 'КАЛИБР',
                             "00.01.FT1_FD1": 'НЕКАЛИБР',
                             "00.01.FT1_FD2": 'НЕКАЛИБР',
                             "00.01.FT1_FD3": 'НЕКАЛИБР',
                             "00.01.FT1_FD4": 'НЕКАЛИБР',
                             "00.01.FT2_FD1": 'НЕКАЛИБР',
                             "00.01.FT2_FD2": 'НЕКАЛИБР',
                             "00.01.FT2_FD3": 'НЕКАЛИБР',
                             "00.01.FT2_FD4": 'НЕКАЛИБР',
                             "00.05.BIUS1MeasX": 'КАЛИБР',
                             "00.05.BIUS1MeasY": 'КАЛИБР',
                             "00.05.BIUS1MeasZ": 'КАЛИБР',
                             "00.05.BIUS2MeasX": 'КАЛИБР',
                             "00.05.BIUS2MeasY": 'КАЛИБР',
                             "00.05.BIUS2MeasZ": 'КАЛИБР'}, None)

        # переключить ММ, опросить, добавить доп значения в словарь
        # TODO: поставить неисправность 0x0084 с Asciihex
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0201 0000'), pause=10)  # Отказ ММ1
        # sendFromJson(SCPICMD, 0x002A, AsciiHex('0x0200 0000'), pause=10)  # Включить ММ2
        sleep(10)   # пауза на переключение
        mm2 = Ex.get('ТМИ', {"00.02.Sat_Bx": 'КАЛИБР',
                             "00.02.Sat_By": 'КАЛИБР',
                             "00.02.Sat_Bz": 'КАЛИБР'}, None)
        for item in mm2.items():
            tmi[item[0] + '_2'] = item[1]
        # sendFromJson(SCPICMD, 0x002A, AsciiHex('0x0100 0000'))  # Включить ММ1
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0200 0000'), pause=1)  # Сброс отказ ММ1
        sendFromJson(SCPICMD, 0x0083, AsciiHex('0x0301 0000'), pause=1)  # отказ ММ2


        # Звездники работают только в режиме 0x0065(0x1F00 0000)- подрежим ориентации (штатая ориентация)

        if not Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10):
            sendFromJson(SCPICMD, 0x0065, AsciiHex('0x1F00 0000'))  # задать штатный режим ориентации
            Ex.wait('ТМИ', '{00.01.mode.НЕКАЛИБР} == 3 and {00.01.submode.НЕКАЛИБР} == 31', 10)
        zd = {}
        # TODO: OrientReady_ST включаить АСН, задать ориент

        for x in range(0, 4):
            zd['00.08.Q_ST%s_0' % (x + 1)] = 'КАЛИБР'
            zd['00.08.Q_ST%s_1' % (x + 1)] = 'КАЛИБР'
            zd['00.08.Q_ST%s_2' % (x + 1)] = 'КАЛИБР'
            zd['00.08.Q_ST%s_3' % (x + 1)] = 'КАЛИБР'
            # zd['00.08.OrientReady_ST%s' % (x + 1)] = 'НЕКАЛИБР'
        zd = Ex.get('ТМИ', zd, None)
        for item in zd.items():
            tmi[item[0]] = round(item[1], 2)
        # проверить кватернионы
        # <= tmi['{00.08.Q_ST1_0}'] <=

        # оринетация 91
        #
        # 0x0084 (0x0D00 0000) - сброс ошибок

        # пров ориентации
        # 'orient_ready': lambda x: executeTMI(doEquation('00.08.OrientReady_ST%s' % x, '@H', 'yes'), count=1, pause=8),
        # bprint('Проверка построения ориентации ЗД %s' % num)
        # result, values = ZD.uv_di['orient_ready'](num)
        # bprint('Опрос кватернионов ЗД %s' % num)
        # ZD.uv_di['zd_orient'](num, ZD.quaternions[num])
        # 'zd_orient': lambda x, vals: executeTMI(
        #     doEquation('00.08.Q_ST%s_0' % x, '@H', 'orient', ref_val=vals[0]) + ' and ' +
        #     doEquation('00.08.Q_ST%s_1' % x, '@H', 'orient', ref_val=vals[1]) + ' and ' +
        #     doEquation('00.08.Q_ST%s_2' % x, '@H', 'orient', ref_val=vals[2]) + ' and ' +
        #     doEquation('00.08.Q_ST%s_3' % x, '@H', 'orient', ref_val=vals[3]), count=1, pause=8)

        # заменяем значения
        for item in tmi.items():
            # KSO._tmi[item[0]] = item[1]
            KSO._tmi[item[0]].append(item[1])

    @staticmethod
    def get_tmi():
        """Получить тми и вывод"""
        KSO._get_tmi()  # опросить ТМИ
        KSO._printTmi(KSO._tmi)

    @staticmethod
    def _printTmi(tmi, twoVals=False):
        """Вывод словаря тми, или сопоставить два одинаковых словаря"""
        ar = []
        for item in tmi.items():
            if twoVals is True:
                columns = item[1][-2]
            else:
                columns = item[1]
            for index, x in enumerate(columns):
                if not isinstance(x, str):
                    columns[index] = str(x)
            ar.append([item[0] + ':', *columns])
        string = tabulate(ar, tablefmt='simple')
        print(string.strip('- \n'))

    @staticmethod
    def is_normal():
        # опросить ДМ раскручены
        # ЗД включены, и есть кватернионы по имитаторам
        # ММ значения, и что не сильно прыгают по сравнению с предыдущим запросом
        # ДС - засвечены и включены имитаторы
        # БИУС - значения
        pass


##################### DUK ##############################
class DUK:
    @staticmethod
    def on():
        pass
    @staticmethod
    def off():
        pass
    @staticmethod
    def foo():
        pass