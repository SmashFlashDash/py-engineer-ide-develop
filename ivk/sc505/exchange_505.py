import threading, binascii, json, time, re, struct, ctypes, traceback, socket
import pika
import base64
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pysnmp.hlapi import SnmpEngine, UsmUserData, UdpTransportTarget, ContextData, auth, getCmd, setCmd
from pyasn1.codec.ber import decoder
from pysnmp.proto.mpmod.rfc3412 import SNMPv3Message, ScopedPduData, ScopedPDU
from pysnmp.proto.rfc1905 import PDUs, SNMPv2TrapPDU, VarBindList
from pysnmp.proto.rfc1902 import ObjectSyntax

from ivk import config as conf
from ivk.global_log import GlobalLog
from ivk.log_db import DbLog
from ivk.abstract import AbstractExchange
from ivk.rokot_tmi import RokotTmi, RokotWidget

from cpi_framework.utils.basecpi_abc import BaseCpi
from cpi_framework import otc505
from cpi_framework.utils.basecpi_abc import *
from ivk.sc505.boi import BOIIE

from ivk.sc505.control_td import TerminalDevice
from ivk.sc505.control_modem import Modem
from ivk.sc505.widget_monitor import MonitorWidget
from ivk.sc505.simplifications import getSimpleCommandsDP, RCD
from ivk.swap import swap_bytes


class Exchange(AbstractExchange):
    config = {
        'reponse_wait_time': 10,

        'amqp_ip': '192.168.3.87',
        'amqp_port': 5672,
        'amqp_virtual_host': '505_test',  # '/' for default
        'amqp_user': 'guest',
        'amqp_password': 'guest',

        'amqp_queues': {'УЦО1': 'DP1', 'УЦО2': 'DP2', 'ТКС': 'BOI'},
        'amqp_queues_reverse': {'DP1': 'УЦО1', 'DP2': 'УЦО2', 'BOI': 'ТКС'},

        'amqp_rcd_queue': 'RCD',
        'amqp_rcd_queue_params': {'x-max-length': 10},
        
        'amqp_ack_queue': 'DP_ACK',
        'amqp_ack_queue_params': {'x-max-length': 10},

        'amqp_td_status_queue': 'SIM_STATUS',
        'amqp_td_status_params': {'x-max-length': 10},

        'amqp_dp_rcd_queue': 'DP_RCD',
        'amqp_dp_rcd_queue_params': {'x-max-length': 10},

        'amqp_rokot_queue': 'ROKOT',
        'amqp_rokot_queue_params': None,

        'modem_ip' : '192.168.3.55',
        'modem_port' : 10161,
        'modem_local_port' : 10162,
        'modem_proto' : 'md5',
        'modem_user' : 'control',
        'modem_password' : '12345678',
        'modem_data_proto' : 'DES',
        'modem_data_pass' : '87654321',

        'rokot_db_ip': '192.168.13.127',
        'rokot_db_port': 5432,
        'rokot_db_name': 'rokot_ng',
        'rokot_db_user': 'rokot',
        'rokot_db_password': '@sS00n@s',
        'rokot_default_ka_umn': '0505',
        'rokot_use_log_database' : False,

        'log_to_database': True,
        'log_db_ip': '127.0.0.1',
        'log_db_port': 5432,
        'log_db_name': 'ivk_log',
        'log_db_user': 'postgres',
        'log_db_password': '1111'

    }

    monitor_dock = None
    stop_daemons = False
    channel_out = None  # Канал для отправки всякого управления и КПИ вовне
    modem_udp_sock = None

    @staticmethod
    def make_out_channel():
        parameters_out = pika.ConnectionParameters(
            conf.getConf('amqp_ip'),
            conf.getConf('amqp_port'),
            conf.getConf('amqp_virtual_host'),
            pika.PlainCredentials(conf.getConf('amqp_user'), conf.getConf('amqp_password'))
        )
        parameters_out.heartbeat = 0
        connection_out = pika.BlockingConnection(parameters_out)
        Exchange.channel_out = connection_out.channel()

    @staticmethod
    def init():
        """Открытие приложение, инициализация модуля обмена"""

        # Очистка redis бд данных
        conf.cleanData()
        conf.updData("amqp_ack", 0)
        conf.updData("amqp_ack_semaphore", False)
        conf.updData("cpi_crypt_iv", 0) #первое использование увеличит на 1

        try:
            # Параметры AMQP соединения
            parameters = pika.ConnectionParameters(
                conf.getConf('amqp_ip'),
                conf.getConf('amqp_port'),
                conf.getConf('amqp_virtual_host'),
                pika.PlainCredentials(conf.getConf('amqp_user'), conf.getConf('amqp_password'))
            )
            parameters.heartbeat = 0
            connection = pika.BlockingConnection(parameters)

            # Инициализация очередей для отправки сообщений
            channel = connection.channel()
            for _, queue in conf.getConf('amqp_queues').items():
                channel.queue_declare(queue)
                channel.queue_purge(queue)
            channel.close()
            connection.close()

            GlobalLog.log(threading.get_ident(), 'AMQP',
                          'Подключено к AMQP серверу (%s:%d), созданы и очищены очереди: %s\n' % (
                              conf.getConf('amqp_ip'),
                              conf.getConf('amqp_port'),
                              ', '.join([q for _, q in conf.getConf('amqp_queues').items()])
                          ), False)

            # Инициализация очереди для получения данных
            connection_recv = pika.BlockingConnection(parameters)
            channel_recv = connection_recv.channel()
            channel_recv.queue_declare(conf.getConf('amqp_rcd_queue'), arguments=conf.getConf('amqp_rcd_queue_params'))
            channel_recv.queue_purge(conf.getConf('amqp_rcd_queue'))
            t = threading.Thread(
                target=lambda: Exchange.__start_consuming(conf.getConf('amqp_rcd_queue'), channel_recv), daemon=True)
            t.start()

            GlobalLog.log(threading.get_ident(), 'AMQP',
                          'Cоздана и очищена очередь для приема данных: %s\n' % conf.getConf('amqp_rcd_queue'), False)

            # Инициализация очереди для получения acknolegment (отчетов о приеме сообщений)
            connection_ack = pika.BlockingConnection(parameters)
            channel_ack = connection_ack.channel()
            channel_ack.queue_declare(conf.getConf('amqp_ack_queue'), arguments=conf.getConf('amqp_ack_queue_params'))
            channel_ack.queue_purge(conf.getConf('amqp_ack_queue'))
            t = threading.Thread(target=lambda: Exchange.__start_consuming(conf.getConf('amqp_ack_queue'), channel_ack),
                                 daemon=True)
            t.start()

            GlobalLog.log(threading.get_ident(), 'AMQP',
                          'Cоздана и очищена очередь для приема ответов: %s\n' % conf.getConf('amqp_ack_queue'), False)

            # Инициализация очереди для получения ответов от оконечных устройств status, ...
            connection_td = pika.BlockingConnection(parameters)
            channel_td = connection_td.channel()
            channel_td.queue_declare(conf.getConf('amqp_td_status_queue'),
                                     arguments=conf.getConf('amqp_td_status_params'))
            channel_td.queue_purge(conf.getConf('amqp_td_status_queue'))
            t = threading.Thread(
                target=lambda: Exchange.__start_consuming(conf.getConf('amqp_td_status_queue'), channel_td),
                daemon=True)
            t.start()

            GlobalLog.log(threading.get_ident(), 'AMQP',
                          'Cоздана и очищена очередь для мониторинга ОУ: %s\n' % conf.getConf('amqp_td_status_queue'),
                          False)

            # Инициализация очереди для получения ИОК
            connection_dp_rcd = pika.BlockingConnection(parameters)
            channel_dp_rcd = connection_dp_rcd.channel()
            channel_dp_rcd.queue_declare(conf.getConf('amqp_dp_rcd_queue'), arguments=conf.getConf('amqp_dp_rcd_queue_params'))
            channel_dp_rcd.queue_purge(conf.getConf('amqp_dp_rcd_queue'))
            t = threading.Thread(target=lambda: Exchange.__start_consuming(conf.getConf('amqp_dp_rcd_queue'), channel_dp_rcd),
                                 daemon=True)
            t.start()

            GlobalLog.log(threading.get_ident(), 'AMQP',
                          'Cоздана и очищена очередь для приема ИОК: %s\n' % conf.getConf('amqp_dp_rcd_queue'), False)
            
            #Запускаем прослушивание SNMP-модема по UDP
            t = threading.Thread(target=lambda: Exchange.__listenUDP(
                'modem_udp_sock', 
                conf.getConf('modem_ip'), 
                conf.getConf('modem_local_port'),
                ),
            daemon=True)
            t.start()
            GlobalLog.log(threading.get_ident(), 'МОДЕМ',
                          'Запущено прослушивание модема (%s) по UDP на порту %d\n' % (conf.getConf('modem_ip'), conf.getConf('modem_local_port')), False)

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

            # Запуск мониторинга статуса оконечников
            t = threading.Thread(target=Exchange.__td_status, daemon=True)
            t.start()

            # Подключение к БД логов
            try:
                DbLog.connectDb(raise_exceptions=True)
                GlobalLog.log(threading.get_ident(), 'LOG_DB', 'Подключено к PostgreSQL серверу (%s:%d)\n' % (
                    conf.getConf("log_db_ip"), conf.getConf("log_db_port")), False)
            except Exception as exc:
                GlobalLog.log(threading.get_ident(), 'LOG_DB', 'Не удалось подключиться к PostgreSQL серверу: %s - %s\n' % (conf.getConf("log_db_ip"), repr(exc)), True)

        except Exception as exc:
            GlobalLog.log(threading.get_ident(), 'AMQP', 'Не удалось подключиться к AMQP серверу: %s\n' % repr(exc),
                          True)

    @staticmethod
    def onClose():
        '''Закрытие приложения'''
        Exchange.stop_daemons = True
        print("closing -> stop daemons")
        if Exchange.modem_udp_sock is not None:
            try:
                Exchange.modem_udp_sock.shutdown(socket.SHUT_RDWR)
                Exchange.modem_udp_sock.close()
            except Exception as exc:
                print("modem_udp_sock close exc: %s" % str(exc))
        print("closing -> modem_udp_sock closed")

    @staticmethod
    def getRootCommandNodeName():
        '''Определение названия для группы комманд в панели комманд'''
        return 'КА 505'
    @staticmethod  
    def getRootCommandNodeDescription():
        '''Определение описания для группы комманд в панели комманд'''
        return ''

    @staticmethod
    def getModuleFilter():
        '''Определение списка модулей, которые нужно подтянуть из cpi_framework, например:
        '''
        return ['cpi505']

    @staticmethod
    def getAdditionalCommands():
        '''Определение дополнительных комманд, которые нужно добавить в панельку:'''
        commands = []
        #Упрощенные команды отправки в УЦО1 и УЦО2
        commands.extend(getSimpleCommandsDP())
        # Разовые команды 505
        commands.append({
            'name': 'OTC505',
            'import_string': 'from cpi_framework.spacecrafts.sc505.otc import OTC505',
            'description': 'Выдача разовых команд',
            'params': ['cmd'],
            'values': ['0'],
            'keyword': [False],
            'translation': 'РК',
            'cat': Exchange.getRootCommandNodeName(),
            'queues': Exchange.getCpiFrameworkDestinations()
        })
        # Управление оконечниками
        for name, msg in TerminalDevice.MESSAGES_TO_TD.items():
            commands.append({
                'name': 'TerminalDevice.MSG',
                'import_string': 'from ivk.sc505.control_td import TerminalDevice',
                'description': msg['description'],
                'params': ['name'] if not 'params' in msg else ['name'] + [p['name'] for p in msg['params']],
                'values': ["'%s'" % name] if not 'params' in msg else ["'%s'" % name] + [p['default'] for p in
                                                                                         msg['params']],
                'keyword': [False] if not 'params' in msg else [False] + [True for p in msg['params']],
                'translation': name,
                'cat': 'Управление ОУ',
                'queues': list(conf.getConf('amqp_queues').keys())
            })
        # Управление модемом
        for name, msg in Modem.MESSAGES_TO_MODEM.items():
            if 'trap' not in msg['type'] and 'inform' not in msg['type']:
                commands.append({
                    'name': 'Modem.MSG',
                    'import_string': 'from ivk.sc505.control_modem import Modem',
                    'description': msg['description'],
                    'params': ['name', 'value'] if msg['access'] == 'R/W' else ['name'],
                    'values': ["'%s'" % name, '' if msg['default'] is None else str(msg['default']) if isinstance(msg['default'], int) else "'%s'" % msg['default']] if msg['access'] == 'R/W' else ["'%s'" % name],
                    'keyword': [False, False] if msg['access'] == 'R/W' else [False],
                    'skip_params' : [None, 'Задать'] if msg['access'] == 'R/W' else [None],
                    'translation': "%s (%s)" % (name, msg['oid']),
                    'cat': 'Модем',
                    'queues': ['МОДЕМ']
                })
        commands.append({
            'name': 'BOIIE',
            'import_string': 'from ivk.sc505.boi import BOIIE',
            'description': 'Имитация важного события БОИ',
            'params': ['IE'],
            'values': ['1'],
            'keyword': [False],
            'translation': 'ВС',
            'cat': 'БОИ',
            'queues': ['ТКС']
        })
        commands.append({
            'name': 'BOIKM',
            'import_string': '',
            'description': 'Имитация важного события БОИ',
            'params': ['KM'],
            'values': ['[]'],
            'keyword': [False],
            'translation': 'КМ',
            'cat': 'БОИ',
            'queues': ['ТКС']
        })
        commands.extend(RokotTmi.getAdditionalCommands())

        return commands

    @staticmethod
    def getCpiFrameworkDestinations():
        '''Определение списка пунктов назначения для команд из cpi_framework, например:
        return ['ТКС', 'УЦО1', 'УЦО2']
        '''
        return ['УЦО1', 'УЦО2']

    @staticmethod
    def initDocks(parent, tabs_widget):
        '''Инициализация док-виджетов, возвращает массив с виджетами'''
        Exchange.monitor_dock = MonitorWidget(parent, tabs_widget)
        Exchange.rokot_widget = RokotWidget(parent, tabs_widget)
        return [Exchange.monitor_dock, Exchange.rokot_widget]

    @staticmethod
    def crypt(phrase, key, iv):
        '''шифрование  AES-256 GCM
        необходимо установить cryptography'''
        aesgcm = AESGCM(key)
        iv=iv<<2
        hack_iv = struct.pack("<I", iv)+struct.pack('b',0)*8
        #ct = aesgcm.encrypt(struct.pack(">I", iv), phrase[2:52], phrase[:2])
        ct = aesgcm.encrypt(hack_iv, phrase[2:52], phrase[:2])
        iv=iv>>2
        phrase = phrase[:2] + ct[0:58] + struct.pack("<I", iv)[:4]
        return phrase
        
    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def send(queue_label, data, timeout=11, aes_key=bytes([0xAA for i in range(32)]), iv=None, swap_need=False):
        """Отправка комманды по назначению, параметры:
        queue_label - пункт назначения
        data - данные для отправки
        """
        #SNMP-модем
        if queue_label == 'МОДЕМ':
            (data, msg_name, msg, mode) = data
            if data is None:
                return None

            try:
                if conf.getConf("modem_proto") == 'md5':
                    auth_protocol = auth.usmHMACMD5AuthProtocol 
                elif conf.getConf("modem_proto") == 'sha':
                    auth_protocol = auth.usmHMACSHAAuthProtocol
                else:
                    raise Exception('Конфигурация modem_proto задана неверно, указано %s, доступно "md5" или "sha"' % str(conf.getConf("modem_proto"))) 
                
                if conf.getConf("modem_data_proto") == 'DES':
                    priv_protocol = auth.usmDESPrivProtocol 
                elif conf.getConf("modem_data_proto") == 'AES':
                    priv_protocol = auth.usmAesCfb128Protocol
                else:
                    raise Exception('Конфигурация modem_data_proto задана неверно, указано %s, доступно "DES" или "AES"' % str(conf.getConf("modem_data_proto")))

                user_data = UsmUserData(conf.getConf("modem_user"), conf.getConf("modem_password"), conf.getConf("modem_data_pass"), authProtocol=auth_protocol, privProtocol=priv_protocol)
                transport_target = UdpTransportTarget((conf.getConf("modem_ip"), conf.getConf("modem_port")))

                if mode == 'R':
                    print('{#cec4f5}Получение %s (%s) из модема ... ' % (msg_name, msg['oid']))
                    iterator = getCmd(SnmpEngine(), user_data, transport_target, ContextData(), data)
                    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                        if errorIndication:
                            raise Exception(str(errorIndication))
                        elif errorStatus:
                            raise Exception('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                        else:
                            for varBind in varBinds:
                                val = int(varBind[1]) if msg['type'] in ('Integer', 'Gauge32') else varBind[1].prettyPrint()
                                raw_val = varBind[1]._value
                                print('{#e5deff}Получено %s = %s' % (varBind[0].getOid(), str(val)))
                                return val, raw_val
                else:
                    print('{#cec4f5}Установка значения для %s (%s) в модеме ... ' % (msg_name, msg['oid']))
                    iterator = setCmd(SnmpEngine(), user_data, transport_target, ContextData(), data)
                    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                        if errorIndication:
                            raise Exception(str(errorIndication))
                        elif errorStatus:
                            raise Exception('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
                        else:
                            for varBind in varBinds:
                                val = int(varBind[1]) if msg['type'] in ('Integer', 'Gauge32') else varBind[1].prettyPrint()
                                raw_val = varBind[1]._value
                                print('{#e5deff}Установлено %s = %s' % (varBind[0].getOid(), str(val)))
                                return val, raw_val
            except Exception as exc:
                print('{#ff0000}Ошибка при обмене с модемом: %s' % repr(exc))
            
            return None

        #AMQP очереди
        else:
            ACK = None

            try:
                if queue_label not in conf.getConf('amqp_queues'):
                    raise Exception('Не верно задано название очереди AMQP - "%s", доступны названия %s' % (
                        queue_label, ', '.join(conf.getConf('amqp_queues').keys())))

                body = {}
                name = 'КПИ'
                if isinstance(data, BaseCpi) or isinstance(data, bytes):
                    from_bytes = isinstance(data, bytes)
                    
                    name = data.getDescription()['translation'] if not from_bytes else 'Байт-КПИ'
                    body['cmd'] = 'CPI'
                    cpibytes = data.asByteStream() if not from_bytes else data
                    if swap_need:
                        cpibytes = bytearray(cpibytes)
                        swap_bytes(cpibytes, 1)
                        cpibytes = bytes(cpibytes)
                    cpicount = len(cpibytes) // 64

                    #Ожидание завершения предыдущей отправки
                    if timeout:
                        sleep_counter = 0
                        while conf.getData("amqp_ack_semaphore") is True:
                            time.sleep(0.05)
                            sleep_counter += 1
                            if sleep_counter >= 20:
                                print("Ожидание завершения отправки другого сообщения ...")
                                sleep_counter = 0
                        #И блокируем отправку для других процессов и потоков
                        conf.updData("amqp_ack_semaphore", True)

                    print('{#ccf3ff}Отправка %s в %s ... ' % (name, queue_label))
                    try:
                        for i in range(cpicount):
                            #Шифрование при необходимости
                            if aes_key:
                                if iv is None:
                                    iv = conf.incData("cpi_crypt_iv")
                                else:
                                    iv+=1
                                    conf.updData("cpi_crypt_iv", iv)
                                body['arguments'] = ''.join(
                                    binascii.hexlify(Exchange.crypt(cpibytes[i * 64:i * 64 + 64], aes_key, iv)).decode('utf-8'))
                            else:
                                body['arguments'] = binascii.hexlify(cpibytes[i * 64:i * 64 + 64]).decode('utf-8')
                            
                            if Exchange.channel_out is None:
                                Exchange.make_out_channel()
                            
                            #Ставим ожидание ответа при необходимости
                            if timeout:
                                conf.updData("amqp_ack", 0)
                                send_time = datetime.now()

                            #Отправка КПИ
                            Exchange.channel_out.basic_publish(exchange='', routing_key=conf.getConf('amqp_queues')[queue_label], body=json.dumps(body))

                            #Ожидаем ответ
                            if timeout:
                                ACK = conf.getData("amqp_ack")
                                while ACK == 0 and (datetime.now() - send_time).total_seconds() < timeout:
                                    time.sleep(0.05)
                                    ACK = conf.getData("amqp_ack")
                                print("%sОтправлена фраза КПИ %d из %d с результатом '%s'" % ('{#4fff9b}' if ACK == 1 else '{#ff4545}', i+1, cpicount, "%s (%d)" % ("ACK" if ACK == 1 else "Timeout" if ACK == 0 else "Error", ACK)))
                                #break отправки нескольких фраз, если одна не дошла
                                if not ACK:
                                    break
                            else:
                                print("Отправлена фраза КПИ %d из %d" % (i+1, cpicount))

                    except Exception as exc:
                        print('{#ff0000}Не удалось отправить %s в %s: %s' % (name, queue_label, repr(exc)))
                    
                    if timeout:
                        conf.updData("amqp_ack_semaphore", False)
                else:

                    if isinstance(data, otc505.OTC505):
                        name = 'РК'
                        body['cmd'] = 'OTC'
                        body['arguments'] = str(data.cmd)
                    elif isinstance(data, dict):
                        name = data['cmd']
                        body = data
                    elif isinstance(data, BOIIE):
                        body['cmd'] = "IE"
                        body['arguments'] = str(data.ie)
                    else:
                        raise Exception('Некорректный тип данных для отправки "%s"' % type(data).__name__)

                    print('{#ccf3ff}Отправка %s в %s ... ' % (name, queue_label))
                    if Exchange.channel_out is None:
                        Exchange.make_out_channel()
                    Exchange.channel_out.basic_publish(exchange='', routing_key=conf.getConf('amqp_queues')[queue_label], body=json.dumps(body))
                

            except Exception as exc:
                print('{#ff0000}Не удалось отправить сообщение в AMQP-очередь "%s": %s' % (queue_label, repr(exc)))
            
            return ACK 

    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def get(queue_label, msg_name, field_name):
        if queue_label == 'ТМИ':
            return RokotTmi.getTmi(msg_name, field_name)
        else:
            raise Exception('Получение параметров не реализовано для источника "%s"' % queue_label)

    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def wait(queue_label, expression, timeout, print_locals=False):
        '''Формат expression ({сообщение.поле} > 15 and {сообщение.другое_поле} == -14.5) or {сообщение.третье_поле} <= 0
        '''
        params = re.findall(r'\{(.*?)\}', expression)
        params_to_locals = { }
        locals_to_params = { }
        for i, param in enumerate(params):
            local_var = 'var%d' % (i + 1,)
            params_to_locals[param] = local_var
            locals_to_params[local_var] = param
            expression = expression.replace('{%s}' % param, local_var)

        start_time = datetime.now()
        result = False
        while not result and (datetime.now() - start_time).total_seconds() < timeout:
            _locals = { }

            if queue_label == 'ТМИ':
                tmis = { }
                tmi_name_to_param = { }
                for param in params:
                    splitted = param.rsplit('.', 1)
                    msg_name = splitted[0]
                    field_name = splitted[1]
                    tmis[msg_name] = field_name
                    tmi_name_to_param[msg_name] = param
                tmis = RokotTmi.getTmis(tmis)
                for name, value in tmis.items():
                    _locals[params_to_locals[tmi_name_to_param[name]]] = value
            else:
                raise Exception('Ожидание параметров не реализовано для источника "%s"' % queue_label)

            if all([var is not None for var in _locals.values()]):
                if print_locals:
                    print(''.join(['%s: %s' % (locals_to_params[k], str(v)) for k, v in _locals.items()]))
                try:
                    result = eval(expression, globals(), _locals)
                except Exception as exc:
                    raise Exception(
                        'В процессе обработки выражения "%s" произошла ошибка: "%s"' % (expression, repr(exc)))

            if not result:
                time.sleep(1)

        return result


    @staticmethod
    def __listenUDP(sock_name, host, local_port):     
        sock = getattr(Exchange, sock_name)      
        while not Exchange.stop_daemons:
            if sock is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                setattr(Exchange, sock_name, sock)
                sock.bind(('0.0.0.0', local_port)) #Устанавливает локальный порт (на этом конце), '0.0.0.0' - прием на любом ip ЭТОГО ПК (несколько сетевух, вирутальтные и т.д.), host - на конкретном ip ЭТОГО ПК
                sock.settimeout(1000)
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
            
            varbinds = []
            msg, restOfwholeMsg = decoder.decode(data, asn1Spec=SNMPv3Message())
            for v1 in msg.values():
                if isinstance(v1, ScopedPduData):
                    for v2 in v1.values():
                        if isinstance(v2, ScopedPDU):
                            for v3 in v2.values():
                                if isinstance(v3, PDUs):
                                    for v4 in v3.values():
                                        if isinstance(v4, SNMPv2TrapPDU):
                                            for v5 in v4.values(): 
                                                if isinstance(v5, VarBindList):
                                                    for bindVal in v5:
                                                        oid = str(bindVal[0])
                                                        value = None
                                                        for bv1 in bindVal[1].values():
                                                            if isinstance(bv1, ObjectSyntax):
                                                                for bv2 in bv1.values():
                                                                    for bv3 in bv2.values():
                                                                        value = bv3
                                                                        break
                                                                    break
                                                                break
                                                        varbinds.append((oid, value))
                                                    break
                                            break
                                    break
                            break
                    break
            
            print('===== MODEM TRAP ======')
            for varbind in varbinds:
                (oid, val) = varbind
                name = None
                msg = None
                for n, m in Modem.MESSAGES_TO_MODEM.items():
                    if m['oid'] == oid:
                        msg = m
                        name = n
                        break
                if msg:
                    binary = bytes(val) if msg['type'] not in ('Integer', 'Gauge32') else None
                    val = int(val) if msg['type'] in ('Integer', 'Gauge32') else val.prettyPrint()
                    print('%s (%s) = %s | %s' % (name, oid, val, binary))
                else:
                    val = val.prettyPrint()
                    print('unknown (%s) = %s' % (oid, val))

        # 'modem_ip' : '192.168.3.55',
        # 'modem_port' : 10161,
        # 'modem_local_port' : 10162,
        # 'modem_proto' : 'md5',
        # 'modem_user' : 'control',
        # 'modem_password' : '12345678',
        # 'modem_data_proto' : 'DES',
        # 'modem_data_pass' : '87654321',

    @staticmethod
    def __start_consuming(queue_name, channel):
        cosumer_tag = ''

        while True:
            try:
                cosumer_tag = channel.basic_consume(queue=queue_name, on_message_callback=Exchange.__consume_message,
                                                    auto_ack=True, exclusive=True)
                channel.start_consuming()
            except Exception as exc:
                GlobalLog.log(threading.get_ident(), 'AMQP',
                              'Не удалось инициализировать AMQP-очередь "%s": %s\n' % (queue_name, repr(exc)), True)
                if channel.is_open:
                    channel.basic_cancel(cosumer_tag)
                time.sleep(1)

    @staticmethod
    def __consume_message(ch, method, properties, body, *args, **kwargs):
        try:
            msg = json.loads(body.decode('utf-8'))
            msg_from = conf.getConf('amqp_queues_reverse')[msg['from']] if msg['from'] in conf.getConf('amqp_queues_reverse') else method.routing_key

            #Acknolegement после отправки КПИ
            if method.routing_key == conf.getConf('amqp_ack_queue'):
                if msg['cmd'] == 'CPI_ACK':
                    arg = int(msg['arguments'], 16)
                    counter = (arg >> 8) & 0xFF
                    ack = arg & 0xFF
                    response = 'КПИ получено, счетчик: %d, результат: %d' % (counter, ack)
                    Exchange.monitor_dock.updateStatus({'queue': msg['from'], 'counter_cpi': counter})
                else:
                    response = 'Не реализована расшифровка cmd "%s" из очереди "%s"' % (msg['cmd'], method.routing_key)
                conf.updData("amqp_ack", ack)
                GlobalLog.log(threading.get_ident(), 'AMQP', 'Ответ от %s: %s\n' % (msg_from, response), False)

            #Телеметрия рокот и RCD
            elif method.routing_key == conf.getConf('amqp_rcd_queue'):
                
                #При необходимости пересылаем в рокот новый ключ шифрования
                new_aes_key = conf.getData('ROKOT_NEW_AES_KEY')
                if new_aes_key is not None:
                    conf.updData('ROKOT_NEW_AES_KEY', None)
                    key_to_send = b'\x4b\x45\x59\x5f' + AsciiHex(new_aes_key).bytes
                    key_to_send = key_to_send + b'\x00'*(68-len(key_to_send))
                    RokotTmi.sendTmi(key_to_send)
                
                data = base64.b16decode(msg['arguments'])
                data = b'\x52\x43\x44\x5f' + data
                RokotTmi.sendTmi(data)
                Exchange.rokot_widget.tmiSent()
                # print('Пересылаем %s в ROKOT из %s, длина %d' % (msg['cmd'], msg_from, len(data)))
            
            #Статус оконечников
            elif method.routing_key == conf.getConf('amqp_td_status_queue'):
                if msg['cmd'] == 'STATUS':
                    Exchange.monitor_dock.updateStatus({'queue': msg['from'], 'status': msg['arguments'] == 'true'})
                else:
                    print('Не реализована расшифровка cmd "%s" из очереди "%s"' % (msg['cmd'], method.routing_key))

            #ИОК2
            elif method.routing_key == conf.getConf('amqp_dp_rcd_queue'):
                rcd = RCD()
                rcd.fromStream(AsciiHex(msg['arguments']).bytes)
                rcd.total = AsciiHex(msg['arguments'])

                if conf.getData('RCD_SEMAPHORE') is not None:
                    while conf.getData('RCD_SEMAPHORE'):
                        time.sleep(0.05)
                conf.updData('RCD_SEMAPHORE', True)
                conf.updData('ИОК_%d' % rcd.num, rcd.toDict())
                conf.updData('RCD_SEMAPHORE', False)
                print('RECEIVED RCD', rcd.num, rcd.addnum, rcd.wordcount, bytes(rcd.body))

            else:
                raise Exception("Неизвестная очередь")
 
        except Exception as exc:
            GlobalLog.log(threading.get_ident(), 'AMQP',
                          'Не удалось получить сообщение из AMQP-очереди "%s": %s\n' % (method.routing_key, repr(exc)),
                          True)
            traceback.print_exc()

    @staticmethod
    def __td_status():
        parameters = pika.ConnectionParameters(
            conf.getConf('amqp_ip'),
            conf.getConf('amqp_port'),
            conf.getConf('amqp_virtual_host'),
            pika.PlainCredentials(conf.getConf('amqp_user'), conf.getConf('amqp_password'))
        )
        parameters.heartbeat = 0
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        while not Exchange.stop_daemons:
            for queue in conf.getConf('amqp_queues').values():
                channel.basic_publish(exchange='', routing_key=queue, body=json.dumps(TerminalDevice.MSG('Статус')))
            time.sleep(2)

        channel.close()
        connection.close()



