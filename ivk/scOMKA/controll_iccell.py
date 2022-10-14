import ctypes
import struct

from cpi_framework.utils.BinaryStream import BinaryStreamBE, BinaryStreamLE
from ivk import config


class ICCELL:
    MESSAGES_TO_ICCELL = config.odict(
        ('ЗапрСост', {
            'id': 0x00,
            'description': 'Запрос состояния ячейки ПИ (0x00)',
            'responce_id': 0x80,
            'get_responce_class': lambda: StatusResponce()
        }),
        ('ВыходИБГФ', {  # OK
            'id': 0x01,
            'description': 'Управление коммутацией выходов ИГБФ (имитатор генератора батареи фотоэлектрической). Четыре 8ми битовых целых числа, каждый бит (0-7) ' +
                           'отвечает за состояние соответствующего выхода (1-8 для первого числа, 9-16 для второго числа, 17-24 для третьего числа, ' +
                           '25-32 для четвертого числа соответственно). Значение битов: 0 выход отключен, 1 выход включен.\nПараметры:\n' + \
                           '  - out(list[int]): список значений состояний выходов ИГБФ',
            'params': [
                {'name': 'out',
                 'type': list,
                 'subtype': int,
                 'default': '[0xFF, 0xFF, 0xFF, 0xFF]',
                 'check': lambda lst: len(lst) == 4 and all(x >= 0 and x <= 0xFF for x in lst),
                 'check_msg': 'Список должен содержать 4 числа и каждое число должно находиться в диапазоне от 0x0 до 0xFF',
                 'to_data': lambda lst: struct.pack('>4B', *lst)}
            ],
            'responce_id': 0x81,
            'get_responce_class': lambda: IBGFResponce()
        }),
        ('ВыходИАБ', {  # OK
            'id': 0x02,
            'description': 'Управление коммутацией выхода ИАБ (имитатор акумуляторной батареи): 0 выход отключен, 1 выход включен.\nПараметры:\n' + \
                           '  - out(int): значение состояния выхода ИАБ',
            'params': [
                {'name': 'out',
                 'type': int,
                 'default': '1',
                 'check': lambda val: val in (0, 1),
                 'check_msg': 'Состояние выхода ИАБ должно иметь значение 0 или 1',
                 'to_data': lambda val: struct.pack('>B', val)}
            ],
            'responce_id': 0x82,
            'get_responce_class': lambda: IABResponce()
        }),
        ('ВыходММ', {  # OK
            'id': 0x03,
            'description': 'Управление полярность выходов источников питания для иммитаторов ММ (магнитометры). 8ми битовое целое число. ' +
                           'Биты (0-5) числа (параметр POLARITY), ' +
                           'отвечают за полярность соответствующего выхода (X1, X2, Y1, Y2, Z1, Z2 соответственно), ' +
                           'значение битов: 0 отрицательная полярность, 1 положительная полярность.\nПараметры:\n' + \
                           '  - polarity(int): значение полярности выходов ММ',
            'params': [
                {'name': 'polarity',
                 'type': int,
                 'default': '0x3F',
                 'check': lambda val: val >= 0 and val <= 0x3F,
                 'check_msg': 'Побитная полярность выходов питания иммитаторов ММ должна находиться в диапазоне от 0x0 до 0x3F',
                 'to_data': lambda val: struct.pack('>B', val)},
            ],
            'responce_id': 0x83,
            'get_responce_class': lambda: MMResponce()
        }),
        ('ВыходДС', {  # OK
            'id': 0x04,
            'description': 'Управление выходами источников питания имитаторов для ДС (датчик солнца), 8ми битное целое число. ' +
                           'Биты 0-7 отвечают за состояние соответствующего выхода (1-8), значения битов: 0 выход отключен, 1 выход включен.\nПараметры:\n' + \
                           '  - out(int): значение состояний выходов ДС',
            'params': [
                {'name': 'out',
                 'type': int,
                 'default': '0xFF',
                 'check': lambda val: val >= 0 and val <= 0xFF,
                 'check_msg': 'Состояние выходов источников питания имитаторов для ДС должно находиться в диапазоне от 0x0 до 0xFF',
                 'to_data': lambda val: struct.pack('>B', val)}
            ],
            'responce_id': 0x84,
            'get_responce_class': lambda: DSResponce()
        }),
        ('ВыходДВ', {  # OK
            'id': 0x05,
            'description': 'Управление выходом питания имитатора для ДВ (датчик вертикали): 0 выход отключен, 1 выход включен.\nПараметры:\n' + \
                           '  - out(int): значение состояния выхода ДВ',
            'params': [
                {'name': 'out',
                 'type': int,
                 'default': '1',
                 'check': lambda val: val in (0, 1),
                 'check_msg': 'Состояние выхода ДВ должно иметь значение 0 или 1',
                 'to_data': lambda val: struct.pack('>B', val)}
            ],
            'responce_id': 0x85,
            'get_responce_class': lambda: DVResponce()
        }),
        ('ВыходЗД', {  # OK
            'id': 0x06,
            'description': 'Управление выходами питания для имитаторов ЗД (звездный датчик), 4ех битное целое число. ' +
                           'Биты 0-3 отвечают за состояние соответствующего выхода (1-4), значения битов: 0 выход отключен, 1 выход включен.\nПараметры:\n' + \
                           '  - out(int): значение состояний выходов ЗД',
            'params': [
                {'name': 'out',
                 'type': int,
                 'default': '0xF',
                 'check': lambda val: val >= 0 and val <= 0xF,
                 'check_msg': 'Состояние выходов питания имитаторов ЗД должно находиться в диапазоне от 0x0 до 0xF',
                 'to_data': lambda val: struct.pack('>B', val)}
            ],
            'responce_id': 0x86,
            'get_responce_class': lambda: ZDResponce()
        }),
        ('ВыходИВКР', {  # OK
            'id': 0x07,
            'description': 'Управление релейными выходами шкафа ИВК-Р, 5ти битное целое число. ' +
                           'Биты 0-4 отвечают за состояние соответствующего выхода (1ОтклБС, 2ОтклБС, 1Котд, 2Котд, БлокБС), ' +
                           'значения битов: 0 выход отключен, 1 выход включен.\nПараметры:\n' + \
                           '  - out(int): значение состояний выходов ИВК-Р',
            'params': [
                {'name': 'out',
                 'type': int,
                 'default': '0x1F',
                 'check': lambda val: val >= 0 and val <= 0x1F,
                 'check_msg': 'Состояние выходов шкафа ИВК-Р должно находиться в диапазоне от 0x0 до 0x1F',
                 'to_data': lambda val: struct.pack('>B', val)}
            ],
            'responce_id': 0x87,
            'get_responce_class': lambda: IVKRResponce()
        }),
        ('Импульс', {
            'id': 0x08,
            'description': 'Управление формированием импульсных команд. При получении ячейкой ПИ пакета - формируются однократные импульсные команды по соответствующим выходам. ' +
                           'Два 8ми битовых целых числа, каждый бит (0-7) отвечает за формирование импульсных команд по соответствующему ' +
                           'выходу (1-8 для первого числа, 9-16 для второго числа). Значение битов: 0 формировать импульсную команду, ' +
                           '1 не формировать импульсную команду.\nПараметры:\n' + \
                           '  - out(list[int]): список указаний на формирование импульсных команд\n'
                           'Максимум 1 импульсная команда в одном УВ',
            'params': [
                {'name': 'out',
                 'type': list,
                 'subtype': int,
                 'default': '[0xFF, 0xFF]',
                 'check': lambda lst: len(lst) == 2 and all(x >= 0 and x <= 0xFF for x in lst) and 1 >= ''.join(
                     map(lambda x: bin(x)[2:], lst)).count('1'),
                 # только один бит 1 в двух числах
                 # lambda lst: len(lst) == 2 and all(x >= 0 and x <= 0xFF for x in lst)
                 # TODO: Предлагают сделать выпадающую менюшку с разрешенными параметрами
                 'check_msg': 'Список должен содержать 2 числа одно из которых принимает одно из следующих значений: 0x40 0x20 0x10 0x08 0x04 0x02 0x01',
                 # Список должен содержать 2 числа и каждое число должно находиться в диапазоне от 0x0 до 0xFF
                 'to_data': lambda lst: struct.pack('>2B', *lst)}
            ],
            'responce_id': 0x88,
            'get_responce_class': lambda: ImpulseResponce()
        }),
        ('ТемператураАБ', {
            'id': 0x09,
            'description': 'Управление имитатором датчиков температуры АБ (аккумуляторная батарея). Значения температуры передаются в °С в диапазоне от 0 до 50°С.' +
                           'При передаче значения температуры, превышающего 50°С - имитируется обрыв цепи датчика. ' +
                           'Значение 51 разрешено к передаче и предназначено для имитации обрыва цепи датчика. ' +
                           '12 целых числел, каждое из которых отвечает за соответствующий (1-12) датчик температуры.\nПараметры:\n' + \
                           '  - temp(list[int]): список значений датчиков температуры АБ',
            'params': [
                {'name': 'temp',
                 'type': list,
                 'subtype': int,
                 'default': '[50, 50, 50, 50, 50, 50, \n50, 50, 50, 50, 50, 50]',
                 'check': lambda lst: len(lst) == 12 and all(x >= 0 and x <= 51 for x in lst),
                 'check_msg': 'Список должен содержать 12 чисел и каждое число должно находиться в диапазоне от 0 до 51',
                 'to_data': lambda lst: struct.pack('>12B', *lst)}
            ],
            'responce_id': 0x89,
            'get_responce_class': lambda: TempABResponce()
        }),
        ('ТемператураБФ', {
            'id': 0x0A,
            'description': 'Управление имитатором датчиков температуры БФ (батарея фотоэлектрическая). Кодировка значений температуры приведена в таблице 16 документа ТЯБК.441461.002 Д10. ' +
                           'При передаче кодов, не включенных в таблицу 16 - имитируется обрыв в цепи датчика. ' +
                           'Значение 0x15 разрешено к передаче и предназначено для имитации обрыва цепи датчика. ' +
                           '32 целых числа, каждое из которых отвечает за соответствующий (1-32) датчик температуры.\nПараметры:\n' + \
                           '  - temp(list[int]): список значений датчиков температуры БФ',
            'params': [
                {'name': 'temp',
                 'type': list,
                 'subtype': int,
                 'default': '[%s]' % ', '.join(['\n0x0F' if i in (6, 20) else '0x0F' for i in range(32)]),
                 'check': lambda lst: len(lst) == 32 and all(x >= 0 and x <= 0x15 for x in lst),
                 'check_msg': 'Список должен содержать 32 числа и каждое число должно находиться в диапазоне от 0x00 до 0x15',
                 'to_data': lambda lst: struct.pack('>32B', *lst)}
            ],
            'responce_id': 0x8A,
            'get_responce_class': lambda: TempBFResponce()
        }),
        ('ЗапрНараб', {
            'id': 0x0B,
            'description': 'Запрос времени наработки. Параметр reset отвечает за сброс счетчика наработки КА: '
                           'если пармаметр установлен в 1 то время наработки КА будет сброшено, если 0 то нет.\nПараметры:\n' + \
                           '  - reset(int): необходимость сброса времени наработки КА',
            'params': [
                {'name': 'reset',
                 'type': int,
                 'default': '0',
                 'check': lambda val: val in (0, 1),
                 'check_msg': 'Параметр сброса наработки КА должен принимать значения 0 или 1',
                 'to_data': lambda val: struct.pack('>H', 0x55AA) if val == 1 else struct.pack('>H', 0x0)}
            ],
            'responce_id': 0x8B,
            'get_responce_class': lambda: RunTimeResponce()
        }),
        ('ЗапрНапряж', {
            'id': 0x0C,
            'description': 'Запрос напряжения БС (бортовая сеть)',
            'responce_id': 0x8C,
            'get_responce_class': lambda: VoltageResponce()
        }),
        ('ЗапрСопрИзол', {
            'id': 0x0D,
            'description': 'Запрос значений сопротивления изоляции',
            'responce_id': 0x8D,
            'get_responce_class': lambda: ResistResponce()
        }),
        ('ЗапрНапряжСигТЛМ', {
            'id': 0x0E,
            'description': 'Запрос значений напряжения сигналов аналоговой телеметрии',
            'responce_id': 0x8E,
            'get_responce_class': lambda: VoltageSigTLMResponce()
        }),
        ('ЗапрТемпАБ', {
            'id': 0x0F,
            'description': 'Запрос значений температуры АБ (аккумуляторная батарея)',
            'responce_id': 0x8F,
            'get_responce_class': lambda: TempABReqResponce()
        })
    )

    def __init__(self, name, **kwargs):
        msg = None
        if isinstance(name, str) and name in ICCELL.MESSAGES_TO_ICCELL:
            msg = ICCELL.MESSAGES_TO_ICCELL[name]
        elif isinstance(name, int):
            for k, v in ICCELL.MESSAGES_TO_ICCELL.items():
                if v['id'] == name:
                    name = k
                    msg = ICCELL.MESSAGES_TO_ICCELL[name]
                    break
        if msg is None:
            raise Exception('Неопознанный код команды "%s"' % str(name))

        packed = struct.pack('>BB', config.getConf("iccell_counter"), msg['id'])
        if 'params' in msg:
            for param in msg['params']:
                if param['name'] not in kwargs:
                    raise Exception('Для команды "%s" необходимо задать параметр "%s"' % (name, param['name']))
                val = kwargs[param['name']]
                if not isinstance(val, param['type']):
                    raise Exception('Неверный тип данных параметра "%s"' % param['name'])
                if 'subtype' in param and not all(isinstance(x, param['subtype']) for x in val):
                    raise Exception('Неверный тип данных в списке параметра "%s"' % param['name'])
                if 'check' in param and not param['check'](val):
                    raise Exception(param['check_msg'])
                packed += param['to_data'](val)

        self.name = name
        self.msg = msg
        self.stream = packed


class ICCellResponce:
    def __init__(self, msg=None):
        if msg is not None:
            self.counter, self.packet_code = struct.unpack(">BB", msg[:2])
            self.data = msg[2:]
            self.unpacked = None
            self.msg_name = None
            for name, msg in ICCELL.MESSAGES_TO_ICCELL.items():
                if msg['responce_id'] == self.packet_code:
                    self.msg_name = name
                    self.unpacked = msg['get_responce_class']()
                    self.unpacked.fromStream(self.data)
                    break
        else:
            self.counter = 0x01
            self.data = None

    def dataString(self):
        return '[%s]' % ', '.join(['%d' % (b,) for b in self.data])

    def msgString(self):
        print("counter : %d, packet_code: %d, data: %s" % (self.counter, self.packet_code, self.dataString()))

    def onData(self):
        if self.unpacked:
            config.updData('iccell_' + self.msg_name, self.unpacked.toDict())

    @staticmethod
    def FromRedis(name):
        d = config.getData('iccell_' + name)
        if d:
            resp = ICCellResponce()
            resp.msg_name = name
            resp.packet_code = ICCELL.MESSAGES_TO_ICCELL[name]['responce_id']
            resp.unpacked = ICCELL.MESSAGES_TO_ICCELL[name]['get_responce_class']()
            resp.unpacked.fromDict(d)
            return resp
        return None

    @staticmethod
    def GetMsgFieldsDict():
        d = config.odict()
        for name, msg in ICCELL.MESSAGES_TO_ICCELL.items():
            d[name] = msg['get_responce_class']().getFieldNames()
        return d


class StatusResponce(BinaryStreamBE):
    _fields_ = [
        ('ka_powered', ctypes.c_uint8, 1),
        ('emergency_button', ctypes.c_uint8, 1),
        ('DS_pwr', ctypes.c_uint8, 1),
        ('MM_pwr', ctypes.c_uint8, 1),
        ('ZD_pwr', ctypes.c_uint8, 1),
        ('DV_pwr', ctypes.c_uint8, 1),
        ('IAB_pwr', ctypes.c_uint8, 1),
        ('IGBF_pwr', ctypes.c_uint8, 1),

        ('IZD_connected', ctypes.c_uint8, 1),
        ('KST_connected', ctypes.c_uint8, 1),
        ('IPD_connected', ctypes.c_uint8, 1),
        ('KMM_connected', ctypes.c_uint8, 1),
        ('KI4_connected', ctypes.c_uint8, 1),
        ('KI3_connected', ctypes.c_uint8, 1),
        ('KI2_connected', ctypes.c_uint8, 1),
        ('KI1_connected', ctypes.c_uint8, 1),

        ('PST_connected', ctypes.c_uint8, 1),
        ('IDT14_connected', ctypes.c_uint8, 1),
        ('IDT13_connected', ctypes.c_uint8, 1),
        ('IDT12_connected', ctypes.c_uint8, 1),
        ('IDT11_connected', ctypes.c_uint8, 1),
        ('IDT2_connected', ctypes.c_uint8, 1),
        ('IDT1_connected', ctypes.c_uint8, 1),
        ('IT_connected', ctypes.c_uint8, 1),

        ('reserved_byte_5', ctypes.c_uint8, 2),
        ('p24V_converter2', ctypes.c_uint8, 1),
        ('p24V_converter1', ctypes.c_uint8, 1),
        ('ka_counter_ok', ctypes.c_uint8, 1),
        ('ivk_counter_ok', ctypes.c_uint8, 1),
        ('IN_connected', ctypes.c_uint8, 1),
        ('IIK_connected', ctypes.c_uint8, 1),

        ('commutation_IGBF_8', ctypes.c_uint8, 1),
        ('commutation_IGBF_7', ctypes.c_uint8, 1),
        ('commutation_IGBF_6', ctypes.c_uint8, 1),
        ('commutation_IGBF_5', ctypes.c_uint8, 1),
        ('commutation_IGBF_4', ctypes.c_uint8, 1),
        ('commutation_IGBF_3', ctypes.c_uint8, 1),
        ('commutation_IGBF_2', ctypes.c_uint8, 1),
        ('commutation_IGBF_1', ctypes.c_uint8, 1),

        ('commutation_IGBF_16', ctypes.c_uint8, 1),
        ('commutation_IGBF_15', ctypes.c_uint8, 1),
        ('commutation_IGBF_14', ctypes.c_uint8, 1),
        ('commutation_IGBF_13', ctypes.c_uint8, 1),
        ('commutation_IGBF_12', ctypes.c_uint8, 1),
        ('commutation_IGBF_11', ctypes.c_uint8, 1),
        ('commutation_IGBF_10', ctypes.c_uint8, 1),
        ('commutation_IGBF_9', ctypes.c_uint8, 1),

        ('commutation_IGBF_24', ctypes.c_uint8, 1),
        ('commutation_IGBF_23', ctypes.c_uint8, 1),
        ('commutation_IGBF_22', ctypes.c_uint8, 1),
        ('commutation_IGBF_21', ctypes.c_uint8, 1),
        ('commutation_IGBF_20', ctypes.c_uint8, 1),
        ('commutation_IGBF_19', ctypes.c_uint8, 1),
        ('commutation_IGBF_18', ctypes.c_uint8, 1),
        ('commutation_IGBF_17', ctypes.c_uint8, 1),

        ('commutation_IGBF_32', ctypes.c_uint8, 1),
        ('commutation_IGBF_31', ctypes.c_uint8, 1),
        ('commutation_IGBF_30', ctypes.c_uint8, 1),
        ('commutation_IGBF_29', ctypes.c_uint8, 1),
        ('commutation_IGBF_28', ctypes.c_uint8, 1),
        ('commutation_IGBF_27', ctypes.c_uint8, 1),
        ('commutation_IGBF_26', ctypes.c_uint8, 1),
        ('commutation_IGBF_25', ctypes.c_uint8, 1),

        ('reserved_byte_10', ctypes.c_uint8, 1),
        ('commutation_MM_Z2', ctypes.c_uint8, 1),
        ('commutation_MM_Z1', ctypes.c_uint8, 1),
        ('commutation_MM_Y2', ctypes.c_uint8, 1),
        ('commutation_MM_Y1', ctypes.c_uint8, 1),
        ('commutation_MM_X2', ctypes.c_uint8, 1),
        ('commutation_MM_X1', ctypes.c_uint8, 1),
        ('commutation_IAB', ctypes.c_uint8, 1),

        ('out_DS8', ctypes.c_uint8, 1),
        ('out_DS7', ctypes.c_uint8, 1),
        ('out_DS6', ctypes.c_uint8, 1),
        ('out_DS5', ctypes.c_uint8, 1),
        ('out_DS4', ctypes.c_uint8, 1),
        ('out_DS3', ctypes.c_uint8, 1),
        ('out_DS2', ctypes.c_uint8, 1),
        ('out_DS1', ctypes.c_uint8, 1),

        ('reserved_byte_12', ctypes.c_uint8, 3),
        ('out_ZD4', ctypes.c_uint8, 1),
        ('out_ZD3', ctypes.c_uint8, 1),
        ('out_ZD2', ctypes.c_uint8, 1),
        ('out_ZD1', ctypes.c_uint8, 1),
        ('out_DV', ctypes.c_uint8, 1),

        ('reserved_byte_13', ctypes.c_uint8, 3),
        ('out_blokBS', ctypes.c_uint8, 1),
        ('out_2kotd', ctypes.c_uint8, 1),
        ('out_1kotd', ctypes.c_uint8, 1),
        ('out_2otklBS', ctypes.c_uint8, 1),
        ('out_1otklBS', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('ka_powered', 'питание_ка'),
        ('emergency_button', 'аварийная_кнопка'),
        ('DS_pwr', 'выход_ДС'),
        ('MM_pwr', 'выход_ММ'),
        ('ZD_pwr', 'выход_ЗД'),
        ('DV_pwr', 'выход_ДВ'),
        ('IAB_pwr', 'выход_ИАБ'),
        ('IGBF_pwr', 'выход_ИБГФ'),

        ('IZD_connected', 'связь_ИЗД'),
        ('KST_connected', 'связь_КСТ'),
        ('IPD_connected', 'связь_ИПД'),
        ('KMM_connected', 'связь_КММ'),
        ('KI4_connected', 'связь_КИ№4'),
        ('KI3_connected', 'связь_КИ№3'),
        ('KI2_connected', 'связь_КИ№2'),
        ('KI1_connected', 'связь_КИ№1'),

        ('PST_connected', 'связь_ПСТ'),
        ('IDT14_connected', 'связь_ИДТ1№4'),
        ('IDT13_connected', 'связь_ИДТ1№3'),
        ('IDT12_connected', 'связь_ИДТ1№2'),
        ('IDT11_connected', 'связь_ИДТ1№1'),
        ('IDT2_connected', 'связь_ИДТ№2'),
        ('IDT1_connected', 'связь_ИДТ№1'),
        ('IT_connected', 'связь_ИТ'),

        ('reserved_byte_5', None),
        ('p24V_converter2', 'питание_24В_П2'),
        ('p24V_converter1', 'питание_24В_П1'),
        ('ka_counter_ok', 'счетчик_КА_ок'),
        ('ivk_counter_ok', 'счетчик_ИВК_ок'),
        ('IN_connected', 'связь_ИН'),
        ('IIK_connected', 'связь_ИИК'),

        ('commutation_IGBF_8', 'коммутация_ИГБФ8'),
        ('commutation_IGBF_7', 'коммутация_ИГБФ7'),
        ('commutation_IGBF_6', 'коммутация_ИГБФ6'),
        ('commutation_IGBF_5', 'коммутация_ИГБФ5'),
        ('commutation_IGBF_4', 'коммутация_ИГБФ4'),
        ('commutation_IGBF_3', 'коммутация_ИГБФ3'),
        ('commutation_IGBF_2', 'коммутация_ИГБФ2'),
        ('commutation_IGBF_1', 'коммутация_ИГБФ1'),

        ('commutation_IGBF_16', 'коммутация_ИГБФ16'),
        ('commutation_IGBF_15', 'коммутация_ИГБФ15'),
        ('commutation_IGBF_14', 'коммутация_ИГБФ14'),
        ('commutation_IGBF_13', 'коммутация_ИГБФ13'),
        ('commutation_IGBF_12', 'коммутация_ИГБФ12'),
        ('commutation_IGBF_11', 'коммутация_ИГБФ11'),
        ('commutation_IGBF_10', 'коммутация_ИГБФ10'),
        ('commutation_IGBF_9', 'коммутация_ИГБФ9'),

        ('commutation_IGBF_24', 'коммутация_ИГБФ24'),
        ('commutation_IGBF_23', 'коммутация_ИГБФ23'),
        ('commutation_IGBF_22', 'коммутация_ИГБФ22'),
        ('commutation_IGBF_21', 'коммутация_ИГБФ21'),
        ('commutation_IGBF_20', 'коммутация_ИГБФ20'),
        ('commutation_IGBF_19', 'коммутация_ИГБФ19'),
        ('commutation_IGBF_18', 'коммутация_ИГБФ18'),
        ('commutation_IGBF_17', 'коммутация_ИГБФ17'),

        ('commutation_IGBF_32', 'коммутация_ИГБФ32'),
        ('commutation_IGBF_31', 'коммутация_ИГБФ31'),
        ('commutation_IGBF_30', 'коммутация_ИГБФ30'),
        ('commutation_IGBF_29', 'коммутация_ИГБФ29'),
        ('commutation_IGBF_28', 'коммутация_ИГБФ28'),
        ('commutation_IGBF_27', 'коммутация_ИГБФ27'),
        ('commutation_IGBF_26', 'коммутация_ИГБФ26'),
        ('commutation_IGBF_25', 'коммутация_ИГБФ25'),

        ('reserved_byte_10', None),
        ('commutation_MM_Z2', 'коммутация_ММ_Z2'),
        ('commutation_MM_Z1', 'коммутация_ММ_Z1'),
        ('commutation_MM_Y2', 'коммутация_ММ_Y2'),
        ('commutation_MM_Y1', 'коммутация_ММ_Y1'),
        ('commutation_MM_X2', 'коммутация_ММ_X2'),
        ('commutation_MM_X1', 'коммутация_ММ_X1'),
        ('commutation_IAB', 'коммутация_ИАБ'),

        ('out_DS8', 'выход_ДС8'),
        ('out_DS7', 'выход_ДС7'),
        ('out_DS6', 'выход_ДС6'),
        ('out_DS5', 'выход_ДС5'),
        ('out_DS4', 'выход_ДС4'),
        ('out_DS3', 'выход_ДС3'),
        ('out_DS2', 'выход_ДС2'),
        ('out_DS1', 'выход_ДС1'),

        ('reserved_byte_12', None),
        ('out_ZD4', 'выход_ЗД4'),
        ('out_ZD3', 'выход_ЗД3'),
        ('out_ZD2', 'выход_ЗД2'),
        ('out_ZD1', 'выход_ЗД1'),
        ('out_DV', 'выход_ДВ'),

        ('out_blokBS', 'выход_БлокБС'),
        ('out_2kotd', 'выход_2Котд'),
        ('out_1kotd', 'выход_1Котд'),
        ('out_2otklBS', 'выход_2ОтклБС'),
        ('out_1otklBS', 'выход_1ОтклБС')
    ]


class IBGFResponce(BinaryStreamBE):
    _fields_ = [
        ('outs_1_8', ctypes.c_uint8),
        ('outs_9_16', ctypes.c_uint8),
        ('outs_17_24', ctypes.c_uint8),
        ('outs_25_32', ctypes.c_uint8)
    ]
    _field_names_ = [
        ('outs_1_8', 'выходы_1_8'),
        ('outs_9_16', 'выходы_9_16'),
        ('outs_17_24', 'выходы_17_24'),
        ('outs_25_32', 'выходы_25_32')
    ]


class IABResponce(BinaryStreamBE):
    _fields_ = [
        ('reserved', ctypes.c_uint8, 7),
        ('iab_out', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('reserved', None),
        ('iab_out', 'выход_ИАБ')
    ]


class MMResponce(BinaryStreamBE):
    _fields_ = [
        ('reserved', ctypes.c_uint8, 2),
        ('polarity_Z2', ctypes.c_uint8, 1),
        ('polarity_Z1', ctypes.c_uint8, 1),
        ('polarity_Y2', ctypes.c_uint8, 1),
        ('polarity_Y1', ctypes.c_uint8, 1),
        ('polarity_X2', ctypes.c_uint8, 1),
        ('polarity_X1', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('reserved', None),
        ('polarity_Z2', 'полярность_Z2'),
        ('polarity_Z1', 'полярность_Z1'),
        ('polarity_Y2', 'полярность_Y2'),
        ('polarity_Y1', 'полярность_Y1'),
        ('polarity_X2', 'полярность_X2'),
        ('polarity_X1', 'полярность_X1')
    ]


class DSResponce(BinaryStreamBE):
    _fields_ = [
        ('out_8', ctypes.c_uint8, 1),
        ('out_7', ctypes.c_uint8, 1),
        ('out_6', ctypes.c_uint8, 1),
        ('out_5', ctypes.c_uint8, 1),
        ('out_4', ctypes.c_uint8, 1),
        ('out_3', ctypes.c_uint8, 1),
        ('out_2', ctypes.c_uint8, 1),
        ('out_1', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('out_8', 'выход_8'),
        ('out_7', 'выход_7'),
        ('out_6', 'выход_6'),
        ('out_5', 'выход_5'),
        ('out_4', 'выход_4'),
        ('out_3', 'выход_3'),
        ('out_2', 'выход_2'),
        ('out_1', 'выход_1')
    ]


class DVResponce(BinaryStreamBE):
    _fields_ = [
        ('reserved', ctypes.c_uint8, 7),
        ('dv_out', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('reserved', None),
        ('dv_out', 'выход_ДВ')
    ]


class ZDResponce(BinaryStreamBE):
    _fields_ = [
        ('reserved', ctypes.c_uint8, 4),
        ('out_4', ctypes.c_uint8, 1),
        ('out_3', ctypes.c_uint8, 1),
        ('out_2', ctypes.c_uint8, 1),
        ('out_1', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('reserved', None),
        ('out_4', 'выход_4'),
        ('out_3', 'выход_3'),
        ('out_2', 'выход_2'),
        ('out_1', 'выход_1')
    ]


class IVKRResponce(BinaryStreamBE):
    _fields_ = [
        ('reserved', ctypes.c_uint8, 3),
        ('out_blokBS', ctypes.c_uint8, 1),
        ('out_2kotd', ctypes.c_uint8, 1),
        ('out_1kotd', ctypes.c_uint8, 1),
        ('out_2otklBS', ctypes.c_uint8, 1),
        ('out_1otklBS', ctypes.c_uint8, 1)
    ]
    _field_names_ = [
        ('reserved', None),
        ('out_blokBS', 'выход_БлокБС'),
        ('out_2kotd', 'выход_2Котд'),
        ('out_1kotd', 'выход_1Котд'),
        ('out_2otklBS', 'выход_2ОтклБС'),
        ('out_1otklBS', 'выход_1ОтклБС')
    ]


class ImpulseResponce(BinaryStreamBE):
    _fields_ = [
        ('impulse_1_8', ctypes.c_uint8),
        ('impulse_9_16', ctypes.c_uint8)
    ]
    _field_names_ = [
        ('impulse_1_8', 'импульс_1_8'),
        ('impulse_9_16', 'импульс_9_16')
    ]


class TempABResponce(BinaryStreamBE):
    _fields_ = [
        ('temp_chan_1', ctypes.c_uint8),
        ('temp_chan_2', ctypes.c_uint8),
        ('temp_chan_3', ctypes.c_uint8),
        ('temp_chan_4', ctypes.c_uint8),
        ('temp_chan_5', ctypes.c_uint8),
        ('temp_chan_6', ctypes.c_uint8),
        ('temp_chan_7', ctypes.c_uint8),
        ('temp_chan_8', ctypes.c_uint8),
        ('temp_chan_9', ctypes.c_uint8),
        ('temp_chan_10', ctypes.c_uint8),
        ('temp_chan_11', ctypes.c_uint8),
        ('temp_chan_12', ctypes.c_uint8)
    ]
    _field_names_ = [
        ('temp_chan_1', 'темп_канал_1'),
        ('temp_chan_2', 'темп_канал_2'),
        ('temp_chan_3', 'темп_канал_3'),
        ('temp_chan_4', 'темп_канал_4'),
        ('temp_chan_5', 'темп_канал_5'),
        ('temp_chan_6', 'темп_канал_6'),
        ('temp_chan_7', 'темп_канал_7'),
        ('temp_chan_8', 'темп_канал_8'),
        ('temp_chan_9', 'темп_канал_9'),
        ('temp_chan_10', 'темп_канал_10'),
        ('temp_chan_11', 'темп_канал_11'),
        ('temp_chan_12', 'темп_канал_12')
    ]


class TempBFResponce(BinaryStreamBE):
    _fields_ = [
        ('temp_chan_1', ctypes.c_uint8),
        ('temp_chan_2', ctypes.c_uint8),
        ('temp_chan_3', ctypes.c_uint8),
        ('temp_chan_4', ctypes.c_uint8),
        ('temp_chan_5', ctypes.c_uint8),
        ('temp_chan_6', ctypes.c_uint8),
        ('temp_chan_7', ctypes.c_uint8),
        ('temp_chan_8', ctypes.c_uint8),
        ('temp_chan_9', ctypes.c_uint8),
        ('temp_chan_10', ctypes.c_uint8),
        ('temp_chan_11', ctypes.c_uint8),
        ('temp_chan_12', ctypes.c_uint8),
        ('temp_chan_13', ctypes.c_uint8),
        ('temp_chan_14', ctypes.c_uint8),
        ('temp_chan_15', ctypes.c_uint8),
        ('temp_chan_16', ctypes.c_uint8),
        ('temp_chan_17', ctypes.c_uint8),
        ('temp_chan_18', ctypes.c_uint8),
        ('temp_chan_19', ctypes.c_uint8),
        ('temp_chan_20', ctypes.c_uint8),
        ('temp_chan_21', ctypes.c_uint8),
        ('temp_chan_22', ctypes.c_uint8),
        ('temp_chan_23', ctypes.c_uint8),
        ('temp_chan_24', ctypes.c_uint8),
        ('temp_chan_25', ctypes.c_uint8),
        ('temp_chan_26', ctypes.c_uint8),
        ('temp_chan_27', ctypes.c_uint8),
        ('temp_chan_28', ctypes.c_uint8),
        ('temp_chan_29', ctypes.c_uint8),
        ('temp_chan_30', ctypes.c_uint8),
        ('temp_chan_31', ctypes.c_uint8),
        ('temp_chan_32', ctypes.c_uint8)
    ]
    _field_names_ = [
        ('temp_chan_1', 'код_темп_канал_1'),
        ('temp_chan_2', 'код_темп_канал_2'),
        ('temp_chan_3', 'код_темп_канал_3'),
        ('temp_chan_4', 'код_темп_канал_4'),
        ('temp_chan_5', 'код_темп_канал_5'),
        ('temp_chan_6', 'код_темп_канал_6'),
        ('temp_chan_7', 'код_темп_канал_7'),
        ('temp_chan_8', 'код_темп_канал_8'),
        ('temp_chan_9', 'код_темп_канал_9'),
        ('temp_chan_10', 'код_темп_канал_10'),
        ('temp_chan_11', 'код_темп_канал_11'),
        ('temp_chan_12', 'код_темп_канал_12'),
        ('temp_chan_13', 'код_темп_канал_13'),
        ('temp_chan_14', 'код_темп_канал_14'),
        ('temp_chan_15', 'код_темп_канал_15'),
        ('temp_chan_16', 'код_темп_канал_16'),
        ('temp_chan_17', 'код_темп_канал_17'),
        ('temp_chan_18', 'код_темп_канал_18'),
        ('temp_chan_19', 'код_темп_канал_19'),
        ('temp_chan_20', 'код_темп_канал_20'),
        ('temp_chan_21', 'код_темп_канал_21'),
        ('temp_chan_22', 'код_темп_канал_22'),
        ('temp_chan_23', 'код_темп_канал_23'),
        ('temp_chan_24', 'код_темп_канал_24'),
        ('temp_chan_25', 'код_темп_канал_25'),
        ('temp_chan_26', 'код_темп_канал_26'),
        ('temp_chan_27', 'код_темп_канал_27'),
        ('temp_chan_28', 'код_темп_канал_28'),
        ('temp_chan_29', 'код_темп_канал_29'),
        ('temp_chan_30', 'код_темп_канал_30'),
        ('temp_chan_31', 'код_темп_канал_31'),
        ('temp_chan_32', 'код_темп_канал_32')
    ]


class RunTimeResponce(BinaryStreamLE):
    _fields_ = [
        ('run_time_IVK', ctypes.c_uint32),
        ('run_time_KA', ctypes.c_uint32)
    ]
    _field_names_ = [
        ('run_time_IVK', 'наработка_ИВК'),
        ('run_time_KA', 'наработка_КА')
    ]


class VoltageResponce(BinaryStreamLE):
    _fields_ = [
        ('voltage', ctypes.c_uint16)
    ]
    _field_names_ = [
        ('voltage', 'напряжение_БС')
    ]


class ResistResponce(BinaryStreamLE):
    _fields_ = [
        ('resist_SEP_plus', ctypes.c_uint16),
        ('resist_SEP_minus', ctypes.c_uint16)
    ]
    _field_names_ = [
        ('resist_SEP_plus', 'сопр_СЭП+'),
        ('resist_SEP_minus', 'сопр_СЭП-')
    ]


class VoltageSigTLMResponce(BinaryStreamLE):
    _fields_ = [
        ('voltage_chan_1', ctypes.c_uint16),
        ('voltage_chan_2', ctypes.c_uint16),
        ('voltage_chan_3', ctypes.c_uint16),
        ('voltage_chan_4', ctypes.c_uint16),
        ('voltage_chan_5', ctypes.c_uint16),
        ('voltage_chan_6', ctypes.c_uint16),
        ('voltage_chan_7', ctypes.c_uint16),
        ('voltage_chan_8', ctypes.c_uint16)
    ]
    _field_names_ = [
        ('voltage_chan_1', 'напряж_канал_1'),
        ('voltage_chan_2', 'напряж_канал_2'),
        ('voltage_chan_3', 'напряж_канал_3'),
        ('voltage_chan_4', 'напряж_канал_4'),
        ('voltage_chan_5', 'напряж_канал_5'),
        ('voltage_chan_6', 'напряж_канал_6'),
        ('voltage_chan_7', 'напряж_канал_7'),
        ('voltage_chan_8', 'напряж_канал_8')
    ]


class TempABReqResponce(BinaryStreamLE):
    _fields_ = [
        ('temp_chan_1', ctypes.c_int16),
        ('temp_chan_2', ctypes.c_int16),
        ('temp_chan_3', ctypes.c_int16),
        ('temp_chan_4', ctypes.c_int16),
        ('temp_chan_5', ctypes.c_int16),
        ('temp_chan_6', ctypes.c_int16),
        ('temp_chan_7', ctypes.c_int16),
        ('temp_chan_8', ctypes.c_int16),
        ('temp_chan_9', ctypes.c_int16),
        ('temp_chan_10', ctypes.c_int16),
        ('temp_chan_11', ctypes.c_int16),
        ('temp_chan_12', ctypes.c_int16)
    ]
    _field_names_ = [
        ('temp_chan_1', 'темп_канал_1'),
        ('temp_chan_2', 'темп_канал_2'),
        ('temp_chan_3', 'темп_канал_3'),
        ('temp_chan_4', 'темп_канал_4'),
        ('temp_chan_5', 'темп_канал_5'),
        ('temp_chan_6', 'темп_канал_6'),
        ('temp_chan_7', 'темп_канал_7'),
        ('temp_chan_8', 'темп_канал_8'),
        ('temp_chan_9', 'темп_канал_9'),
        ('temp_chan_10', 'темп_канал_10'),
        ('temp_chan_11', 'темп_канал_11'),
        ('temp_chan_12', 'темп_канал_12')
    ]
