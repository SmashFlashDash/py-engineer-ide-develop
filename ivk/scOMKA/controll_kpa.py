import struct, ctypes
from cpi_framework.utils.BinaryStream import BinaryStreamBE
from ivk import config
# import buff

from ivk.rokot_tmi import RokotTmi
from ivk.scOMKA.networkingTools import Buffer


class KPA:
    MESSAGES_TO_KPA = config.odict(

        ('Соединение', {'id': 100,
                        'description': 'Установить соединение с ИВК (для получения сообщений по UDP)',
                        'data': None}),

        # Управление КПА СЗД
        ('КПА_СЗД-откл', {'id': 1500,
                          'description': 'Отключить обмен с КПА СЗД',
                          'data': None}),
        ('КПА_СЗД-имит', {'id': 1501,
                          'description': 'Имитировать обмен с КПА СЗД',
                          'data': None}),
        ('КПА_СЗД-вкл', {'id': 1502,
                         'description': 'Включить обмен с КПА СЗД',
                         'data': None}),
        ('КПА_М694-У', {'id': 1503,
                        'description': 'Включить обмен с М-694У',
                        'data': None}),

        # Управление МКПД
        ('МКПД-откл', {'id': 1700,
                       'description': 'Отключить линии "А" и "В" МКПД',
                       'data': None}),
        ('МКПД-А', {'id': 1701,
                    'description': 'Включить только линию "А" МКПД',
                    'data': None}),
        ('МКПД-В', {'id': 1702,
                    'description': 'Включить только линию "В" МКПД',
                    'data': None}),
        ('МКПД-АВ', {'id': 1703,
                     'description': 'Включить линии "А" и "В" МКПД',
                     'data': None}),
        ('МКПД-ПК', {'id': 1704,
                     'description': 'Отправить указанную ПК по МКПД.\nПараметры:\n' + \
                                    '  - data(bytes): данные ПК',
                     'data': {'len': 16,
                              'type': bytes,
                              'check': None,
                              'default': "bytes([0 for i in range(16)])"}
                     }),

        # Управление декодером канала "вниз"
        ('Скорость-16', {'id': 800,
                         'description': 'Установить скорость декодера ПРМ КПА на 16 кбит/с',
                         'data': None}),
        ('Скорость-32', {'id': 801,
                         'description': 'Установить скорость декодера ПРМ КПА на 32 кбит/с',
                         'data': None}),
        ('Скорость-300', {'id': 802,
                          'description': 'Установить скорость декодера ПРМ КПА на 300 кбит/с',
                          'data': None}),
        ('Скорость-600', {'id': 803,
                          'description': 'Установить скорость декодера ПРМ КПА на 600 кбит/с',
                          'data': None}),

        # Управление имитаторами М-694
        ('М-694-1-ОИ-откл', {'id': 1600,
                             'description': 'Отключить канал ОИ имитатора М-694 №1',
                             'data': None}),
        ('М-694-1-ОИ-вкл', {'id': 1601,
                            'description': 'Включить канал ОИ имитатора М-694 №1',
                            'data': None}),
        ('М-694-1-ЗИ-откл', {'id': 1602,
                             'description': 'Отключить канал ЗИ имитатора М-694 №1',
                             'data': None}),
        ('М-694-1-ЗИ-вкл', {'id': 1603,
                            'description': 'Включить канал ЗИ имитатора М-694 №1',
                            'data': None}),
        ('М-694-2-ОИ-откл', {'id': 1604,
                             'description': 'Отключить канал ОИ имитатора М-694 №2',
                             'data': None}),
        ('М-694-2-ОИ-вкл', {'id': 1605,
                            'description': 'Включить канал ОИ имитатора М-694 №2',
                            'data': None}),
        ('М-694-2-ЗИ-откл', {'id': 1606,
                             'description': 'Отключить канал ЗИ имитатора М-694 №2',
                             'data': None}),
        ('М-694-2-ЗИ-вкл', {'id': 1607,
                            'description': 'Включить канал ЗИ имитатора М-694 №2',
                            'data': None}),
        ('М-694-3-ОИ-откл', {'id': 1608,
                             'description': 'Отключить канал ОИ имитатора М-694 №3',
                             'data': None}),
        ('М-694-3-ОИ-вкл', {'id': 1609,
                            'description': 'Включить канал ОИ имитатора М-694 №3',
                            'data': None}),
        ('М-694-3-ЗИ-откл', {'id': 1610,
                             'description': 'Отключить канал ЗИ имитатора М-694 №3',
                             'data': None}),
        ('М-694-3-ЗИ-вкл', {'id': 1611,
                            'description': 'Включить канал ЗИ имитатора М-694 №3',
                            'data': None}),
        ('М-694-4-ОИ-откл', {'id': 1612,
                             'description': 'Отключить канал ОИ имитатора М-694 №4',
                             'data': None}),
        ('М-694-4-ОИ-вкл', {'id': 1613,
                            'description': 'Включить канал ОИ имитатора М-694 №4',
                            'data': None}),
        ('М-694-4-ЗИ-откл', {'id': 1614,
                             'description': 'Отключить канал ЗИ имитатора М-694 №4',
                             'data': None}),
        ('М-694-4-ЗИ-вкл', {'id': 1615,
                            'description': 'Включить канал ЗИ имитатора М-694 №4',
                            'data': None}),

        # Управление источником питания
        ('Питание-откл', {'id': 1300,
                          'description': 'Отключить питание БА КИС-Р',
                          'data': None}),
        ('Питание-вкл', {'id': 1301,
                         'description': 'Включить питание БА КИС-Р',
                         'data': None}),
        ('Питание-норм', {'id': 1302,
                          'description': 'Установить напряжение питание БА КИС-Р в 27 В',
                          'data': None}),
        ('Питание++', {'id': 1303,
                       'description': 'Увеличить напряжение питания БА КИС-Р на 1 В',
                       'data': None}),
        ('Питание--', {'id': 1304,
                       'description': 'Уменьшить напряжение питания БА КИС-Р на 1 В',
                       'data': None}),

        # Управление кодером канала "вверх"
        ('ЗК-квит.', {'id': 700,
                      'description': 'Режим отправки кадров с квитированием',
                      'data': None}),
        ('ЗК-обход', {'id': 701,
                      'description': 'Режим отправки кадров с флагом обхода',
                      'data': None}),
        ('ИДКА-уст.', {'id': 702,
                       'description': 'Установить указанный ИД КА.\nПараметры:\n' + \
                                      '  - data(int): ИД КА для установки',
                       'data': {'len': 2,
                                'type': int,
                                'check': lambda ka_id: ka_id >= 0 and ka_id <= 65535,
                                'check_msg': 'ИД КА должен находиться в диапазоне от 0 до 65535',
                                'default': '1'}
                       }),

        # Управление модулятором канала "вверх"
        ('Модуляция-откл', {'id': 600,
                            'description': 'Отключить модуляцию (режим "несущая")',
                            'data': None}),
        ('Модуляция-меандр', {'id': 601,
                              'description': 'Модуляция данными "все 0"',
                              'data': None}),
        ('Модуляция-данные', {'id': 602,
                              'description': 'Модуляция данными',
                              'data': None}),
        ('Модуляция-дальн.', {'id': 603,
                              'description': 'Модуляция сигналом дальнометрии',
                              'data': None}),
        ('Модуляция-совм.', {'id': 604,
                             'description': 'Модуляция сигналом дальнометрии и данными',
                             'data': None}),

        # Управление обменом
        ('Отпр-ЗК', {'id': 750,
                     'description': 'Отправить указанный ЗК по радиоканалу.\nПараметры:\n' + \
                                    '  - data(bytes): данные ЗК',
                     'data': {'len': 114,
                              'type': bytes,
                              'check': None,
                              'default': 'bytes([0 for i in range(114)])'}
                     }),
        ('Отпр-КПИ', {'id': 751,
                      'show': False,
                      'description': 'Отправить указанные данные КПИ по радиоканалу',
                      'data': {'len': 64,
                               'type': bytes,
                               'check': None}
                      }),
        ('Отпр-РКо', {'id': 752,
                      'show': False,
                      'description': 'Отправить указанный РКо по радиоканалу',
                      'data': {'len': 16,
                               'type': bytes,
                               'check': None}
                      }),
        ('Отпр-РКз', {'id': 753,
                      'show': False,
                      'description': 'Отправить указанный РКз по радиоканалу',
                      'data': {'len': 16,
                               'type': bytes,
                               'check': None}
                      }),

        # Управление сквозным тестированием
        ('КПИ-тест-откл', {'id': 2000,
                           'description': 'Отключить выдачу тестовой КПИ по радиоканалу',
                           'data': None}),
        ('КПИ-тест-вкл', {'id': 2001,
                          'description': 'Включить выдачу тестовой КПИ по радиоканалу',
                          'data': None}),
        ('ОК-тест-откл', {'id': 2002,
                          'description': 'Отключить выдачу тестовых данных БЦК по МКПД',
                          'data': None}),
        ('ОК-тест-вкл', {'id': 2003,
                         'description': 'Включить выдачу тестовых данных БЦК по МКПД',
                         'data': None}),

        # Управление трансивером
        ('Отпр-старт', {'id': 754,
                        'description': 'Установка признака стартового кадра',
                        'data': None}),
        ('Литера-1', {'id': 500,
                      'description': 'Установить частотную литеру №1',
                      'data': None}),
        ('Литера-2', {'id': 501,
                      'description': 'Установить частотную литеру №2',
                      'data': None}),
        ('Литера-3', {'id': 502,
                      'description': 'Установить частотную литеру №3',
                      'data': None}),
        ('Литера-4', {'id': 503,
                      'description': 'Установить частотную литеру №4',
                      'data': None}),
        ('Литера-5', {'id': 504,
                      'description': 'Установить частотную литеру №5',
                      'data': None}),
        ('Литера-6', {'id': 505,
                      'description': 'Установить частотную литеру №6',
                      'data': None}),
        ('Литера-7', {'id': 506,
                      'description': 'Установить частотную литеру №7',
                      'data': None}),
        ('Литера-8', {'id': 507,
                      'description': 'Установить частотную литеру №8',
                      'data': None}),
        ('ПРД-1', {'id': 508,
                   'description': 'Переключить ПРД КПА на выход №1',
                   'data': None}),
        ('ПРД-2', {'id': 509,
                   'description': 'Переключить ПРД КПА на выход №2',
                   'data': None}),
        ('ПРМ-1', {'id': 510,
                   'description': 'Переключить ПРМ КПА на вход №1',
                   'data': None}),
        ('ПРМ-2', {'id': 511,
                   'description': 'Переключить ПРМ КПА на вход №2',
                   'data': None}),
        ('Мощность-ниж', {'id': 512,
                          'description': 'Установить уровень сигнала ПРД КПА в нижнее значение',
                          'data': None}),
        ('Мощность-верх', {'id': 513,
                           'description': 'Установить уровень сигнала ПРД КПА в верхнее значение',
                           'data': None}),
        ('Мощность++', {'id': 514,
                        'description': 'Увеличить уровень сигнала ПРД КПА на 0,5 дБ',
                        'data': None}),
        ('Мощность--', {'id': 515,
                        'description': 'Уменьшить уровень сигнала ПРД КПА на 0,5 дБ',
                        'data': None}),
        ('Мощность-уст', {'id': 516,
                          'description': 'Установить указанный уровень сигнала ПРД КПА.\nПараметры:\n' + \
                                         '  - data(int - передавать как float): уровень сигнала ПРД\n' +
                                         '\tфактически КПА устанавливает только четные значениея [-60, -84], нечетные [-85, -109]',
                          'data': {'len': 4,
                                   'type': float,
                                   # TODO: КПА реагирует только на float значения четные [-60, -84] нечетные, [-85, -109]
                                   # должны быть только интовые значениея dbm >= -109 and dbm <= -60
                                   'check': lambda dbm: tuple(range(-109, -60 + 1)).__contains__(dbm),
                                   'check_msg': 'Уровень выходного сигнала должен находиться в диапазоне от -109 до -60 дБм',
                                   'default': '-100.0'}
                          }),
        ('Частота-центр', {'id': 517,
                           'description': 'Установить смещение частоты ПРД КПА в 0',
                           'data': None}),
        ('Частота++', {'id': 518,
                       'description': 'Увеличить частоту ПРД КПА на 100 Гц',
                       'data': None}),
        ('Частота--', {'id': 519,
                       'description': 'Уменьшить частоту ПРД КПА на 100 Гц',
                       'data': None}),
        ('Частота-уст', {'id': 520,
                         'description': 'Установить указанное смещение частоты ПРД КПА.\nПараметры:\n' + \
                                        '  - data(float): смещение частоты ПРД',
                         'data': {'len': 4,
                                  'type': float,
                                  'check': lambda freq: freq >= -100000.0 and freq <= 100000.0,
                                  'check_msg': 'Смещение частоты должно находиться в диапазоне от -100000 до 100000 Гц',
                                  'default': '50000.0'}
                         }),
        ('Команда-абонент',
         {
             'id': 1400,
             'description': 'Отправка в М-694У произвольной команды по абонентской линии',
             'data':
                 {
                     'type': bytes,
                     'check': None,
                     'default': "AsciiHex('0x0000000000000000000000000000').bytes"
                 }
         }
         ),
        ('Команда-канал',
         {
             'id': 1401,
             'description': 'Отправка в М-694У произвольной команды по канальной линии',
             'data':
                 {
                     'type': bytes,
                     'check': None,
                     'default': "AsciiHex('0x0000000000000000000000000000').bytes"
                 }
         }
         ),
        ('Установка-ключа',
         {
             'id': 1402,
             'description': 'Отправка в М-694У команды установки ключа',
             'data':
                 {
                     'type': bytes,
                     'check': None,
                     'default': "AsciiHex('0x00000000000000000000').bytes"
                 }
         }
         ),
        ('Удаление-ключа',
         {
             'id': 1403,
             'description': 'Отправка в М-694У команды удаления ключа',
             'data':
                 {
                     'type': bytes,
                     'check': None,
                     'default': "AsciiHex('0x00000000000000000000').bytes"
                 }
         }
         ),
        ('Удаление-ключей',
         {
             'id': 1404,
             'description': 'Отправка в М-694У команды удаления всех ключей',
             'data':
                 {
                     'type': bytes,
                     'check': None,
                     'default': "AsciiHex('0x00000000000000000000').bytes"
                 }
         }
         )
    )

    def __init__(self, name, data=None):
        msg = None
        if isinstance(name, str) and name in KPA.MESSAGES_TO_KPA:
            msg = KPA.MESSAGES_TO_KPA[name]
        elif isinstance(name, int):
            for k, v in KPA.MESSAGES_TO_KPA.items():
                if v['id'] == name:
                    name = k
                    msg = KPA.MESSAGES_TO_KPA[name]
                    break
        if msg is None:
            raise Exception('Неопознанный код команды "%s"' % str(name))

        if msg['data']:
            if data is None:
                raise Exception('Для команды "%s" необходимо задать данные' % name)
            if not isinstance(data, msg['data']['type']):
                raise Exception('Неверный тип данных для команды "%s"' % name)
            if msg['data']['check'] and not msg['data']['check'](data):
                raise Exception(msg['data']['check_msg'])
            if msg['data']['type'] == bytes and 'len' in msg['data'].keys() and len(data) != msg['data']['len']:
                raise Exception('Необходимо %d байт данных (передано %d)' % (msg['data']['len'], len(data)))

            # КОСТЫЛЬ ПРВОЕРИТЬ РАБОТАЕТ ЛИ ИНТ команда id 516 дргими данными
            # при type float
            # if  msg['id'] == 516:
            #     data = struct.pack('>i', int(data))     # >i >h >l не берет типы
            if msg['data']['type'] == float:
                data = struct.pack('>f' if msg['data']['len'] == 4 else '>d', data)
            elif msg['data']['type'] == int:
                data = struct.pack('>H' if msg['data']['len'] == 2 else ('>I' if msg['data']['len'] == 4 else '>Q'),
                                   data)

        self.msg = msg
        self.name = name
        self.stream = KPA.Wrap(msg['id'], data)

    @staticmethod
    def Wrap(msg_type, data):

        packet = struct.pack(">H", msg_type)
        packet += struct.pack(">I", 0)
        packet += struct.pack(">H", len(data) if data else 0)
        if data:
            packet += data
        return packet


# class bufferKPAtcp():
#     data = bytearray()
#
#     @staticmethod
#     def Extend(newBytes):
#         bufferKPAtcp.data.extend(newBytes)
#
#     @staticmethod
#     def ClearBuf():
#         bufferKPAtcp.data = bytearray()
#
#     @staticmethod
#     def Length():
#         return len(bufferKPAtcp.data)


class KPAResponce:
    RESPONCES_FROM_KPA = {
        'ДИ_КПА': {
            'msg_type': 57360,
            'get_responce_class': lambda: IDKPA()
        },
        'ОК_ПОЛН': {
            'msg_type': 17000
        },
        'ОК_ОБР': {
            'msg_type': 57344
        },
        'ДИ_МКПД': {
            'msg_type': 57345
        }
    }

    def __init__(self, protocol=None, msg=None):
        self.protocol = protocol
        if msg is not None and len(msg) >= 8:
            print('Байт для обработки: ', len(msg))
            self.msg_type, self.ident, self.data_len = struct.unpack(">HIH", msg[:8])
            self.data = msg[8:]
            self.unpacked = None
            self.msg_name = None
            for name, msg in KPAResponce.RESPONCES_FROM_KPA.items():
                if msg['msg_type'] == self.msg_type:
                    self.msg_name = name
                    if 'get_responce_class' in msg:
                        self.unpacked = msg['get_responce_class']()
                        self.unpacked.fromStream(self.data)
                    break
        else:
            self.msg_type = None
            self.ident = None
            self.data_len = len(msg) if msg is not None else None
            self.data = msg if msg is not None else None
            self.unpacked = None
            self.msg_name = None

    def dataString(self):
        return '[%s]' % ', '.join(['%d' % (b,) for b in self.data]) if self.msg_type else 'empty msg'

    def msgString(self):
        if self.msg_type:
            print("msg_type : %d, ident: %d, data_len: %d, data: %s" % (
                self.msg_type, self.ident, self.data_len, self.dataString()))
        else:
            print("empty msg")

    def onData(self):
        # ДИ_КПА
        if self.msg_name == 'ДИ_КПА':
            if self.unpacked:
                config.updData('kpa_' + self.msg_name, self.unpacked.toDict())
            else:
                print('[%s] ДИ_КПА %d не распакован -> %s' % (self.protocol, len(self.data), self.data.hex()))
        # ДИ_МКПД
        elif self.msg_name == 'ДИ_МКПД':
            print("[%s] ДИ-МКПД %d -> %s" % (self.protocol, len(self.data), self.data.hex()))
        # ОК_ПОЛН
        elif self.msg_name == 'ОК_ПОЛН':
            print("[%s] ОК_ПОЛН %d" % (self.protocol, len(self.data)))
        # ОК_ОБР
        elif self.msg_name == 'ОК_ОБР':
            if len(self.data) == 1279:
                RokotTmi.sendTmi(self.data)
                config.get_exchange().rokot_widget.tmiSent()
                if config.get_exchange().kpa_dock is not None and config.get_exchange().kpa_dock.write_dump:
                    path = config.get_exchange().kpa_dock.dump_file_path
                    path = path.with_name(path.stem + '_' + self.protocol + path.suffix)
                    f = open(str(path), mode='ab')
                    f.write(self.data)
                    f.close()
            print("[%s] ОК_ОБР %d" % (self.protocol, len(self.data)))
        # НЕИЗВЕСТНЫЙ ИД СООБЩЕНИЯ
        elif self.msg_type:
            print("[%s] НЕИЗВЕСТНО(ТИП %d) %d" % (self.protocol, self.msg_type, len(self.data)))
        else:
            print("[%s] НЕКОРРЕКТНОЕ СООБЩЕНИЕ len=%s" % (self.protocol, str(self.data_len)))

    @staticmethod
    def FromRedis(name):
        d = config.getData('kpa_' + name)
        if d:
            resp = KPAResponce()
            resp.msg_name = name
            resp.msg_type = KPAResponce.RESPONCES_FROM_KPA[name]['msg_type']
            resp.unpacked = KPAResponce.RESPONCES_FROM_KPA[name]['get_responce_class']()
            resp.unpacked.fromDict(d)
            return resp
        return None

    @staticmethod
    def GetMsgFieldsDict():
        d = config.odict()
        for name, msg in KPAResponce.RESPONCES_FROM_KPA.items():
            if 'get_responce_class' in msg:
                d[name] = msg['get_responce_class']().getFieldNames()
        return d


bufferKPAtcp = Buffer()


class KPAResponce_TCP:
    RESPONCES_FROM_KPA = {
        'ДИ_КПА': {
            'msg_type': 57360,
            'get_responce_class': lambda: IDKPA(),
            'size': 32  # если старая весрия КПА 33
        },
        'ОК_ПОЛН': {
            'msg_type': 17000,
            'size': 1279
        },
        'ОК_ОБР': {
            'msg_type': 57344,
            'size': 1114
        },
        'ДИ_МКПД': {
            'msg_type': 57345
        }
    }

    def __init__(self, protocol=None, msg=None):
        self.data = None
        self.protocol = protocol
        if msg is not None:
            bufferKPAtcp.Extend(msg)
        self.msg_type = None
        self.ident = None
        self.data_len = None
        self.unpacked = None
        self.msg_name = None
        self.newMsg()

    def newMsg(self):
        if bufferKPAtcp.data is not None and bufferKPAtcp.Length() >= 8:
            self.msg_type, self.ident, self.data_len = struct.unpack(">HIH", bufferKPAtcp.data[:8])
            if bufferKPAtcp.Length() >= self.data_len + 8:
                self.data = bufferKPAtcp.data[8: 8 + self.data_len]
                bufferKPAtcp.data = bufferKPAtcp.data[8 + self.data_len:]
            else:
                self.data = None
            self.unpacked = None
            self.msg_name = None
            for name, msg in KPAResponce.RESPONCES_FROM_KPA.items():
                if msg['msg_type'] == self.msg_type:
                    self.msg_name = name
                    if 'get_responce_class' in msg:
                        self.unpacked = msg['get_responce_class']()
                        self.unpacked.fromStream(self.data)
                    break
            if self.msg_name is None:
                bufferKPAtcp.ClearBuf()
        else:
            self.msg_name = None

    def dataString(self):
        return '[%s]' % ', '.join(['%d' % (b,) for b in self.data]) if self.msg_type else 'empty msg'

    def msgString(self):
        if self.msg_type:
            print("msg_type : %d, ident: %d, data_len: %d, data: %s" % (
                self.msg_type, self.ident, self.data_len, self.dataString()))
        else:
            print("empty msg")

    def onData(self):
        while self.msg_name is not None and self.data is not None:
            # ДИ_КПА
            if self.msg_name == 'ДИ_КПА':
                if self.unpacked:
                    config.updData('kpa_' + self.msg_name, self.unpacked.toDict())
                    print('[%s] ДИ_КПА %d' % (self.protocol, len(self.data)))
                else:
                    print('[%s] ДИ_КПА %d не распакован -> %s' % (
                        self.protocol, len(self.data[:self.data_len]), bufferKPAtcp.data.hex()))
            # ДИ_МКПД
            elif self.msg_name == 'ДИ_МКПД':
                print("[%s] ДИ-МКПД %d -> %s" % (self.protocol, len(self.data), self.data.hex()))
            # ОК_ПОЛН
            elif self.msg_name == 'ОК_ПОЛН':
                RokotTmi.sendTmi(self.data)
                config.get_exchange().rokot_widget.tmiSent()
                if config.get_exchange().kpa_dock is not None and config.get_exchange().kpa_dock.write_dump:
                    path = config.get_exchange().kpa_dock.dump_file_path
                    path = path.with_name(path.stem + '_' + self.protocol + path.suffix)
                    f = open(str(path), mode='ab')
                    f.write(self.data)
                    f.close()
                print("[%s] ОК_ПОЛН %d" % (self.protocol, len(self.data[:self.data_len])))
            # ОК_ОБР
            elif self.msg_name == 'ОК_ОБР':
                RokotTmi.sendTmi(self.data)
                config.get_exchange().rokot_widget.tmiSent()
                if config.get_exchange().kpa_dock is not None and config.get_exchange().kpa_dock.write_dump:
                    path = config.get_exchange().kpa_dock.dump_file_path
                    path = path.with_name(path.stem + '_' + self.protocol + path.suffix)
                    f = open(str(path), mode='ab')
                    f.write(self.data)
                    f.close()
                print("[%s] ОК_ОБР %d" % (self.protocol, self.data_len))
            # НЕИЗВЕСТНЫЙ ИД СООБЩЕНИЯ
            elif self.msg_type:
                print("[%s] НЕИЗВЕСТНО(ТИП %d) %d" % (self.protocol, self.msg_type, len(self.data)))
            else:
                print("[%s] НЕКОРРЕКТНОЕ СООБЩЕНИЕ len=%s" % (self.protocol, str(self.data_len)))
            self.newMsg()
            if self.msg_name is None:
                break

    @staticmethod
    def FromRedis(name):
        d = config.getData('kpa_' + name)
        if d:
            resp = KPAResponce()
            resp.msg_name = name
            resp.msg_type = KPAResponce.RESPONCES_FROM_KPA[name]['msg_type']
            resp.unpacked = KPAResponce.RESPONCES_FROM_KPA[name]['get_responce_class']()
            resp.unpacked.fromDict(d)
            return resp
        return None

    @staticmethod
    def GetMsgFieldsDict():
        d = config.odict()
        for name, msg in KPAResponce.RESPONCES_FROM_KPA.items():
            if 'get_responce_class' in msg:
                d[name] = msg['get_responce_class']().getFieldNames()
        return d


class IDKPA(BinaryStreamBE):
    _fields_ = [
        ('queue_count', ctypes.c_uint8),
        ('letter', ctypes.c_uint8),
        ('receiver_frequency', ctypes.c_float),
        ('receiver_power', ctypes.c_float),
        ('receiver_speed', ctypes.c_uint8),
        ('transmiter_modulation', ctypes.c_uint8),
        ('receiver_input', ctypes.c_uint8),
        ('transmiter_output', ctypes.c_uint8),
        ('ka_id', ctypes.c_uint16),
        ('transmiter_power', ctypes.c_float),
        ('is_receiving', ctypes.c_uint8),
        ('count_msg_from_ivk', ctypes.c_uint8),
        ('last_ivk_msg_number', ctypes.c_uint16),
        ('ka_estimate_range', ctypes.c_float),
        ('ka_estimate_speed', ctypes.c_float)
    ]

    _field_names_ = [
        ('queue_count', 'очередь_ЗК'),
        ('letter', 'литера'),
        ('receiver_frequency', 'отстр_част_ПРМ'),
        ('receiver_power', 'мощн_ПРМ'),
        ('receiver_speed', 'скорость_декод_ПРМ'),
        ('transmiter_modulation', 'модуляц_ПРД'),
        ('receiver_input', 'вход_ПРМ'),
        ('transmiter_output', 'выход_ПРД'),
        ('ka_id', 'ИД_КА'),
        ('transmiter_power', 'мощн_ПРД'),
        ('is_receiving', 'прием_КА'),
        ('count_msg_from_ivk', 'кол_сообщ_ИВК'),
        ('last_ivk_msg_number', 'посл_сообщ_ИВК'),
        ('ka_estimate_range', 'дальн_КА'),
        ('ka_estimate_speed', 'скорость_движ_КА')
    ]

    def toString(self):
        return '''ЗК в очереди: %d
Текущая литера: %d
Текущая отстройка частоты приёмника: %.3f Гц
Текущий уровень мощности, поступающей на приёмник: %.3f дБм
Текущая  скорость декодера ПРМ КПА: %d
Режим модуляции ПРД КПА: %d
Вход Приемника: %d
Выход Передатчика: %d
Установленный ИД КА: %d
Выходной уровень мощности  ПРД КПА: %.3f дБ
Наличие приема с КА: %d
Количество сообщений, полученных из ИВК: %d
Номер последнего сообщения, полученного из ИВК: %d
Оценка дальности до КА: %.3f м
Оценка скорости движения КА: %.3f м/с
''' % (self.queue_count, self.letter, self.receiver_frequency, self.receiver_power, self.receiver_speed,
       self.transmiter_modulation, self.receiver_input, self.transmiter_output, self.ka_id, self.transmiter_power,
       self.is_receiving, self.count_msg_from_ivk, self.last_ivk_msg_number, self.ka_estimate_range,
       self.ka_estimate_speed)


class TMI(BinaryStreamBE):
    _fields_ = [
        ('box_frame_type', ctypes.c_uint16),
        ('box_zero', ctypes.c_uint32),
        ('box_len', ctypes.c_uint16),

        ('start_1ACFFC1D', ctypes.c_uint32),

        ('frame_zero0', ctypes.c_uint16, 2),
        ('frame_ka_id', ctypes.c_uint16, 10),
        ('frame_is_hk', ctypes.c_uint16, 4),
        ('frame_counter_main', ctypes.c_uint8),
        ('frame_counter_virtual', ctypes.c_uint8),
        ('frame_95', ctypes.c_uint8),
        ('frame_255', ctypes.c_uint8),
        ('frame_expected_close_rk', ctypes.c_uint8),
        ('frame_counter_close_rk', ctypes.c_uint8),
        ('frame_zero8', ctypes.c_uint8),
        ('frame_expected_cpi', ctypes.c_uint8),
        ('frame_counter_cpi', ctypes.c_uint8),
        ('frame_zero11', ctypes.c_uint8),
        ('frame_zero12', ctypes.c_uint8),
        ('frame_zero13', ctypes.c_uint8),
        ('frame_break_close_rk', ctypes.c_uint8, 1),
        ('frame_zero14_1', ctypes.c_uint8, 2),
        ('frame_break_cpi', ctypes.c_uint8, 1),
        ('frame_zero14_2', ctypes.c_uint8, 4),
        ('frame_error_bch', ctypes.c_uint8, 1),
        ('frame_error_crc', ctypes.c_uint8, 1),
        ('frame_error_format', ctypes.c_uint8, 1),
        ('frame_error_ka_id', ctypes.c_uint8, 1),
        ('frame_error_channel_id', ctypes.c_uint8, 1),
        ('frame_error_m694', ctypes.c_uint8, 1),
        ('frame_error_hk', ctypes.c_uint8, 1),
        ('frame_exists_hk', ctypes.c_uint8, 1),
        ('frame_ready_m694', ctypes.c_uint8, 1),
        ('frame_zero16', ctypes.c_uint8, 7),
        ('frame_zero17', ctypes.c_uint8),
        ('frame_tmi_ba_kis', ctypes.c_uint8 * 41),
        ('frame_sync_package', ctypes.c_uint8 * 8),
        ('frame_tmi_ba_kis_tech', ctypes.c_uint8 * 1048),

        ('end_crc', ctypes.c_uint8 * 160),
    ]
