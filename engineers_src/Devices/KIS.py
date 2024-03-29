from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation, executeWaitTMI
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


class KIS(Device):
    cur = None
    cyphs = {1: '1/2', 2: '2/2', 3: '3/4', 4: '4/4'}
    levels_kpa = {1: None, 2: None, 3: None, 4: None, }
    cmds = {
        'DR 1/2': ((SOTC, 1), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'DR 2/2': ((SOTC, 2), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'DR 3/4': ((SOTC, 3), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'DR 4/4': ((SOTC, 4), 5, (SKPA, 'Скорость-16'), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 87), 5, (SOTC, 155), 1),
        'standby': ((SOTC, 73),),
        'continue': ((SOTC, 95),),
        'uncog': ((SOTC, 41),),
        'fx': ((SOTC, 87),)
    }
    kpa_powers = [x * 1.0 for x in tuple(range(-60, -85, -2)) + tuple(range(-85, -110, -2))]  # значения мощности КПА

    @classmethod
    @print_start_and_end(string='КИС: включить')
    def on(cls, num, ask_TMI=True):
        """перевод БАРЛ в СР
        :param num: номер БАРЛ
        :param ask_TMI: проверить ДИ
        :return: None"""
        cls.log('Включить', num)
        if cls.cur is not None:
            raise Exception('КИС-%s уже включен!' % cls.cur)
        elif not 0 < num < 5:
            raise Exception('КИС имеет комплекты 1 2 3 4!')
        cls.cur = num
        cls.__run_cmd('DR ' + cls.cyphs[num])
        if ask_TMI:
            pass

    @classmethod
    @print_start_and_end(string='КИС: отключить')
    def off(cls, ask_TMI=True):
        """ перевод БАРЛ в ДР
        :return: None"""
        cls.log('Отключить')
        cls.__run_cmd('standby')
        cls.cur = None
        if ask_TMI:
            pass

    @classmethod
    def get_tmi(cls):
        """проверка запущенного БАРЛ, мкпд и уровня приема БАРЛ """
        if cls.cur is None:
            raise Exception("Для провеки СР нужно включить БАРЛ")
        bprint('Проверка: обмена по мкпд, номера активного БАРЛ, уровня сигнала БАРЛ')
        cypher = cls.cyphs[cls.cur]
        nrk_cypher = '1/2' if cls.cur in [0, 1] else '3/4'
        executeTMI('{15.00.MKPD%s}@H==1 and ' % nrk_cypher +
                   '{15.00.NBARL}@H==%s and' % (cls.cur - 1) +
                   '{15.00.UPRM%s}@H==[80,255]' % nrk_cypher, count=1)

    @classmethod
    @print_start_and_end(string='КИС: тест соединения')
    def get_tmi_conn_test(cls, num):
        cls.get_tmi()
        cls.__conn_test(num)

    @classmethod
    @print_start_and_end(string='КИС: настроенные уровни КПА КИС')
    def print_BARL_levels(cls):
        yprint('УРОВНИ БАРЛ:')
        yprint('\n'.join(['\tБАРЛ %s: %s' % (cls.cyphs[num], cls.levels_kpa[num]) for num in range(1, 5)]))

    @classmethod
    @print_start_and_end(string='КИС: настройка ПРД КПА')
    def sensitive_prm(cls, n_cmd):
        """Поиск минимального уровня мощности КПА КИС, чтобы проходили команды на БАРЛ
        :param n_cmd: кол-во раз сколько будет выдана комманда"""
        # Установим минимальную мощность КПА и долбим команды пока не пройдут все
        if cls.cur is None:
            raise Exception("Замер чувствит ПРМ производится при включенном БАРЛ")
        cypher = cls.cyphs[cls.cur]
        yprint('КИС замер чувствительности БАРЛ %s' % cypher, tab=1)
        powers_tx = cls.kpa_powers  # -60 -62 ... -84 -85 -87 ... -109 значения мощности КПА
        for index, power in enumerate(powers_tx):
            cls.__set_KPA_power(power)
            cls.__conn_test(n_cmd)
            # решение оператор установить уровень, предыдущий или продолжить настройку
            btn_name = inputGG(title='Настройка мощности КПА КИС',
                               btnsList=([('Продолжить', 'ЗАВ НАСТ ИСП ПРЕД УРОВЕНЬ')]))
            if btn_name != 'Продолжить':
                index = index if index == 0 else index - 1  # перейти на предыдущий уровень
                break
        bprint('Настроенный уровень сигнала КПА: %s dbm' % powers_tx[index])
        # добавить в словарь урвоень сигнала
        cls.levels_kpa[cls.cur] = powers_tx[index]
        Ex.send('КПА', KPA('Мощность-уст', cls.levels_kpa[cls.cur]))

    @classmethod
    @print_start_and_end(string='КИС: настройка бинарным поиском ПРД КПА')
    def sensitive_prm_bin(cls, n_cmd):
        """Предварительно определяет диапазон для настройки КПА"""
        if cls.cur is None:
            raise Exception("Замер чувствит ПРМ производится при включенном БАРЛ")
        powers_tx = cls.kpa_powers
        mid = len(powers_tx) // 2
        low = 0
        high = len(powers_tx) - 1
        values = []
        value = None
        while low <= high:
            values.append(powers_tx[mid])
            cls.__set_KPA_power(powers_tx[mid])
            errors = cls.__conn_test(n_cmd)
            # errors = 1 if powers_tx[mid] < -109.0 else 0
            if errors == 0:
                value = powers_tx[mid]
            if errors == 0:
                low = mid + 1
            else:
                high = mid - 1
            mid = (low + high) // 2
        print("Проверенные значения: %s" % values)
        if value is None:
            cls.levels_kpa[cls.cur] = powers_tx[0]
            rprint('Настроен максимальный уровень')
        else:
            cls.levels_kpa[cls.cur] = value
        gprint('Уровень определен')
        bprint('Настроенный уровень сигнала КПА: %s dbm' % cls.levels_kpa[cls.cur])

    # TODO: как использовать
    @classmethod
    @print_start_and_end(string='КИС: установить измеренный уровень мощности КПА')
    def set_KPA_level(cls):
        """Установить найденный ранее уровень мощности КПА КИС для текущего БАРЛ"""
        power = cls.levels_kpa.get(cls.cur)
        if power is None:
            raise Exception('Не измерен уровень передатчика КПА для текущего БАРЛ')
        cls.__set_KPA_power(power)        # установить заданую мощность КПА

    # TODO: сделать прин приятней
    @classmethod
    def __conn_test(cls, n_cmd):
        """Проверка прохождения команд
        :param n_cmd: кол-во раз сколько будет выданы комманды"""
        yprint('Тест прохождения %s комманд' % n_cmd)
        result = []
        nrk_cypher = '1/2' if cls.cur in [0,1] else '3/4'
        for cmd_count in range(0, n_cmd // 2):
            for x in ('uncog', 'fx'):
                cls.__run_cmd(x)
                # out = '{15.00.NRK%s.НЕКАЛИБР} == %s' % (nrk_cypher, cls.cmds[x][0][1])
                # result.append(Ex.wait('ТМИ', out, 20))
                # gprint(out) if result[-1] is True else rprint(out)
                result.append(executeWaitTMI('{15.00.NRK%s}@H == %s' % (nrk_cypher, cls.cmds[x][0][1]), 10, stopFalse=False)[0])
            print('Команд: %s/%s' % (cmd_count * 2, n_cmd))
        errors_count = result.count(False)
        comm_print('Ошибок приема %s из %s' % (errors_count, n_cmd))
        return errors_count

    @classmethod
    def __set_KPA_power(cls, ref_power):
        bprint("Устаовить уровень мощности прд КПА...")
        Ex.send('КПА', KPA('Мощность-уст', ref_power))  # установить заданую мощность КПА
        if not Ex.wait('КПА', '%s < {ДИ_КПА.мощн_ПРД} < %s' % (ref_power-0.1, ref_power+0.1), 10):
            rprint("Не удалось установить Мощность КПА %s" % ref_power)
            inputG("Не удалось установить Мощность КПА %s" % ref_power)
        else:
            gprint("Мощность КПА устаовлена")

    @classmethod
    def __run_cmd(cls, key):
        for cmd in cls.cmds[key]:
            if isinstance(cmd, int):
                sleep(cmd)
            elif isinstance(cmd, tuple):
                sendFromJson(*cmd)
