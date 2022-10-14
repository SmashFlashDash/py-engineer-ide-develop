import threading, binascii, json, time, re, struct, ctypes, traceback
import pika
import base64
from datetime import datetime
from ivk import config as conf
from ivk.global_log import GlobalLog
from ivk.log_db import DbLog
from ivk.abstract import AbstractExchange

from cpi_framework.utils.basecpi_abc import BaseCpi
from cpi_framework.spacecrafts.omka.otc import OTC

from ivk.scBRK.simplifications import getSimpleCommandsCPI

class Exchange(AbstractExchange):
    config = {
        'reponse_wait_time': 10,

        'amqp_ip': '192.168.3.87',
        'amqp_port': 5672,
        'amqp_virtual_host': 'MKA',
        'amqp_user': 'guest',
        'amqp_password': 'guest',

        'amqp_queues': {'БРК': 'BRK'},
        'amqp_queues_reverse': {'BRK': 'БРК'},
    }

    stop_daemons = False
    channel_out = None  # Канал для отправки всякого управления и КПИ вовне

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
        conf.cleanData()
              
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

        except Exception as exc:
            GlobalLog.log(threading.get_ident(), 'AMQP', 'Не удалось подключиться к AMQP серверу: %s\n' % repr(exc),
                          True)

    @staticmethod
    def onClose():
        '''Закрытие приложения'''
        Exchange.stop_daemons = True

    @staticmethod
    def getRootCommandNodeName():
        '''Определение названия для группы комманд в панели комманд'''
        return 'БРК'
    @staticmethod  
    def getRootCommandNodeDescription():
        '''Определение описания для группы комманд в панели комманд'''
        return ''

    @staticmethod
    def getModuleFilter():
        '''Определение списка модулей, которые нужно подтянуть из cpi_framework, например:
        '''
        return ['cpiomka']

    @staticmethod
    def getAdditionalCommands():
        '''Определение дополнительных комманд, которые нужно добавить в панельку:'''
        commands = []
        #Упрощенные команды отправки КПИ
        commands.extend(getSimpleCommandsCPI())
        commands.append({
            'name': '',
            'import_string': '',
            'description': 'Передача скорости',
            'params': [''],
            'values': ["'8'"],
            'keyword': [False],
            'translation': 'Передача скорости',
            'cat': Exchange.getRootCommandNodeName(),
            'queues': Exchange.getCpiFrameworkDestinations()
        })
        return commands

    @staticmethod
    def getCpiFrameworkDestinations():
        '''Определение списка пунктов назначения для команд из cpi_framework, например:
        return ['ТКС', 'УЦО1', 'УЦО2']
        '''
        return ['БРК']

    @staticmethod
    def initDocks(parent, tabs_widget):
        '''Инициализация док-виджетов, возвращает массив с виджетами'''
        return []
  
    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def send(queue_label, data):
        """Отправка комманды по назначению, параметры:
        queue_label - пункт назначения
        data - данные для отправки
        """
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
                cpicount = len(cpibytes) // 64
                
                print('{#ccf3ff}Отправка %s в %s ... ' % (name, queue_label))
                try:
                    for i in range(cpicount):
                        body['arguments'] = binascii.hexlify(cpibytes[i * 64:i * 64 + 64]).decode('utf-8')                        
                        if Exchange.channel_out is None:
                            Exchange.make_out_channel()                   
                        #Отправка КПИ
                        Exchange.channel_out.basic_publish(exchange='', routing_key=conf.getConf('amqp_queues')[queue_label], body=json.dumps(body))
                        print("Отправлена фраза КПИ %d из %d" % (i+1, cpicount))
                except Exception as exc:
                    print('{#ff0000}Не удалось отправить %s в %s: %s' % (name, queue_label, repr(exc)))
            if isinstance(data, str):
                body['cmd'] = 'SLEEP'  
                print('{#ccf3ff}Отправка %s в %s ... ' % (name, queue_label))   
                body['arguments'] = data
                try:
                    if Exchange.channel_out is None:
                                Exchange.make_out_channel()    
                    Exchange.channel_out.basic_publish(exchange='', routing_key=conf.getConf('amqp_queues')[queue_label], body=json.dumps(body))
                    print("Отправлена установка скорости %s" % (data))
                except Exception as exc:
                    print('{#ff0000}Не удалось отправить %s в %s: %s' % (name, queue_label, repr(exc)))
        except Exception as exc:
            print('{#ff0000}Не удалось отправить сообщение в AMQP-очередь "%s": %s' % (queue_label, repr(exc)))

    # Выполняется из pydev процесса, не использовать переменные ui-процесса
    @staticmethod
    def get(queue_label, msg_name, field_name):
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



