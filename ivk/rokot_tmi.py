import threading, time, traceback, time
import pika
import psycopg2, psycopg2.extras
from datetime import datetime

from PyQt5.QtWidgets import QWidget, QBoxLayout, QDockWidget, QLabel, QPushButton, QComboBox, QLineEdit, QMenu, QAction, QFileDialog
from PyQt5.QtGui import QColor, QIcon, QPalette
from PyQt5.QtCore import Qt

from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.labels import StyledLabel
from ui.components.commons import Commons

from ivk.global_log import GlobalLog
from ivk.log_db import DbLog
from ivk import config

class RokotTmi:
    '''
    AMQP параметры формата:
    {
        'amqp_ip': '192.168.3.87',
        'amqp_port' : 5672,
        'amqp_virtual_host': '505', #'/' for default
        'amqp_user': 'guest',
        'amqp_password': 'guest',
        'amqp_queue' : 'RCD',
        'amqp_queue_params' : {'x-max-length' : 10}
    }
    '''
    amqp_config = None
    amqp_connection = None
    amqp_channel = None

    db_connection = None


    @staticmethod
    def init(amqp_config):
        RokotTmi.amqp_config = amqp_config
        try:
            #Параметры AMQP соединения
            parameters = pika.ConnectionParameters(
                amqp_config['amqp_ip'],
                amqp_config['amqp_port'],
                amqp_config['amqp_virtual_host'], 
                pika.PlainCredentials(amqp_config['amqp_user'], amqp_config['amqp_password'])
            )
            parameters.heartbeat = 0
            RokotTmi.amqp_connection = pika.BlockingConnection(parameters)
            RokotTmi.amqp_channel = RokotTmi.amqp_connection.channel()
            RokotTmi.amqp_channel.queue_declare(amqp_config['amqp_queue'], arguments=amqp_config['amqp_queue_params'])
            RokotTmi.amqp_channel.queue_purge(amqp_config['amqp_queue'])

            GlobalLog.log(threading.get_ident(), 'ROKOT', 'Подключено к AMQP серверу (%s:%d), создана и очищена очередь: %s\n' % (
                amqp_config['amqp_ip'],
                amqp_config['amqp_port'],
                amqp_config['amqp_queue']
            ), False)

        except Exception as exc:
            GlobalLog.log(threading.get_ident(), 'ROKOT', 'Не удалось подключиться к AMQP серверу: %s\n' % repr(exc), True)
        
        try:
            RokotTmi.connectDb()
            if config.getConf('rokot_use_log_database'):
                GlobalLog.log(threading.get_ident(), 'ROKOT', 'Подключено к локальной БД\n', False)
            else:
                GlobalLog.log(threading.get_ident(), 'ROKOT', 'Подключено к PostgreSQL серверу (%s:%d)\n' % (config.getConf("rokot_db_ip"), config.getConf("rokot_db_port")), False)
        except Exception as exc:
            if config.getConf('rokot_use_log_database'):
                GlobalLog.log(threading.get_ident(), 'ROKOT', 'Не удалось подключиться к локальной БД - %s\n' % repr(exc), True)
            else:
                GlobalLog.log(threading.get_ident(), 'ROKOT', 'Не удалось подключиться к PostgreSQL серверу: %s - %s\n' % (config.getConf("rokot_db_ip"), repr(exc)), True)
    
    @staticmethod
    def sendTmi(data):
        if RokotTmi.amqp_channel:
            RokotTmi.amqp_channel.basic_publish(exchange='', routing_key=RokotTmi.amqp_config['amqp_queue'], body=data)

    #Выполняется из pydev процесса, не использовать переменные ui-процесса, выбрасывать исключения
    @staticmethod
    def connectDb():
        if RokotTmi.db_connection is not None and not RokotTmi.db_connection.closed:
            RokotTmi.db_connection.close()
        if config.getConf('rokot_use_log_database'):
            host = config.getConf("log_db_ip")
            port = config.getConf("log_db_port")
            db = config.getConf("log_db_name")
            user = config.getConf("log_db_user")
            password = config.getConf("log_db_password")
        else:
            host = config.getConf("rokot_db_ip")
            port = config.getConf("rokot_db_port")
            db = config.getConf("rokot_db_name")
            user = config.getConf("rokot_db_user")
            password = config.getConf("rokot_db_password")
            
        if host is None or port is None or db is None or user is None or password is None:
            raise Exception("Не удалость получить параметры подключения к БД РОКОТ из конфигурации")
        RokotTmi.db_connection = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)


    #Выполняется из pydev процесса, не использовать переменные ui-процесса, выбрасывать исключения
    #value_type == 'КАЛИБР ТЕКУЩ', 'КАЛИБР ИНТЕРВАЛ', 'НЕКАЛИБР ТЕКУЩ', 'НЕКАЛИБР ИНТЕРВАЛ'
    @staticmethod
    def getTmi(param_name, value_type):
        if value_type not in ('КАЛИБР ТЕКУЩ', 'КАЛИБР ИНТЕРВАЛ', 'НЕКАЛИБР ТЕКУЩ', 'НЕКАЛИБР ИНТЕРВАЛ'):
            raise Exception('Выбран неизвестный тип получаемых данных "%s"' % value_type)
        RokotTmi.connectDb()
        tmsid = config.getData('rokot_current_tmsid')
        if tmsid is None:
            raise Exception("Не выбран сеанс для получения данных ТМИ")
        cur = RokotTmi.db_connection.cursor()
        # if 'ТЕКУЩ' in value_type and isinstance(param_name, (list, tuple, set)):
        #     # TODO: вторая реализация использовать getTmis()
        #     cur.execute("SELECT * FROM "
        #                 "(SELECT value, tmid, ROW_NUMBER() OVER (PARTITION BY value->>'name' ORDER BY tmid DESC) "
        #                 "FROM tm WHERE tmsid = %s AND value->>'name' IN %s "
        #                 "ORDER BY tmid DESC) AS tb "
        #                 "WHERE tb.ROW_NUMBER = 1;", (tmsid, tuple(param_name)))
        #     res = {}
        #     for cyph in param_name:
        #         res[cyph] = None
        #     for row in cur:
        #         config.updData("%d_%s" % (threading.get_ident(), row[0]['name']), row[0]['value'])
        #         res[row[0]['name']] = row[0]['value'] if 'НЕКАЛИБР' in value_type else row[0]['calibrated_value']
        if 'ТЕКУЩ' in value_type:
            cur.execute("SELECT value, tmid FROM tm WHERE tmsid = %s AND value->>'name' = %s ORDER BY tmid DESC", (tmsid, param_name))
            res = cur.fetchone()
            if res is not None:
                config.updData("%d_%s" % (threading.get_ident(), param_name), res[1])
                res = res[0]['value'] if 'НЕКАЛИБР' in value_type else res[0]['calibrated_value']
            else:
                res = None
        else:
            last_tmid = config.getData("%d_%s" % (threading.get_ident(), param_name))
            if last_tmid is None:
                raise Exception('Не удалось обнаружить предыдущий запрос параметра "%s"' % param_name)
            cur.execute("SELECT value FROM tm WHERE tmsid = %s AND tmid > %s AND value->>'name' = %s ORDER BY tmid ASC", (tmsid, last_tmid, param_name))
            res = []
            for row in cur:
                res.append(row[0]['value'] if 'НЕКАЛИБР' in value_type else row[0]['calibrated_value']) 
        cur.close()
        return res

    #Выполняется из pydev процесса, не использовать переменные ui-процесса, выбрасывать исключения
    #params = {'name1' : 'КАЛИБР', 'name2' : 'НЕКАЛИБР', ...}
    @staticmethod
    def getTmis(params, field_name=None):
        res = {}
        for param_name, value_type in params.items():
            if value_type not in ('КАЛИБР', 'НЕКАЛИБР'):
                raise Exception('Выбран неизвестный тип получаемых данных "%s"' % value_type)
            if field_name == 'ИНТЕРВАЛ':
                res[param_name] = []
            else:
                res[param_name] = None
        RokotTmi.connectDb()
        tmsid = config.getData('rokot_current_tmsid')
        if tmsid is None:
            raise Exception("Не выбран сеанс для получения данных ТМИ")

        if field_name == 'ИНТЕРВАЛ':
            query = "SELECT value, tmid FROM tm WHERE tmsid = %s AND (" % tmsid
            tmp_query = []
            for param_name in params.keys():
                last_tmid = config.getData("%d_%s" % (threading.get_ident(), param_name))
                if last_tmid is None:
                    raise Exception('Не удалось обнаружить предыдущий запрос параметра "%s"' % param_name)
                tmp_query.append("(tmid > %s AND value->>'name' = '%s')" % (last_tmid, param_name))
            query += ' OR '.join(tmp_query) + ") ORDER BY tmid ASC"
        else:
            query = "SELECT DISTINCT ON(tmparamsid) value, tmid FROM tm " \
                    "WHERE tmsid = %s AND value->>'name' IN %s " \
                    "ORDER BY tmparamsid, tmid DESC " % (tmsid, str(tuple(params.keys())).replace(',)', ')'))

        cur = RokotTmi.db_connection.cursor()
        cur.execute(query)
        for row in cur:
            config.updData("%d_%s" % (threading.get_ident(), row[0]['name']), row[1])

            ##################### DEBUG
            # if field_name != 'ИНТЕРВАЛ':
            #     config.updData("%d_%s" % (threading.get_ident(), row[0]['name']), 648681700)
            # print("%d_%s = %s" % (threading.get_ident(), row[0]['name'],
            #       config.getData("%d_%s" % (threading.get_ident(), row[0]['name']))))

            value = row[0]['value'] if 'НЕКАЛИБР' in params[row[0]['name']] else row[0]['calibrated_value']
            if field_name == 'ИНТЕРВАЛ':
                res[row[0]['name']].append(value)
            else:
                res[row[0]['name']] = value
        cur.close()
        return res

    #Выполняется из pydev процесса, не использовать переменные ui-процесса, выбрасывать исключения
    @staticmethod
    def putTmi(name, value):
        if not config.getConf('rokot_allow_tmi_insert'):
            raise Exception("Запись ТМИ запрещена в настройках")
        RokotTmi.connectDb()
        tmsid = config.getData('rokot_current_tmsid')
        if tmsid is None:
            raise Exception("Не выбран сеанс для записи ТМИ") 
        #Для колонок jsonb
        from psycopg2.extensions import register_adapter
        register_adapter(dict, psycopg2.extras.Json)

        cur = RokotTmi.db_connection.cursor()
        if config.getConf('rokot_use_log_database'):
            cur.execute('SELECT MAX(tmid) AS last_id FROM tm')
            last_id = cur.fetchone()
            last_id = 0 if last_id is None else last_id[0]
            cur.execute('INSERT INTO tm ("tmid", "tmsid", "time", "value", "tmparamsid", "framenumber", "tlmspeed", "UNCALIB_dk", "UNCALIB_dkw", "CALIB_dk", "CALIB_dkw") VALUES (%s, %s, 0, %s, 0, 0, 0, FALSE, FALSE, FALSE, FALSE)', [
                last_id + 1,
                tmsid, 
                {'mode' : 'НП IVK-TEST', 'name' : name, 'value' : value, 'calibrated_value' : value}
            ])
        else:
            cur.execute('INSERT INTO tm ("tmsid", "time", "value", "tmparamsid", "framenumber", "tlmspeed", "UNCALIB_dk", "UNCALIB_dkw", "CALIB_dk", "CALIB_dkw") VALUES (%s, 0, %s, 0, 0, 0, FALSE, FALSE, FALSE, FALSE)', [
                tmsid, 
                {'mode' : 'НП IVK-TEST', 'name' : name, 'value' : value, 'calibrated_value' : value}
            ])
        RokotTmi.db_connection.commit()
        cur.close()
        pass
    
    @staticmethod
    def getKAs():
        try:
            RokotTmi.connectDb()
        except:
            return None
        cur = RokotTmi.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT k00id, Название, Индекс FROM k00")
        res = cur.fetchall()
        cur.close()
        return res
    
    @staticmethod
    def getSessions(k00id):
        try:
            RokotTmi.connectDb()
        except:
            return None
        cur = RokotTmi.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT tmsid, date FROM tms WHERE scid = %s ORDER BY tmsid DESC", (k00id,))
        res = cur.fetchall()
        cur.close()
        return res

    @staticmethod
    def getAdditionalCommands():
        default_umn = config.getConf("rokot_default_ka_umn")
        kas = RokotTmi.getKAs()
        if kas is None:
            return []

        scid = None
        for ka in kas:
            if default_umn and ka['Индекс'] == default_umn:
                scid = ka['k00id']
                break
        if scid is None:
            raise Exception("Не удалось получить ИД КА для чтения списка параметров ТМИ")

        msg_fields_get = config.odict()
        msg_fields_wait = config.odict()
        cur = RokotTmi.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT name FROM tmparams WHERE scid = %s and deleted=false", (scid,))
        for c in cur:
            msg_fields_get[c['name']] = ['КАЛИБР ТЕКУЩ', 'КАЛИБР ИНТЕРВАЛ', 'НЕКАЛИБР ТЕКУЩ', 'НЕКАЛИБР ИНТЕРВАЛ']
            msg_fields_wait[c['name']] = ['КАЛИБР', 'НЕКАЛИБР']
        cur.close()

        commands = []
        commands.append({
            'name' : '{GET}',
            'import_string' : 'from ivk.rokot_tmi import RokotTmi',
            'description' : 'Получить параметр из ТМИ. Используется для получения значение определенных параметров ТМИ из БД. ВНИМАНИЕ, для работы команд категории ТМИ необходимо выбрать сеанс ТМИ в окне "Телеметрия ROKOT"\nПараметры:\n' + \
                            '  - msg_name(str): ИД параметра ТМИ,\n' + \
                            "  - field_name(str): тип значения параметра ('КАЛИБР ТЕКУЩ', 'КАЛИБР ИНТЕРВАЛ', 'НЕКАЛИБР ТЕКУЩ', 'НЕКАЛИБР ИНТЕРВАЛ')",
            'example' : '''#Получить калиброванное значение поля 'Кадр'
val = Ex.get('ТМИ', 'Кадр', 'КАЛИБР ТЕКУЩ')
#Получить некалиброванное значение поля 'синхромаркер'
val = Ex.get('ТМИ', 'синхромаркер', 'НЕКАЛИБР ТЕКУЩ')
#Получить список некалиброванных значений поля 'синхромаркер'
#c момента последнего запроса
values = Ex.get('ТМИ', 'синхромаркер', 'НЕКАЛИБР ИНТЕРВАЛ')''',
            'msg_fields' : msg_fields_get,
            'translation' : 'Получить ТМИ',
            'cat' : 'ТМИ',
            'cat_description' : 'Команды категории "ТМИ" позволяют получать данные из телеметрической БД.',
            'queues' : ['ТМИ'],
            'ex_send' : False, 
            'is_function' : False
        })
        commands.append({
            'name' : '{WAIT}',
            'import_string' : 'from ivk.rokot_tmi import RokotTmi',
            'description' : 'Ожидание значений параметров из ТМИ. Используется для ожидания наступления определенного события. Возвращает результат (событие наступило или вышло время ожидания). ВНИМАНИЕ, для работы команд категории ТМИ необходимо выбрать сеанс ТМИ в окне "Телеметрия ROKOT"\nПараметры:\n' + \
                            '  - expression(str): выражение для ожидания, можно использовать любые логические конструкции Python (and, or, not, ==, >=, <=, >, <, !=), группировку скобками и имена параметров в формате {ИД_ПАРАМЕТРА.ТИП_ЗНАЧЕНИЯ},\n' + \
                            '  - timeout(float): максимальное время ожидания в секундах',
            'example' : '''#Ожидание CLCW.КАЛИБР > 3.1 или tlmWorkMode.НЕКАЛИБР >= 0,
#при том что синхромаркер.КАЛИБР < 1.2, с таймаутом 14 сек
res = Ex.wait('ТМИ', '({CLCW.КАЛИБР} > 3.1 or {tlmWorkMode.НЕКАЛИБР} >= 0) 
    and {синхромаркер.КАЛИБР} < 1.2', 14)
#Ожидание ИОК_БРК.КАЛИБР != 1 и ИОК_БЦКОСН.НЕКАЛИБР >= 4, с таймаутом 31.5 сек
res = Ex.wait('ТМИ', '{ИОК_БРК.КАЛИБР} != 1 and {ИОК_БЦКОСН.НЕКАЛИБР} >= 4', 31.5)''',
            'msg_fields' : msg_fields_wait,
            'default_timeout' : 20,
            'translation' : 'Ожидание ТМИ',
            'cat' : 'ТМИ',
            'cat_description' : 'Команды категории "ТМИ" позволяют получать данные из телеметрической БД.',
            'queues' : ['ТМИ'],
            'ex_send' : False, 
            'is_function' : False
        })
        if config.getConf('rokot_allow_tmi_insert'):
            commands.append({
                'name' : 'RokotTmi.putTmi',
                'import_string' : 'from ivk.rokot_tmi import RokotTmi',
                'description' : 'Добавляет в БД ТМИ запись с указанным именем параметра и значением (одинаковое значение для КАЛИБР/НЕКАЛИБР). ВНИМАНИЕ, для работы команд категории ТМИ необходимо выбрать сеанс ТМИ в окне "Телеметрия ROKOT". Использовать только для тестовых ПК вне МИКа',
                'example' : '''#ИСПОЛЬЗОВАТЬ ТОЛЬКО ДЛЯ ТЕСТОВВЫХ ПК ВНЕ МИКа
#Запись параметров в БД ТМИ
RokotTmi.putTmi('CLCW', 2.5)
RokotTmi.putTmi('tlmWorkMode', 0x6f55)''',
                'params' : ['name', 'value'],
                'values' : ["'Имя параметра'", '0'],
                'keyword' : [False, False],
                'translation' : "Запись ТМИ",
                'cat' : 'ТМИ',
                'cat_description' : 'Команды категории "ТМИ" позволяют получать данные из телеметрической БД.',
                'queues' : ['ТМИ'],
                'ex_send' : False
            })

        return commands

    @staticmethod
    def copyToLogDb():
        if config.getConf('rokot_use_log_database'):
            Commons.WarningBox('Ошибка копирования в локальную БД', 'В качестве БД ТМИ используется локальная БД, копирование данных ТМИ невозможно')
            return
        try:
            connected = DbLog.connectDb(raise_exceptions=True)
            if not connected:
                Commons.WarningBox('Ошибка копирования в локальную БД', 'Подключение к локальной БД отключено в настройках, копирование данных ТМИ невозможно')
                return
        except Exception as exc:
            Commons.WarningBox('Ошибка копирования в локальную БД', 'Ошибка подключения к локальной БД: %s' % str(exc))
            return
        try:
            RokotTmi.connectDb()
        except Exception as exc:
            Commons.WarningBox('Ошибка копирования в локальную БД', 'Ошибка подключения к БД ТМИ: %s' % str(exc))
            return

        #Для колонок jsonb
        from psycopg2.extensions import register_adapter
        register_adapter(dict, psycopg2.extras.Json)

        t = threading.Thread(target=RokotTmi.__copyToLogDb, daemon=True)
        t.start()
    @staticmethod
    def __copyToLogDb():
        try:
            #Получаем архитектуру интересующих нас таблиц
            GlobalLog.log(threading.get_ident(), 'ROKOT', "Получение архитектуры таблиц из БД ТМИ ...\n", False)
            tables = config.odict(("k00", None), ("tmparams", None), ("tms", None), ("tm", None))
            for table_name in tables:
                create_columns = []
                insert_columns = []

                cur = RokotTmi.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = %s", (table_name,))
                for c in cur:
                    datatype = c['data_type'] if table_name != "tmparams" or c['column_name'] != "startbyte" else "_int4"
                    create_columns.append("\"%s\" %s %s" % (c['column_name'], datatype, "NOT NULL" if c['is_nullable'] == "NO" else "NULL"))
                    insert_columns.append("\"%s\"" % c["column_name"])
                cur.close()

                tables[table_name] = {
                    'create' : "CREATE TABLE IF NOT EXISTS %s (%s)" % (table_name, ", ".join(create_columns)),
                    'clear' : "DELETE FROM %s" % table_name,
                    'select' : "SELECT %s FROM %s" % (", ".join(insert_columns), table_name),
                    'insert' : "INSERT INTO %s (%s) VALUES (%s)" % (table_name, ", ".join(insert_columns), ", ".join(["%s" for i in range(len(insert_columns))]))
                }
            GlobalLog.log(threading.get_ident(), 'ROKOT', "Успешно получена архитекутра таблиц %s\n" % ", ".join(tables), False)
            time.sleep(2)

            for table_name, statements in tables.items():
                GlobalLog.log(threading.get_ident(), 'ROKOT', "Копирование \"%s\" в локальную БД ...\n" % table_name, False)

                #Создаем / чистим таблицы
                cur = DbLog.db_connection.cursor()
                cur.execute(statements['create'])
                cur.execute(statements['clear'])
                DbLog.db_connection.commit()
                cur.close()

                #Копируем данные
                cur = RokotTmi.db_connection.cursor()
                cur2 = DbLog.db_connection.cursor()

                i = 0
                cur.execute(statements['select'])
                for row in cur:
                    cur2.execute(statements['insert'], row)
                    i += 1
                    if i % 500 == 0:
                        DbLog.db_connection.commit()
                if i % 500 != 0:
                    DbLog.db_connection.commit()
                cur.close()
                cur2.close()

                GlobalLog.log(threading.get_ident(), 'ROKOT', "Копирование успешно завершено\n", False)
        except Exception as exc:
            GlobalLog.log(threading.get_ident(), 'ROKOT', "Ошибка копирования в локальную БД: %s\n" % str(exc), True)
            traceback.print_exc()

            





class RokotWidget(QDockWidget):
    
    def __init__(self, parent, tabs_widget):
        super().__init__(parent)
        self.setWindowTitle('Телеметрия ROKOT')
        self.tabs_widget = tabs_widget

        #Контекстное меню для копирования БД ТМИ в локальную БД
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)

        self.colored_labels = {}
        self.colored_labels_dispatcher_thread = threading.Thread(target=self.dispatchLabelColors, daemon=True)
        self.colored_labels_dispatcher_thread.start()
        self.colored_labels_lock = threading.Lock()

        self.combo_ka = QComboBox()
        self.combo_ka.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_ka.currentIndexChanged.connect(self.updateSessions)
        self.combo_ka_refreshing = False
        
        self.combo_sessions = QComboBox()
        self.combo_sessions.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.combo_sessions.currentIndexChanged.connect(self.setCurrentSession)
        self.combo_sessions_refreshing = False
        
        
        self.tmi_start_time = None
        self.tmi_sent_count = 0
        self.label_tmi_speed = StyledLabel('?', object_name='consolasBoldFont')

        self.button_upd = QPushButton(QIcon('res/refresh.png'), 'Обновить')
        self.button_upd.clicked.connect(self.udateKAs)

        #tmp_edit_name = QLineEdit("ИОК8.0")
        #tmp_edit_type = QLineEdit("КАЛИБР ТЕКУЩ")
        #tmp_btn = QPushButton("TEST")
        #tmp_btn.clicked.connect(lambda: print(RokotTmi.getTmi(tmp_edit_name.text(), tmp_edit_type.text())))
        #.hbox(spacing=5).add(tmp_edit_name).add(tmp_edit_type).add(tmp_btn).stretch().up() \

        self.setWidget(QWidget(self))
        lb = QBoxLayoutBuilder(self.widget(), QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        lb.hbox(spacing=5).add(QLabel("КА")).fixW().add(self.combo_ka).add(QLabel("Сеанс")).fixW().add(self.combo_sessions).add(self.button_upd).fixW().up() \
          .hbox(spacing=5).add(QLabel("Пересылка ТМИ:")).add(self.label_tmi_speed).stretch().up() \
          .stretch()

        self.hide()

    def udateKAs(self):
        self.combo_ka_refreshing = True
        self.combo_ka.clear()
        index_to_select = 0
        try:
            default_umn = config.getConf("rokot_default_ka_umn")
            index_to_select = 0
            kas = RokotTmi.getKAs()
            if kas is not None:
                for ka in kas:
                    self.combo_ka.addItem('%s (%s)' % (ka['Название'], ka['Индекс']), (ka['k00id'], ka['Индекс']))
                    if default_umn and ka['Индекс'] == default_umn:
                        index_to_select = self.combo_ka.count()-1
        except Exception as exc:
            Commons.WarningBox('Ошибка', 'Ошибка обновления списка КА: %s' % repr(exc), self.tabs_widget)
        self.combo_ka_refreshing = False
        if self.combo_ka.count():
            if index_to_select == self.combo_ka.currentIndex():
                self.updateSessions(index_to_select)
            else:
                self.combo_ka.setCurrentIndex(index_to_select)

    def updateSessions(self, combo_ka_index):
        if self.combo_ka_refreshing:
            return
        self.combo_sessions_refreshing = True
        self.combo_sessions.clear()
        if self.combo_ka.count() > 0:
            try:
                k00id, umn = self.combo_ka.itemData(combo_ka_index)
                sessions = RokotTmi.getSessions(k00id)
                for session in sessions:
                    self.combo_sessions.addItem('%d - %s' % (session['tmsid'], session['date'].strftime('%Y.%m.%d %H:%M:%S')), session['tmsid'])
            except Exception as exc:
                Commons.WarningBox('Ошибка', 'Ошибка получения сеансов ТМИ для КА %s: %s' % (umn, repr(exc)), self.tabs_widget)
        self.combo_sessions_refreshing = False
        if self.combo_sessions.count():
            if self.combo_sessions.currentIndex() == 0:
                self.setCurrentSession(0)
            else:
                self.combo_sessions.setCurrentIndex(0)
            
    
    def setCurrentSession(self, combo_sessions_index):
        if not self.combo_sessions_refreshing and self.combo_sessions.count():
            tmsid = self.combo_sessions.itemData(combo_sessions_index)
            config.updData('rokot_current_tmsid', tmsid)
        

    def tmiSent(self):
        self.tmi_sent_count += 1
        if self.tmi_start_time is None:
            self.tmi_start_time = datetime.now()
            return
        total_time = (datetime.now()-self.tmi_start_time).total_seconds()
        if total_time > 10:
            self.tmi_start_time = datetime.now()
            self.tmi_sent_count = 1
        elif total_time > 0:
            self.setLabelText(self.label_tmi_speed, '%.1f пакетов/сек' % (self.tmi_sent_count/total_time,))

    def setLabelText(self, label, text):
        if text != label.text():
            label.setText(text)
            
            self.colored_labels_lock.acquire()
            self.colored_labels[label] = {'dt': datetime.now(), 'colored' : True}
            self.colored_labels_lock.release()
            
            label.setAutoFillBackground(True)
            pal = label.palette()
            pal.setColor(QPalette.Window, QColor('#5effb1'))
            label.setPalette(pal)
    
    def dispatchLabelColors(self):
        while True:
            time.sleep(1)
            self.colored_labels_lock.acquire()
            for label, val in self.colored_labels.items():
                if val['colored'] and (datetime.now() - val['dt']).total_seconds() > 10:
                    val['colored'] = False
                    pal = label.palette()
                    pal.setColor(QPalette.Window, self.palette().color(QPalette.Window))
                    label.setPalette(pal)
            self.colored_labels_lock.release()

    def __showContextMenu(self, pos):
        context_menu = QMenu(self)
        sync_action = QAction(QIcon('res/sync.png'), 'Кобировать БД ТМИ в локальную БД', self)
        sync_action.triggered.connect(RokotTmi.copyToLogDb)
        context_menu.addAction(sync_action)
        context_menu.exec(self.mapToGlobal(pos))

    def showEvent(self, event):
        self.udateKAs()
        print("UPDATE KAs")
        super().showEvent(event)
    
    def closeEvent(self, event):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)
        super().closeEvent(event)

    def saveSettings(self):
        pass
        # return {
        #     'sost_check_state' : self.sost_checkbox.checkState(),
        #     'sopriz_check_state' : self.sopriz_checkbox.checkState(),
        #     'narab_check_state' : self.narab_checkbox.checkState(),
        #     'naprtlm_check_state' : self.naprtlm_checkbox.checkState(),
        #     'napr_check_state' : self.napr_checkbox.checkState(),
        #     'tempab_check_state' : self.tempab_checkbox.checkState()
        # }
    
    def restoreSettings(self, settings):
        pass
        # self.sost_checkbox.setCheckState(settings['sost_check_state'])
        # self.sopriz_checkbox.setCheckState(settings['sopriz_check_state'])
        # self.narab_checkbox.setCheckState(settings['narab_check_state'])
        # self.naprtlm_checkbox.setCheckState(settings['naprtlm_check_state'])
        # self.napr_checkbox.setCheckState(settings['napr_check_state'])
        # self.tempab_checkbox.setCheckState(settings['tempab_check_state'])
        
    def settingsKeyword(self):
        return 'RokotWidget'
    
    def getMenuParams(self):
        return {
            'icon' : 'res/tmi_icon.png',
            'text' : 'Телеметрия ROKOT',
            'status_tip' : 'Окно мониторинга телеметрии из ROKOT'
        }
