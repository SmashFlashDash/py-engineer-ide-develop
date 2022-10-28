import sys, threading, socket, ctypes, struct, time, re, functools, traceback
from datetime import datetime
from collections import OrderedDict

from cpi_framework.utils.basecpi_abc import BaseCpi
from cpi_framework.spacecrafts.omka.otc import OTC

from ivk import config as conf
from ivk.global_log import GlobalLog
from ivk.log_db import DbLog
from ivk.abstract import AbstractExchange
from ivk.scOMKA.widget_kpa import KpaWidget
from ivk.scOMKA.controll_kpa import KPA, KPAResponce, KPAResponce_TCP
from ivk.scOMKA.controll_iccell import ICCELL, ICCellResponce
from ivk.scOMKA.widget_iccell import IcCellWidget
from ivk.scOMKA.controll_scpi import SCPI, SCPIResponce
from ivk.scOMKA.widget_scpi import ScpiWidget
from ivk.scOMKA.simplifications import getSimpleCommandsCPI, getSimpleCommandsOTC

from ivk.rokot_tmi import RokotTmi, RokotWidget




class Exchange(AbstractExchange):
    # MIK CONFIG
    config = conf.odict(
        ('ka_id', 0),
        ('kpa_address', '192.168.0.2'),
        ('kpa_port', 8510),
        ('kpa_local_port_tcp', 1488),
        ('kpa_local_port_udp', 8510),
        ('kpa_reconnect_step', 100),

        ('iccell_address', '192.168.1.2'),
        ('iccell_port', 1234),
        ('iccell_reconnect_step', 100),
        ('iccell_counter', 1),

        ('localhost_send_dispathcer_port', 52801),

        ('amqp_ip', '192.168.0.3'),
        ('amqp_port', 5672),
        ('amqp_virtual_host', 'mka1'),  # or '/' for default
        ('amqp_user', 'pidor'),
        ('amqp_password', 'pidor'),

        ('amqp_rokot_queue', 'ROKOT'),
        ('amqp_rokot_queue_params', None),

        ('rokot_db_ip', '192.168.0.3'),
        ('rokot_db_port', 5432),
        ('rokot_db_name', 'rokot_ng'),
        ('rokot_db_user', 'rokot'),
        ('rokot_db_password', '@sS00n@s'),
        ('rokot_default_ka_umn', '1488'),
        ('rokot_use_log_database', False),
        ('rokot_allow_tmi_insert', False),

        ('log_to_database', True),
        ('log_db_ip', '127.0.0.1'),
        ('log_db_port', 5432),
        ('log_db_name', 'ivk_log'),
        ('log_db_user', 'postgres'),
        ('log_db_password', 'Z84h9!d'),

        ('scpi_reconnect_step', 100)
    )

    # Develop VNIIEM Вольная
    # config = conf.odict(
    #     ('ka_id', 0),
    #     ('kpa_address', '127.0.0.1'),
    #     ('kpa_port', 14471),
    #     ('kpa_local_port', 14889),
    #     ('kpa_reconnect_step', 1000),

    #     ('iccell_address', '127.0.0.1'),
    #     ('iccell_port', 14488),
    #     ('iccell_reconnect_step', 1000),
    #     ('iccell_counter', 1),

    #     ('localhost_send_dispathcer_port', 52801),

    #     ('amqp_ip', '192.168.3.87'),
    #     ('amqp_port', 5672),
    #     ('amqp_virtual_host', '505'), #505 or '/' for default
    #     ('amqp_user', 'guest'),
    #     ('amqp_password', 'guest'),

    #     ('amqp_rokot_queue', 'ROKOT'),
    #     ('amqp_rokot_queue_params', None),

    #     ('rokot_db_ip', '192.168.13.127'), #192.168.3.87 для БД на Вольной / 192.168.13.127 для БД на красных
    #     ('rokot_db_port', 5432),
    #     ('rokot_db_name', 'rokot_ng'),
    #     ('rokot_db_user', 'rokot'),
    #     ('rokot_db_password', '@sS00n@s'),
    #     ('rokot_default_ka_umn', '1488'),
    #     ('rokot_use_log_database', False),
    #     ('rokot_allow_tmi_insert', True),

    #     ('log_to_database', True),
    #     ('log_db_ip', '127.0.0.1'),
    #     ('log_db_port', 5432),
    #     ('log_db_name', 'ivk_log'),
    #     ('log_db_user', 'postgres'),
    #     ('log_db_password', '1111'), #Z84h9!d

    #     ('scpi_reconnect_step', 1000)
    # )

    stop_daemons = False
    kpa_sock = None
    kpa_udp_sock = None
    iccell_sock = None
    local_sock = None

    kpa_dock = None
    iccell_dock = None
    scpi_dock = None
    rokot_widget = None

    queues = conf.odict(
        ('КПА', {
            'destination_id': 1,
            'connected': False,
            'getSock': lambda: Exchange.kpa_sock
        }),
        ('Ячейка ПИ', {
            'destination_id': 2,
            'connected': False,
            'getSock': lambda: Exchange.iccell_sock
        })
    )

    # Добавление всех сетевых параметров источников питания
    dest_index = 3
    for k, v in SCPI.SCPI_DEVICES.items():
        config['%s_ip' % k] = v['default_ip']
        config['%s_port' % k] = v['default_port']
        queues[k] = {
            'destination_id': dest_index,
            'connected': False,
            'getSock': functools.partial(lambda device: getattr(Exchange, '%s_sock' % device), k)
        }
        dest_index += 1

    @staticmethod
    def DestToQueue(dest):
        for name, queue in Exchange.queues.items():
            if queue['destination_id'] == dest:
                return name
        return None

    @staticmethod
    def DestToSock(dest):
        for queue in Exchange.queues.values():
            if queue['destination_id'] == dest:
                return queue['getSock']()
        return None

    @staticmethod
    def IsDestConnected(dest):
        for queue in Exchange.queues.values():
            if queue['destination_id'] == dest:
                return queue['connected']
        return None

    @staticmethod
    def init():
        '''Открытие приложение, инициализация модуля обмена'''
        # Очистка redis бд данных
        conf.cleanData()
        # Сброс счетчика Ячейки ПИ
        conf.updConf("iccell_counter", 0)

        # Можно забиндить сокет только перед send или recv, при это сокет биндится на порт,
        # иначе ОС выдаст произвольный порт при первом вызове send или recv
        # потом через один сокет можно отправлять и получать
        Exchange.local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            Exchange.local_sock.bind(('localhost', conf.getConf('localhost_send_dispathcer_port')))
        except:
            # Получаем произвольный порт и сохраняем (фикс "Адрес уже используется")
            Exchange.local_sock.bind(('localhost', 0))
            conf.updConf('localhost_send_dispathcer_port', Exchange.local_sock.getsockname()[1])

        # Запускаем диспатчер отправки сообщений из pydev-процессов
        t = threading.Thread(target=Exchange.__sendDispatch, daemon=True)
        t.start()

        # Тестируем локальный порт для КПА
        kpa_test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            kpa_test_sock.bind(('0.0.0.0', conf.getConf('kpa_local_port_tcp')))
            kpa_test_sock.close()
        except:
            # Получаем произвольный порт и сохраняем (фикс "Адрес уже используется")
            kpa_test_sock.bind(('0.0.0.0', 0))
            conf.updConf('kpa_local_port_tcp', kpa_test_sock.getsockname()[1])
            kpa_test_sock.close()

        # Запускаем прослушивание КПА
        t = threading.Thread(target=lambda: Exchange.__listenTCP('kpa_sock',
                                                                 conf.getConf('kpa_address'),
                                                                 conf.getConf('kpa_port'),
                                                                 conf.getConf('kpa_local_port_tcp'),
                                                                 conf.getConf('kpa_reconnect_step'),
                                                                 'КПА',
                                                                 'КПА',
                                                                 lambda data: KPAResponce_TCP('TCP', data),
                                                                 lambda resp: Exchange.kpa_dock.kpaIncome(resp),
                                                                 None
                                                                 ),
                             daemon=True)
        t.start()
        # Запускаем прослушивание КПА по UDP
        t = threading.Thread(target=lambda: Exchange.__listenUDP('kpa_udp_sock',
                                                                 conf.getConf('kpa_address'),
                                                                 conf.getConf('kpa_local_port_udp'),
                                                                 lambda data: KPAResponce('UDP', data),
                                                                 lambda resp: Exchange.kpa_dock.kpaIncome(resp),
                                                                 None
                                                                 ),
                             daemon=True)
        t.start()

        # Запускаем прослушиваение ячейки ПИ
        t = threading.Thread(target=lambda: Exchange.__listenTCP('iccell_sock',
                                                                 conf.getConf('iccell_address'),
                                                                 conf.getConf('iccell_port'),
                                                                 None,  # local port automaticly
                                                                 conf.getConf('iccell_reconnect_step'),
                                                                 'Ячейка ПИ',
                                                                 'ячейкой ПИ',
                                                                 lambda data: ICCellResponce(data),
                                                                 lambda resp: Exchange.iccell_dock.iccellIncome(resp),
                                                                 lambda: Exchange.iccell_dock.iccellDisconnect()
                                                                 ),
                             daemon=True)
        t.start()

        # Запускаем мониторинг Ячейки ПИ (для обновление инфы в iccell_dock)
        t = threading.Thread(target=Exchange.__monitorICCELL, daemon=True)
        t.start()

        # Запускаем прослушиваение всех источников питания
        for k, v in SCPI.SCPI_DEVICES.items():
            setattr(Exchange, '%s_sock' % k, None)
            t = threading.Thread(target=functools.partial(
                lambda device: Exchange.__listenTCP('%s_sock' % device,
                                                    conf.getConf('%s_ip' % device),
                                                    conf.getConf('%s_port' % device),
                                                    None,  # local port automaticly
                                                    conf.getConf('scpi_reconnect_step'),
                                                    device,
                                                    'источником питания %s' % device,
                                                    lambda data: SCPIResponce(device, data),
                                                    lambda resp: Exchange.scpi_dock.scpiIncome(resp),
                                                    lambda: Exchange.scpi_dock.scpiDisconnect(device)
                                                    ),
                k),
                daemon=True)
            t.start()

        # Запускаем мониторинг источников питания (для обновление инфы в scpi_dock)
        t = threading.Thread(target=Exchange.__monitorSCPI, daemon=True)
        t.start()

        # Запускаем диспатчер отправки данных в источники питания
        t = threading.Thread(target=Exchange.__scpiSendQueueDispatch, daemon=True)
        t.start()

        # Инициализация ROKOT телеметрии
        RokotTmi.init({
            'amqp_ip': conf.getConf('amqp_ip'),
            'amqp_port': conf.getConf('amqp_port'),
            'amqp_virtual_host': conf.getConf('amqp_virtual_host'),  # '/' for default
            'amqp_user': conf.getConf('amqp_user'),
            'amqp_password': conf.getConf('amqp_password'),
            'amqp_queue': conf.getConf('amqp_rokot_queue'),
            'amqp_queue_params': conf.getConf('amqp_rokot_queue_params')
        })

        # Подключение к БД логов
        try:
            connected = DbLog.connectDb(raise_exceptions=True)
            if connected:
                GlobalLog.log(threading.get_ident(), 'LOG_DB', 'Подключено к PostgreSQL серверу (%s:%d)\n' % (
                    conf.getConf("log_db_ip"), conf.getConf("log_db_port")), False)
            else:
                GlobalLog.log(threading.get_ident(), 'LOG_DB', 'Логгирование в БД отключено в настройках\n', True)
        except Exception as exc:
            GlobalLog.log(threading.get_ident(), 'LOG_DB',
                          'Не удалось подключиться к PostgreSQL серверу: %s  - %s\n' % (
                              conf.getConf("log_db_ip"), repr(exc)), True)

    @staticmethod
    def onClose():
        '''Закрытие приложения'''
        Exchange.stop_daemons = True
        print("closing -> stop daemons")
        if Exchange.local_sock is not None:
            try:
                Exchange.local_sock.shutdown(socket.SHUT_RDWR)
                Exchange.local_sock.close()
            except Exception as exc:
                print("local socket close exc: %s" % str(exc))
        if Exchange.kpa_udp_sock is not None:
            try:
                Exchange.kpa_udp_sock.shutdown(socket.SHUT_RDWR)
                Exchange.kpa_udp_sock.close()
            except Exception as exc:
                print("kpa_udp_sock close exc: %s" % str(exc))
        print("closing -> local socket closed")
        for name, queue in Exchange.queues.items():
            sock = queue['getSock']()
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except Exception as exc:
                    print("queue '%s' socket close exc: %s" % (name, str(exc)))
        print("closing -> all queue sockets closed")

    @staticmethod
    def getRootCommandNodeName():
        '''Определение названия для группы комманд в панели комманд'''
        return 'МКА'

    @staticmethod
    def getRootCommandNodeDescription():
        '''Определение описания для группы комманд в панели комманд'''
        return 'Команды категории "МКА" предназначны для выдачи в КПА КПИ и РК.'

    @staticmethod
    def getModuleFilter():
        '''Определение списка модулей, которые нужно подтянуть из cpi_framework, например:
        '''
        return ['cpiomka']

    @staticmethod
    def getAdditionalCommands():
        '''Определение дополнительных комманд, которые нужно добавить в панельку:'''
        commands = []
        # Упрощенные команды отправки КПИ
        commands.extend(getSimpleCommandsCPI())
        # РК МКА
        commands.append({
            'name': 'OTC',
            'translation': 'РК',
            'import_string': 'from cpi_framework.spacecrafts.omka.otc import OTC',
            'description': 'Разовая команда МКА.\nПараметры:\n' + \
                           '  - otc(int): номер команды,\n' + \
                           '  - args(AsciiHex): агрументы команды (если предусмотрен),\n' + \
                           '  - recv(int): номер приемника (0-по умолчанию, 1 - первый, 2 - второй)',
            'example': '''#Отправка в КПА разовых команд
#РК с номером и аргументом
Ex.send('КПА', OTC(1, AsciiHex('0xEF132D00000000000000'), 0))
#РК с номером без аргумента
Ex.send('КПА', OTC(1, AsciiHex(), 1))''',
            'params': ['otc', 'args', 'recv'],
            'values': ['1', "AsciiHex('0x00000000000000000000')", '0'],
            'keyword': [False, False, False],
            'cat': Exchange.getRootCommandNodeName(),
            'queues': ['КПА']
        })
        # Упрощенные команды отправки РК
        commands.extend(getSimpleCommandsOTC())
        # Доп команды на отправку КПА
        for name, msg in KPA.MESSAGES_TO_KPA.items():
            if 'show' in msg and not msg['show']:
                continue
            send_args = "'%s', %s" % (name, msg['data']['default']) if msg['data'] else "'%s'" % name
            send_id_args = "%d, %s" % (msg['id'], msg['data']['default']) if msg['data'] else "%d" % msg['id']
            commands.append({
                'name': 'KPA',
                'import_string': 'from ivk.scOMKA.controll_kpa import KPA',
                'description': msg['description'],
                'example': "#Обычная отправка по имени\nEx.send('КПА', KPA(%s))\n#Обычная отправка по ИД\nEx.send('КПА', KPA(%s))\n#Упрощенная отправка по имени (можно и по ИД)\nSKPA(%s)" % (
                    send_args, send_id_args, send_args),
                'params': ['name', 'data'] if msg['data'] else ['name'],
                'values': ["'%s'" % name, msg['data']['default']] if msg['data'] else ["'%s'" % name],
                'keyword': [False, False] if msg['data'] else [False],
                'translation': "%s (%d)" % (name, msg['id']),
                'cat': 'КПА',
                'cat_description': 'Команды категории "КПА" позволяют отправлять в КПА различные управляюще воздействия.',
                'queues': ['КПА'],

                'simple_name': 'SKPA',
                'simple_import_string': 'from ivk.scOMKA.simplifications import SKPA'
            })
        # Доп команды на получение КПА
        commands.append({
            'name': '{GET}',
            'import_string': 'from ivk.scOMKA.controll_kpa import KPA',
            'description': 'Получить данные из определенного пакета КПА. Используется для получения данных из пакетов, поступающих на ИВК из КПА.\nПараметры:\n' + \
                           '  - msg_name(str): ИД пакета,\n' + \
                           '  - field_name(str): ИД поля внутри пакета',
            'example': "#Получение значения поля 'очередь_ЗК' из пакета 'ДИ_КПА'\nval = Ex.get('КПА', 'ДИ_КПА', 'очередь_ЗК')\n#Получение значения поля 'скорость_декод_ПРМ' из пакета 'ДИ_КПА'\nval = Ex.get('КПА', 'ДИ_КПА', 'скорость_декод_ПРМ')",
            'msg_fields': KPAResponce.GetMsgFieldsDict(),
            'translation': 'Получить данные',
            'cat': 'КПА',
            'cat_description': 'Команды категории "КПА" позволяют отправлять в КПА различные управляюще воздействия.',
            'queues': ['КПА'],
            'ex_send': False,
            'is_function': False
        })
        # Доп команды на ожидание КПА
        commands.append({
            'name': '{WAIT}',
            'import_string': 'from ivk.scOMKA.controll_kpa import KPA',
            'description': 'Ожидание значений параметров из определенного пакета КПА. Используется для ожидания наступления определенного события. Возвращает результат (событие наступило или вышло время ожидания).\nПараметры:\n' + \
                           '  - expression(str): выражение для ожидания, можно использовать любые логические конструкции Python (and, or, not, ==, >=, <=, >, <, !=), группировку скобками и имена параметров в формате {ИМЯ_ПАКЕТА.ПОЛЕ_ПАКЕТА},\n' + \
                           '  - timeout(float): максимальное время ожидания в секундах',
            'example': '''#Ожидание мощн_ПРМ > 29.1 или вход_ПРМ != 4, при том что ИД_КА == 1243,
#с таймаутом 20 сек
res = Ex.wait('КПА', '({ДИ_КПА.мощн_ПРМ} > 29.1 or {ДИ_КПА.вход_ПРМ} != 4) 
    and {ДИ_КПА.ИД_КА} == 1243', 20)
#Ожидание скорость_декод_ПРМ <= 17 и очередь_ЗК < 3, с таймаутом 11 сек
res = Ex.wait('КПА', '{ДИ_КПА.скорость_декод_ПРМ} <= 17 and {ДИ_КПА.очередь_ЗК} < 3', 11)''',
            'msg_fields': KPAResponce.GetMsgFieldsDict(),
            'default_timeout': 20,
            'translation': 'Ожидание данных',
            'cat': 'КПА',
            'cat_description': 'Команды категории "КПА" позволяют отправлять в КПА различные управляюще воздействия.',
            'queues': ['КПА'],
            'ex_send': False,
            'is_function': False
        })
        # Доп команды на отправку Ячейка ПИ
        for name, msg in ICCELL.MESSAGES_TO_ICCELL.items():
            send_args = "'%s', %s" % (name, ', '.join(
                ['%s=%s' % (p['name'], p['default']) for p in msg['params']])) if 'params' in msg else "'%s'" % name
            send_id_args = "%d, %s" % (msg['id'], ', '.join(
                ['%s=%s' % (p['name'], p['default']) for p in msg['params']])) if 'params' in msg else "%d" % msg['id']
            commands.append({
                'name': 'ICCELL',
                'import_string': 'from ivk.scOMKA.controll_iccell import ICCELL',
                'description': msg['description'],
                'example': "#Обычная отправка по имени\nEx.send('Ячейка ПИ', ICCELL(%s))\n#Обычная отправка по ИД\nEx.send('Ячейка ПИ', ICCELL(%s))\n#Упрощенная отправка по имени (можно и по ИД)\nSICCELL(%s)" % (
                    send_args, send_id_args, send_args),
                'params': ['name'] if not 'params' in msg else ['name'] + [p['name'] for p in msg['params']],
                'values': ["'%s'" % name] if not 'params' in msg else ["'%s'" % name] + [p['default'].replace('\n', '')
                                                                                         for p in msg['params']],
                'keyword': [False] if not 'params' in msg else [False] + [True for p in msg['params']],
                'translation': name,
                'cat': 'Ячейка ПИ',
                'cat_description': 'Команды категории "Ячейка ПИ" позволяют отправлять в ячейку ПИ различные управляюще воздействия.',
                'queues': ['Ячейка ПИ'],

                'simple_name': 'SICCELL',
                'simple_import_string': 'from ivk.scOMKA.simplifications import SICCELL'
            })
        # Доп команды на получение Ячейка ПИ
        commands.append({
            'name': '{GET}',
            'import_string': 'from ivk.scOMKA.controll_iccell import ICCELL',
            'description': 'Получить данные из ответа определенной команды Ячейки ПИ. Используется для получения данных из пакетов, поступающих на ИВК из Ячейки ПИ.\nПараметры:\n' + \
                           '  - msg_name(str): ИД пакета,\n' + \
                           '  - field_name(str): ИД поля внутри пакета',
            'example': "#Получение значения поля 'аварийная_кнопка' из пакета 'ЗапрСост'\nval = Ex.get('Ячейка ПИ', 'ЗапрСост', 'аварийная_кнопка')\n#Получение значения поля 'сопр_СЭП+' из пакета 'ЗапрСопрИзол'\nval = Ex.get('Ячейка ПИ', 'ЗапрСопрИзол', 'сопр_СЭП+')",
            'msg_fields': ICCellResponce.GetMsgFieldsDict(),
            'translation': 'Получить данные',
            'cat': 'Ячейка ПИ',
            'cat_description': 'Команды категории "Ячейка ПИ" позволяют отправлять в ячейку ПИ различные управляюще воздействия.',
            'queues': ['Ячейка ПИ'],
            'ex_send': False,
            'is_function': False
        })
        # Доп команды на ожидание Ячейка ПИ
        commands.append({
            'name': '{WAIT}',
            'import_string': 'from ivk.scOMKA.controll_iccell import ICCELL',
            'description': 'Ожидание значений параметров из ответа определенных команд Ячейки ПИ. Используется для ожидания наступления определенного события. Возвращает результат (событие наступило или вышло время ожидания).\nПараметры:\n' + \
                           '  - expression(str): выражение для ожидания, можно использовать любые логические конструкции Python (and, or, not, ==, >=, <=, >, <, !=), группировку скобками и имена параметров в формате {ИМЯ_ПАКЕТА.ПОЛЕ_ПАКЕТА},\n' + \
                           '  - timeout(float): максимальное время ожидания в секундах',
            'example': '''#Ожидание ЗапрСост.питание_ка == 1 или ЗапрСост.коммутация_ИГБФ29 != 0,
#при том что Импульс.импульс_1_8 == 0xFF, с таймаутом 17 сек
res = Ex.wait('Ячейка ПИ', '({ЗапрСост.питание_ка} == 1 
    or {ЗапрСост.коммутация_ИГБФ29} != 0) and {Импульс.импульс_1_8} == 0xFF', 17)
#Ожидание ВыходДС.выход_3 != 0 и ВыходММ.полярность_X2  == 1, с таймаутом 14.5 сек 
res = Ex.wait('Ячейка ПИ', '{ВыходДС.выход_3} != 0 
    and {ВыходММ.полярность_X2} == 1', 14.5)''',
            'msg_fields': ICCellResponce.GetMsgFieldsDict(),
            'default_timeout': 20,
            'translation': 'Ожидание данных',
            'cat': 'Ячейка ПИ',
            'cat_description': 'Команды категории "Ячейка ПИ" позволяют отправлять в ячейку ПИ различные управляюще воздействия.',
            'queues': ['Ячейка ПИ'],
            'ex_send': False,
            'is_function': False
        })
        # Доп команды на отправку ИСТОЧНИКИ ПИТАНИЯ SCPI
        for name, msg in SCPI.MESSAGES_TO_SCPI.items():
            send_args = "'%s', %s" % (name, ', '.join(
                ['%s=%s' % (p['name'], p['default']) for p in msg['params']])) if 'params' in msg else "'%s'" % name
            send_id_args = "%d, %s" % (msg['id'], ', '.join(
                ['%s=%s' % (p['name'], p['default']) for p in msg['params']])) if 'params' in msg else "%d" % msg['id']
            commands.append({
                'name': 'SCPI',
                'import_string': 'from ivk.scOMKA.controll_scpi import SCPI',
                'description': msg['description'],
                'example': "#Отправка по имени\nEx.send('ИГБФ1', SCPI(%s))\n#Отправка по ИД\nEx.send('ММ_Y2', SCPI(%s))" % (
                    send_args, send_id_args),
                'params': ['name'] if not 'params' in msg else ['name'] + [p['name'] for p in msg['params']],
                'values': ["'%s'" % name] if not 'params' in msg else ["'%s'" % name] + [p['default'] for p in
                                                                                         msg['params']],
                'keyword': [False] if not 'params' in msg else [False] + [True for p in msg['params']],
                'translation': name,
                'cat': 'Источники питания',
                'cat_description': 'Команды категории "Источники питания" позволяют управлять источниками питания шкафа ИВК.',
                'queues': SCPI.SCPI_DEVICES.keys()
            })
        # Доп команды на получение ИСТОЧНИКИ ПИТАНИЯ SCPI
        commands.append({
            'name': '{GET}',
            'import_string': 'from ivk.scOMKA.controll_scpi import SCPI',
            'description': 'Получить данные из ответа определенной команды источника питания. Используется для получения ответов на команды передаваемые из ИВК на источники питания.\nПараметры:\n' + \
                           '  - msg_name(str): ИД источника питания,\n' + \
                           '  - field_name(str): ИД команды',
            'example': '''#Получить состояние источника ИГБФ2
val = Ex.get('', 'ИГБФ2', 'ЗапрСост')
#Получить значение тока источника ММ_X1
val = Ex.get('', 'ММ_X1', 'ЗапрТок')
#Получить значение напряжения источника ИАБ
val = Ex.get('', 'ИАБ', 'ЗапрНапряж')''',
            'msg_fields': SCPIResponce.GetMsgFieldsDict(),
            'translation': 'Получить данные',
            'cat': 'Источники питания',
            'cat_description': 'Команды категории "Источники питания" позволяют управлять источниками питания шкафа ИВК.',
            'queues': [],
            'ex_send': False,
            'is_function': False
        })
        # Доп команды на ожидание ИСТОЧНИКИ ПИТАНИЯ SCPI
        commands.append({
            'name': '{WAIT}',
            'import_string': 'from ivk.scOMKA.controll_scpi import SCPI',
            'description': 'Ожидание значений параметров из ответа определенных команд источника питания. Используется для ожидания наступления определенного события. Возвращает результат (событие наступило или вышло время ожидания).\nПараметры:\n' + \
                           '  - expression(str): выражение для ожидания, можно использовать любые логические конструкции Python (and, or, not, ==, >=, <=, >, <, !=), группировку скобками и имена параметров в формате {ИД_ИСТОЧНИКА.ИД_КОМАНДЫ},\n' + \
                           '  - timeout(float): максимальное время ожидания в секундах',
            'example': '''#Ожидание ИГБФ5.ЗапрСост == 1 или ИГБФ9.ЗапрСост != 1,
#при том что ИАБ.ЗапрНапряж > 11.65, с таймаутом 18 сек
res = Ex.wait('', '({ИГБФ5.ЗапрСост} == 1 or {ИГБФ9.ЗапрСост} != 1)
   and {ИАБ.ЗапрНапряж} > 11.65', 28)
#Ожидание ММ_X1.ЗапрТок < 6.3 и ММ_Z2.ЗапрНапряж > 7.8, с таймаутом 24 сек
res = Ex.wait('', '{ММ_X1.ЗапрТок} < 6.3 and {ММ_Z2.ЗапрНапряж} > 7.8', 24)''',
            'msg_fields': SCPIResponce.GetMsgFieldsDict(),
            'default_timeout': 20,
            'translation': 'Ожидание данных',
            'cat': 'Источники питания',
            'cat_description': 'Команды категории "Источники питания" позволяют управлять источниками питания шкафа ИВК.',
            'queues': [],
            'ex_send': False,
            'is_function': False
        })

        commands.extend(RokotTmi.getAdditionalCommands())

        return commands

    @staticmethod
    def getCpiFrameworkDestinations():
        '''Определение списка пунктов назначения для команд из cpi_framework, например:
        return ['ТКС', 'УЦО1', 'УЦО2']
        '''
        return ['КПА']

    @staticmethod
    def initDocks(parent, tabs_widget):
        '''Инициализация док-виджетов, возвращает массив с виджетами'''
        Exchange.kpa_dock = KpaWidget(parent, tabs_widget)
        Exchange.iccell_dock = IcCellWidget(parent, tabs_widget)
        Exchange.rokot_widget = RokotWidget(parent, tabs_widget)
        Exchange.scpi_dock = ScpiWidget(parent, tabs_widget)
        return [Exchange.kpa_dock, Exchange.iccell_dock, Exchange.scpi_dock, Exchange.rokot_widget]

    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def send(queue_label, data):
        '''Отправка комманды по назначению, параметры:
        queue_label - пункт назначения
        data - данные для отправки
        '''
        if queue_label not in Exchange.queues:
            raise Exception('Неверный пункт назначения "%s"' % queue_label)

        HEX = conf.getData('HEX')
        PRINT = conf.getData('PRINT')

        local_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        kpa_adress = (conf.getConf('kpa_address'), conf.getConf('kpa_port'))  # 192.168.0.2 8510
        try:
            local_sock.connect(('localhost', conf.getConf('localhost_send_dispathcer_port')))
        except Exception as exc:
            raise Exception(
                'Не удалось установить соединение с локальным сервером передачи сообщений: "%s"' % repr(exc))

        dest = struct.pack('>B', Exchange.queues[queue_label]['destination_id'])

        if queue_label == 'КПА':
            if isinstance(data, BaseCpi):
                outdata = data.asByteStream()
                for out in outdata:
                    stream = KPA('Отпр-КПИ', out).stream
                    if PRINT:
                        print('{#ffffff}Отправка {#f7f68f}%s {#ffffff}в {#bad9ff}КПА' % data.getDescription()['translation'])
                    if HEX:
                        print('{#0bbeea}%s' % stream.hex())
                    DbLog.log(Exchange.ivk_file_name, 'Отправка %s в КПА' % data.getDescription()['translation'], False,
                              Exchange.ivk_file_path, str(stream))
                    local_sock.sendall(dest + stream)
                    local_sock_udp.sendto(stream, kpa_adress)
            elif isinstance(data, OTC):
                stream = KPA('Отпр-РКо' if data.isOpenOTC() else 'Отпр-РКз', data.asByteStreamKpa()).stream
                if PRINT:
                    print('{#ffffff}Отправка {#f7f68f}%s-%d {#ffffff}в {#bad9ff}КПА' % (
                        'РКо' if data.isOpenOTC() else 'РКз', data.otc))
                if HEX:
                    print('{#0bbeea}%s' % stream.hex())
                DbLog.log(Exchange.ivk_file_name,
                          'Отправка %s-%d в КПА' % ('РКо' if data.isOpenOTC() else 'РКз', data.otc), False,
                          Exchange.ivk_file_path, str(stream))
                local_sock.sendall(dest + stream)
                local_sock_udp.sendto(stream, kpa_adress)
            elif isinstance(data, KPA):
                if PRINT:
                    print('{#ffffff}Отправка {#ffe2ad}%s (%d) {#ffffff}в {#bad9ff}КПА' % (data.name, data.msg['id']))
                if HEX:
                    print('{#0bbeea}%s' % data.stream.hex())
                DbLog.log(Exchange.ivk_file_name, 'Отправка %s (%d) в КПА' % (data.name, data.msg['id']), False,
                          Exchange.ivk_file_path, str(data.stream))
                local_sock.sendall(dest + data.stream)
                local_sock_udp.sendto(data.stream, kpa_adress)
            else:
                raise Exception('Неопределен тип отправляемых данных "%s"' % repr(type(data)))
        elif queue_label == 'Ячейка ПИ':
            if isinstance(data, ICCELL):
                if PRINT:
                    print('{#ffffff}Отправка {#ffe2ad}%s (%d) {#ffffff}в {#b9a9de}Ячейку ПИ' % (
                    data.name, data.msg['id']))
                DbLog.log(Exchange.ivk_file_name, 'Отправка %s (%d) в Ячейку ПИ' % (data.name, data.msg['id']), False,
                          Exchange.ivk_file_path, str(data.stream))
                if HEX:
                    print('{#0bbeea}%s' % data.stream.hex())
                conf.incConf('iccell_counter', 255)
                local_sock.sendall(dest + data.stream)
                local_sock_udp.sendto(data.stream, kpa_adress)
            else:
                raise Exception('Неопределен тип отправляемых данных "%s"' % repr(type(data)))
        elif queue_label in SCPI.SCPI_DEVICES.keys():
            if isinstance(data, SCPI):
                # Проверка отправляемого сообщения в свзяке с источником питания (макс вольтаж, макс ток)
                data.deviceCheck(queue_label)
                if PRINT:
                    print('{#ffffff}Отправка {#ffe2ad}%s (%d) {#ffffff}в {#bdffc2}%s' % (
                        data.name, data.msg['id'], queue_label))
                if HEX:
                    print('{#0bbeea}%s' % data.stream.hex())
                DbLog.log(Exchange.ivk_file_name, 'Отправка %s (%d) в %s' % (data.name, data.msg['id'], queue_label),
                          False, Exchange.ivk_file_path, str(data.stream))
                local_sock.sendall(dest + struct.pack('B', data.msg[
                    'id']) + data.stream)  # Тут необычное поведение, пересылаем еще ИД сообщения для постановки в очередь отправки источника питания
                # вопросик
                local_sock_udp.sendto(struct.pack('B', data.msg['id']) + data.stream, kpa_adress)
            else:
                raise Exception('Неопределен тип отправляемых данных "%s"' % type(data).__name__)

    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def get(queue_label, msg_name, field_name):
        if queue_label not in Exchange.queues and queue_label != 'ТМИ' and queue_label != '':
            raise Exception('Неверный источник "%s"' % queue_label)

        DbLog.log(Exchange.ivk_file_name, 'Получение данных из %s, %s->%s' % (
           queue_label if queue_label != '' else 'источника питания', msg_name, field_name), False,
                 Exchange.ivk_file_path)

        if queue_label == 'ТМИ':
            if isinstance(msg_name, str):
                return RokotTmi.getTmi(msg_name, field_name)
            elif isinstance(msg_name, dict):
                return RokotTmi.getTmis(msg_name)
            else:
                raise Exception("Тип данных поля шифров должны быть: str, dict")

        # Источники питания
        if queue_label == '' and msg_name in SCPI.SCPI_DEVICES:
            return SCPIResponce.FromRedis(msg_name, field_name)

        resp = None
        if queue_label == 'КПА':
            resp = KPAResponce.FromRedis(msg_name)
        elif queue_label == 'Ячейка ПИ':
            resp = ICCellResponce.FromRedis(msg_name)

        if resp is None:
            raise Exception('Не удалось получить данные по команде "%s"' % msg_name)

        val = resp.unpacked.fieldByName(field_name)
        return val  # нормально если None

    WAIT_QUEUE_COLOR = {'КПА': '#bad9ff', 'Ячейка ПИ': '#b9a9de', '': '#bdffc2'}

    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def wait(queue_label, expression, timeout, print_interval=None):
        '''Формат expression ({сообщение.поле} > 15 and {сообщение.другое_поле} == -14.5) or {сообщение.третье_поле} <= 0
        '''
        if queue_label not in Exchange.queues and queue_label != 'ТМИ' and queue_label != '':
            raise Exception('Неверный источник "%s"' % queue_label)
        print('{#ffffff}Ожидание {#b1ecf0}"%s" {#ffffff}из {%s}%s{#ffffff}, таймаут %d сек' % (
            expression,
            Exchange.WAIT_QUEUE_COLOR[queue_label] if queue_label in Exchange.WAIT_QUEUE_COLOR else '#ffffff',
            queue_label if queue_label != '' else 'источников питания',
            timeout
        )
              )
        DbLog.log(Exchange.ivk_file_name, 'Ожидание "%s" из %s, таймаут %d сек' % (
            expression, queue_label if queue_label != '' else 'источников питания', timeout), False,
                  Exchange.ivk_file_path)

        params = re.findall(r'\{(.*?)\}', expression)
        params_locals = conf.odict()
        locals_params = conf.odict()
        for i, param in enumerate(params):
            local_var = 'var%d' % (i + 1,)
            params_locals[param] = local_var
            locals_params[local_var] = param
            expression = expression.replace('{%s}' % param, local_var)

        start_time = datetime.now()
        last_printed = None
        result = False
        while not result and (datetime.now() - start_time).total_seconds() < timeout:
            _locals = conf.odict()

            if queue_label == 'ТМИ':
                tmis = conf.odict()
                tmi_name_to_param = conf.odict()
                for param in params:
                    splitted = param.rsplit('.', 1)
                    msg_name = splitted[0]
                    field_name = splitted[1]
                    tmis[msg_name] = field_name
                    tmi_name_to_param[msg_name] = param
                tmis = RokotTmi.getTmis(tmis)
                for name, value in tmis.items():
                    _locals[params_locals[tmi_name_to_param[name]]] = value
            else:
                for param in params:
                    splitted = param.rsplit('.', 1)
                    msg_name = splitted[0]
                    field_name = splitted[1]

                    resp = None
                    if queue_label == 'КПА':
                        resp = KPAResponce.FromRedis(msg_name)
                    elif queue_label == 'Ячейка ПИ':
                        resp = ICCellResponce.FromRedis(msg_name)
                    elif queue_label == '':
                        resp = SCPIResponce.FromRedis(msg_name, field_name)

                    if queue_label != '':
                        if resp is None:
                            raise Exception('Не удалось получить данные по команде "%s"' % msg_name)
                        val = resp.unpacked.fieldByName(field_name)
                        _locals[params_locals[param]] = val
                    else:
                        _locals[params_locals[param]] = resp

            if all([var is not None for var in _locals.values()]):
                try:
                    result = eval(expression, {}, _locals)
                except Exception as exc:
                    raise Exception(
                        'В процессе обработки выражения "%s" произошла ошибка: "%s"' % (expression, repr(exc)))
                if print_interval is not None and (
                        last_printed is None or (datetime.now() - last_printed).total_seconds() >= print_interval):
                    vaules = ', '.join(['%s=%s' % (locals_params[var], value) for var, value in _locals.items()])
                    print('{#ffffff}Условие %s -> {#b1ecf0}%s' % (
                        'не выполнилось' if not result else 'выполнилось', vaules))
                    last_printed = datetime.now()

            if not result:
                time.sleep(1)

        return result

    @staticmethod
    def __monitorICCELL():
        while not Exchange.stop_daemons:
            dock = Exchange.iccell_dock
            if dock and dock.isVisible() and Exchange.queues['Ячейка ПИ']['connected']:
                try:
                    sock = Exchange.queues['Ячейка ПИ']['getSock']()
                    if dock.sost_checkbox.isChecked():
                        dock.setLoading('ЗапрСост', True)
                        conf.incConf('iccell_counter', 255)
                        sock.sendall(ICCELL('ЗапрСост').stream)
                        time.sleep(0.2)
                    if dock.sopriz_checkbox.isChecked():
                        dock.setLoading('ЗапрСопрИзол', True)
                        conf.incConf('iccell_counter', 255)
                        sock.sendall(ICCELL('ЗапрСопрИзол').stream)
                        time.sleep(0.2)
                    if dock.narab_checkbox.isChecked():
                        dock.setLoading('ЗапрНараб', True)
                        conf.incConf('iccell_counter', 255)
                        sock.sendall(ICCELL('ЗапрНараб', reset=0).stream)
                        time.sleep(0.2)
                    if dock.naprtlm_checkbox.isChecked():
                        dock.setLoading('ЗапрНапряжСигТЛМ', True)
                        conf.incConf('iccell_counter', 255)
                        sock.sendall(ICCELL('ЗапрНапряжСигТЛМ').stream)
                        time.sleep(0.2)
                    if dock.napr_checkbox.isChecked():
                        dock.setLoading('ЗапрНапряж', True)
                        conf.incConf('iccell_counter', 255)
                        sock.sendall(ICCELL('ЗапрНапряж').stream)
                        time.sleep(0.2)
                    if dock.tempab_checkbox.isChecked():
                        dock.setLoading('ЗапрТемпАБ', True)
                        conf.incConf('iccell_counter', 255)
                        sock.sendall(ICCELL('ЗапрТемпАБ').stream)
                        time.sleep(0.2)
                except Exception as exc:
                    print("monitor iccell exc: %s" % str(exc))
            time.sleep(2)

    @staticmethod
    def __monitorSCPI():
        while not Exchange.stop_daemons:
            if Exchange.scpi_dock and Exchange.scpi_dock.isVisible() and Exchange.scpi_dock.monitor_checkbox.isChecked():
                try:
                    for name, device in SCPI.SCPI_DEVICES.items():
                        send_queue = device['send_queue']
                        dest_id = Exchange.queues[name]['destination_id']
                        if Exchange.IsDestConnected(dest_id):
                            for msg_name in ('ЗапрСост', 'ЗапрНапряж', 'ЗапрТок'):
                                Exchange.scpi_dock.setLoading(name, True)
                                # Отправляем только если в очереди не стоит такой же запрос, т.к. данные все равно лягут в redis
                                if not send_queue.has('msg_id', SCPI.MESSAGES_TO_SCPI[msg_name]['id']):
                                    msg = SCPI(msg_name)
                                    # print('MONITOR %s %s' % (name, msg.name))
                                    send_queue.put({'dest_id': dest_id, 'msg_id': msg.msg['id'], 'stream': msg.stream})
                except Exception as exc:
                    print("monitor scpi exc: %s" % str(exc))
            time.sleep(2)

    @staticmethod
    def __listenTCP(sock_name, host, port, local_port, reconnect_step, queue_label, connect_to_label, getResponceFunc,
                    unpackedToDocFunc, onDisconnectFunc):
        reconnect = None
        sock = getattr(Exchange, sock_name)

        while not Exchange.stop_daemons:
            if sock is None:
                if reconnect:
                    time.sleep(reconnect)
                    reconnect = None
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if local_port:
                    sock.bind(('0.0.0.0',
                               local_port))  # Устанавливает локальный порт (на этом конце), '0.0.0.0' - прием на любом ip ЭТОГО ПК (несколько сетевух, вирутальтные и т.д.), host - на конкретном ip ЭТОГО ПК
                sock.settimeout(2)
                try:
                    sock.connect((host, port))
                    setattr(Exchange, sock_name, sock)
                    DbLog.logGlobalAndDb(queue_label, 'Соединение с %s (%s:%d) успешно установлено\n' % (
                        connect_to_label, host, port), False)
                    Exchange.queues[queue_label]['connected'] = True
                except Exception as exc:
                    sock = None
                    Exchange.queues[queue_label]['connected'] = False
                    if onDisconnectFunc:
                        onDisconnectFunc()

                    setattr(Exchange, sock_name, sock)
                    DbLog.logGlobalAndDb(queue_label, 'Не удалось установить соединение с %s (%s:%d), %s%s\n' % (
                        connect_to_label,
                        host,
                        port,
                        str(exc),
                        ', переподключение через %d секунд...' % reconnect_step if reconnect_step else ''
                    ), True)
                    if reconnect_step:
                        reconnect = reconnect_step
                        continue
                    else:
                        break
                sock.settimeout(None)

            try:
                data = sock.recv(65536)
            except:
                if Exchange.stop_daemons:
                    return
                DbLog.logGlobalAndDb(queue_label, 'Соединение с %s (%s:%d) разорвано, переподключение...\n' % (
                    connect_to_label, host, port), True)
                sock.close()
                sock = None
                Exchange.queues[queue_label]['connected'] = False
                if onDisconnectFunc:
                    onDisconnectFunc()
                continue
            if Exchange.stop_daemons:
                return
            if not data:
                DbLog.logGlobalAndDb(queue_label, 'Соединение с %s (%s:%d) разорвано, переподключение...\n' % (
                    connect_to_label, host, port), True)
                sock.close()
                sock = None
                Exchange.queues[queue_label]['connected'] = False
                if onDisconnectFunc:
                    onDisconnectFunc()
                continue

            resp = getResponceFunc(data)

            if resp.unpacked is not None and unpackedToDocFunc:
                unpackedToDocFunc(resp)
            if hasattr(resp, 'onData'):
                resp.onData()

    @staticmethod
    def __listenUDP(sock_name, host, local_port, getResponceFunc, unpackedToDocFunc, onDisconnectFunc):
        sock = getattr(Exchange, sock_name)
        while not Exchange.stop_daemons:
            if sock is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                setattr(Exchange, sock_name, sock)
                sock.bind(('0.0.0.0', local_port))
                # Устанавливает локальный порт (на этом конце), '0.0.0.0' - прием на любом ip ЭТОГО ПК (несколько сетевух, вирутальтные и т.д.), host - на конкретном ip ЭТОГО ПК
                sock.settimeout(100)
            try:
                data, addr = sock.recvfrom(2048)
            except Exception as exc:
                print('UDP recv exception: %s' % exc)
                if Exchange.stop_daemons:
                    return
                continue
            if Exchange.stop_daemons:
                return
            if not data:
                print('UDP NO DATA: %s' % exc)
                if Exchange.stop_daemons:
                    return
                continue

            resp = getResponceFunc(data)

            if resp.unpacked is not None and unpackedToDocFunc:
                unpackedToDocFunc(resp)
            if hasattr(resp, 'onData'):
                resp.onData()

    @staticmethod
    def __sendDispatch():
        Exchange.local_sock.listen()
        while not Exchange.stop_daemons:
            try:
                con, _ = Exchange.local_sock.accept()
                while not Exchange.stop_daemons:
                    try:
                        data = con.recv(2048)
                        if data:
                            dest_id = data[0]
                            queue_name = Exchange.DestToQueue(dest_id)
                            # Постанока в очередь для источников питания
                            # получаем данные по tcp от pydev процессов и тут, в ui-треде, ставим в свою очередь
                            if queue_name in SCPI.SCPI_DEVICES:
                                if Exchange.IsDestConnected(dest_id):
                                    msg_name, msg = SCPI.MsgById(data[1])
                                    if 'unpackResponce' in msg:
                                        send_queue = SCPI.SCPI_DEVICES[queue_name]['send_queue']
                                        # Отправляем только если в очереди не стоит такой же запрос, т.к. данные все равно лягут в redis
                                        if not send_queue.has('msg_id', msg['id']):
                                            send_queue.put(
                                                {'dest_id': dest_id, 'msg_id': msg['id'], 'stream': data[2:]})
                                    # Если у команды для источника питания не предусмотрен ответ, то просто отправляем
                                    else:
                                        sock = Exchange.DestToSock(dest_id)
                                        sock.sendall(data[2:])
                            # Обычная отправка
                            elif Exchange.IsDestConnected(dest_id):
                                # queue_name = Exchange.DestToQueue(dest_id)
                                # if queue_name == 'КПА':
                                #    print(data[1:])
                                sock = Exchange.DestToSock(dest_id)
                                sock.sendall(data[1:])
                        else:
                            con.close()
                            break
                    except Exception as exc:
                        print("send dispatch exc: %s" % str(exc))
                        con.close()
                        break
            except Exception as exc:
                print("local socket accept exc: %s" % str(exc))

    @staticmethod
    def __scpiSendQueueDispatch():
        while not Exchange.stop_daemons:
            for name, device in SCPI.SCPI_DEVICES.items():
                send_queue = device['send_queue']
                recv_queue = device['recv_queue']
                if recv_queue.empty():
                    if not send_queue.empty():
                        msg = send_queue.get()
                        # print('SEND %d' % msg['msg_id'])
                        recv_queue.put({'msg_id': msg['msg_id'], 'stream': msg['stream'], 'send_time': datetime.now()})
                        sock = Exchange.DestToSock(msg['dest_id'])
                        sock.sendall(msg['stream'])
                # таймаут очереди отправки на девайсы 2.5 сек
                elif (datetime.now() - recv_queue.getFromFirst('send_time')).total_seconds() > 2.5:
                    msg = recv_queue.get()
                    # print('DELETE %d' % msg['msg_id'])

            time.sleep(0.25)
