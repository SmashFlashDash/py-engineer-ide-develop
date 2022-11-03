from engineers_src.Devices.Device import Device
from engineers_src.Devices.functions import print_start_and_end, sendFromJson, executeTMI, doEquation
from engineers_src.tools.ivk_script_tools import *
from engineers_src.tools.tools import SCPICMD, AsciiHex, KPA, SOTC, SKPA, Ex, sleep


# TODO: если будет ошибка, то можно использовать мощн -- ++ и брать ДИ на уст ур КПА
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

    @classmethod
    @print_start_and_end(string='КИС: включить')
    def on(cls, num):
        """перевод БАРЛ в СР
        :param num: номер БАРЛ
        :return: None"""
        if cls.cur is not None:
            raise Exception('КИС-%s уже включен!' % cls.cur)
        elif not 0 < num < 5:
            raise Exception('КИС имеет комплекты 1 2 3 4!')
        cls.cur = num
        cls.__run_cmd('DR ' + cls.cyphs[num])   # команды включения

    @classmethod
    @print_start_and_end(string='КИС: отключить')
    def off(cls):
        """ перевод БАРЛ в ДР
        :return: None"""
        cls.__run_cmd('standby')
        cls.cur = None

    @classmethod
    def get_tmi(cls):
        """проверка запущенного БАРЛ, мкпд и уровня приема БАРЛ """
        if cls.cur is None:
            raise Exception("Для провеки СР нужно включить БАРЛ")
        bprint('Проверка: обмена по мкпд, номера активного БАРЛ, уровня сигнала БАРЛ')
        cypher = cls.cyphs[cls.cur]
        executeTMI(' and '.join((doEquation('15.00.MKPD%s' % cypher, '@H', ref_val=1),
                                 doEquation('15.00.NBARL', '@H', ref_val=cls.cur - 1),
                                 doEquation('15.00.UPRM%s' % cypher, '@H', ref_val='[80,255]'))), count=1)

    @classmethod
    def get_tmi_conn_test(cls):
        cls.get_tmi()
        cls.conn_test(5)

    @classmethod
    def print_BARL_levels(cls):
        yprint('УРОВНИ БАРЛ:')
        yprint('\n'.join(['\tБАРЛ %s: %s' % (cls.cyphs[num], cls.levels_kpa[num]) for num in range(1, 5)]))

    @classmethod
    def sensitive_prm(cls, n_cmd):
        """Поиск минимального уровня мощности КПА КИС, чтобы проходили команды на БАРЛ
        :param n_cmd: кол-во раз сколько будет выдана комманда"""
        # Установим минимальную мощность КПА и долбим команды пока не пройдут все
        if cls.cur is None:
            raise Exception("Замер чувствит ПРМ производится при включенном БАРЛ")
        cypher = cls.cyphs[cls.cur]
        yprint('КИС замер чувствительности БАРЛ %s' % cypher, tab=1)
        power_count = 0
        powers_tx = [x * 1.0 for x in tuple(range(-60, -85, -2)) + tuple(range(-85, -110, -2))]  # значения мощности КПА
        # -60 -62 ... -84 -85 -87 ... -109
        run_setting = True
        while run_setting and power_count < len(powers_tx):
            power_transmitter = powers_tx[power_count]
            bprint('Уст Мощность КПА %s dbm...' % power_transmitter)
            Ex.send('КПА', KPA('Мощность-уст', power_transmitter))  # установить заданую мощность КПА
            cls.__valid_KPA_power(power_transmitter)
            cls.conn_test(n_cmd)
            # решение оператор установить уровень, предыдущий или продолжить настройку
            btn_name = inputGG(title='Настройка мощности КПА КИС',
                               btnsList=([('Продолжить', 'ЗАВ НАСТ ИСП ПРЕД УРОВЕНЬ')]))
            if btn_name != 'Продолжить':
                run_setting = False
            power_count += 1
        power_count -= 1
        power_count = power_count if power_count in (
        0, len(powers_tx) - 1) else power_count - 1  # крайние индексы не менять
        bprint('Настроенный уровень сигнала КПА: %s dbm' % powers_tx[power_count])
        # добавить в словарь урвоень сигнала
        cls.levels_kpa[cls.cur] = powers_tx[power_count]
        Ex.send('КПА', KPA('Мощность-уст', cls.levels_kpa[cls.cur]))

    @classmethod
    def conn_test(cls, n_cmd):
        """Проверка прохождения команд
        :param n_cmd: кол-во раз сколько будет выданы комманды"""
        bprint('Проверка прохождения %s комманд...' % n_cmd * 2)
        result = []
        for cmd_count in range(0, n_cmd):
            cls.__run_cmd('uncog')
            result.append(executeTMI('{15.00.NRK%s}@H == %s' % (cls.cyphs[cls.cur], cls.cmds['uncog'][0][1]),
                                     pause=8, count=1, stopFalse=False)[0])
            cls.__run_cmd('fx')
            result.append(executeTMI('{15.00.NRK%s}@H == %s' % (cls.cyphs[cls.cur], cls.cmds['fx'][0][1]),
                                     pause=8, count=1, stopFalse=False)[0])
        errors_count = result.count(False)
        comm_print('Ошибок приема %s из %s' % (errors_count, 2 * n_cmd))
        return errors_count

    # TODO: как использовать
    @classmethod
    @print_start_and_end(string='КИС: установить измеренный урвоень мощности КПА')
    def set_KPA_level(cls):
        """Установить найденный ранее уровень мощности КПА КИС для текущего БАРЛ"""
        if cls.cur is None:
            raise Exception("Чобы установить уровень КПА необходимо включить БАРЛ")
        power = cls.levels_kpa[cls.cur]
        if power is None:
            rprint('Не измерен уровень передатчика КПА для текущего БАРЛ')
            return
        bprint("Устаовить уровень мощности прд КПА...")
        Ex.send('КПА', KPA('Мощность-уст', power))  # установить заданую мощность КПА
        cls.__valid_KPA_power(power)

    # TODO: проверить
    @classmethod
    def __valid_KPA_power(cls, ref_power):
        if not Ex.wait('КПА', '%s < {ДИ_КПА.мощн_ПРД} < %s' % (ref_power-0.1, ref_power+0.1), 10):
            rprint("Не удалось установить Мощность КПА %s" % ref_power)
            inputG("Не удалось установить Мощность КПА %s" % ref_power)
        else:
            gprint("Мощность КПА устаовлена")
        # sleep(1)
        # PowKpa = Ex.get('КПА', 'ДИ_КПА', 'мощн_ПРД')
        # if PowKpa is not None and ref_power - 0.1 <= PowKpa <= ref_power + 0.1:
        #     gprint('Мощность КПА: %s' % PowKpa)
        #     return True
        # else:
        #     rprint('Мощность КПА: %s' % PowKpa)
        #     inputG("Проверь Мощность КПА")
        #     return False

    @classmethod
    def __run_cmd(cls, key):
        for cmd in cls.cmds[key]:
            if isinstance(cmd, int):
                sleep(cmd)
            elif isinstance(cmd, tuple):
                sendFromJson(*cmd)


