import struct, ctypes, threading
from queue import Queue
from cpi_framework.utils.BinaryStream import BinaryStreamBE, BinaryStreamLE
from ivk import config

class CheckableQueue(Queue):

    def has(self, key, value):
        result = False
        with self.mutex:
            for item in self.queue:
                if item[key] == value:
                    result = True
                    break
        return result
    
    def getFromFirst(self, key):
        result = None
        if not self.empty():
            with self.mutex:
                if key in self.queue[0]:
                    result = self.queue[0][key]
        return result
        
        

class SCPI:
    #ИБГФ1 ... ИГБФ32 - Tdk Lambda Z60-3.5-LAN-E, max 60V, max 3.5A
    #ММ_ - Tdk Lambda Z10-20-LAN-E, max 10V, max 20A
    #ИАБ - Tdk Lambda GEN40-38-LAN, max 40V, max 38A
    SCPI_DEVICES = config.odict(
        ('ИГБФ1', {'default_ip': '192.168.1.3', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ2', {'default_ip': '192.168.1.4', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ3', {'default_ip': '192.168.1.5', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ4', {'default_ip': '192.168.1.6', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ5', {'default_ip': '192.168.1.7', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ6', {'default_ip': '192.168.1.8', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ7', {'default_ip': '192.168.1.9', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ8', {'default_ip': '192.168.1.10', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ9', {'default_ip': '192.168.1.11', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ10', {'default_ip': '192.168.1.12', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ11', {'default_ip': '192.168.1.13', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ12', {'default_ip': '192.168.1.14', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ13', {'default_ip': '192.168.1.15', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ14', {'default_ip': '192.168.1.16', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ15', {'default_ip': '192.168.1.17', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ16', {'default_ip': '192.168.1.18', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ17', {'default_ip': '192.168.1.19', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ18', {'default_ip': '192.168.1.20', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ19', {'default_ip': '192.168.1.21', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ20', {'default_ip': '192.168.1.22', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ21', {'default_ip': '192.168.1.23', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ22', {'default_ip': '192.168.1.24', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ23', {'default_ip': '192.168.1.25', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ24', {'default_ip': '192.168.1.26', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ25', {'default_ip': '192.168.1.27', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ26', {'default_ip': '192.168.1.28', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ27', {'default_ip': '192.168.1.29', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ28', {'default_ip': '192.168.1.30', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ29', {'default_ip': '192.168.1.31', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ30', {'default_ip': '192.168.1.32', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ31', {'default_ip': '192.168.1.33', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИГБФ32', {'default_ip': '192.168.1.34', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 60.0, 'max_current': 3.5}),
        ('ИАБ', {'default_ip': '192.168.1.35', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 40.0, 'max_current': 38.0, 'custom_terminator': ';\r\n'}),
        ('ММ_X1', {'default_ip': '192.168.1.36', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 10.0, 'max_current': 20.0}),
        ('ММ_X2', {'default_ip': '192.168.1.37', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 10.0, 'max_current': 20.0}),
        ('ММ_Y1', {'default_ip': '192.168.1.38', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 10.0, 'max_current': 20.0}),
        ('ММ_Y2', {'default_ip': '192.168.1.39', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 10.0, 'max_current': 20.0}),
        ('ММ_Z1', {'default_ip': '192.168.1.40', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 10.0, 'max_current': 20.0}),
        ('ММ_Z2', {'default_ip': '192.168.1.41', 'default_port': 8003, 'send_queue': CheckableQueue(), 'recv_queue': CheckableQueue(), 'max_voltage': 10.0, 'max_current': 20.0})
    )

    #SYSTem:ERRor:ENABle #enable error messages
    #SYST:ERR? #read last error message
    MESSAGES_TO_SCPI = config.odict(
        # ('Кастом', {
        #     'id' : 0,
        #     'description' : 'Кастомный scpi запрос',
        #     'params' : [
        #         { 'name' : 'command', 
        #           'type' : str,
        #           'default' : '"SYST:ERR?"'}
        #     ],
        #     'cmd' : '%s',
        #     'unpackResponce' : lambda device, data: str(data.decode('ascii').strip())
        # }),
        ('ЗапрСост', {
            'id' : 1,
            'description' : 'Запрос состояния, включена или выключена подача тока',
            'cmd' : 'OUTP:STAT?',
            'unpackResponce' : lambda device, data: int(data.decode('ascii').strip()) if device != 'ИАБ' else (1 if data.decode('ascii').strip() == 'ON' else 0)
        }),
        ('УстСост', {
            'id' : 2,
            'description' : 'Установка состояния: 1 - подача тока включена, 0 - подача тока выключена.\nПараметры:\n' + \
                            '  - output(int): значение состояния (0 или 1)',
            'params' : [
                { 'name' : 'output', 
                  'type' : int,
                  'default' : '1', 
                  'check' : lambda val: val in (0, 1), 
                  'check_msg' : 'Значение должно равняться 0 или 1'}
            ],
            'cmd' : 'OUTP:STAT %d'
        }),
        ('ЗапрНапряж', {
            'id' : 3,
            'description' : 'Запрос напряжения в вольтах',
            'cmd' : 'MEAS:VOLT?',
            'unpackResponce' : lambda device, data: float(data.decode('ascii').strip())
        }),
        ('УстНапряж', {
            'id' : 4,
            'description' : 'Установка напряжения в вольтах.\nПараметры:\n' + \
                            '  - voltage(float): значение напряжения в вольтах',
            'params' : [
                { 'name' : 'voltage', 
                  'type' : float,
                  'default' : '20.0', 
                  #'check' : lambda val: val >= 0.0 and val <= 60.0, 
                  #'check_msg' : 'Значение напряжения должно быть числом в диапазоне от 0.0 В до 60.0 В',
                  'device_check' : lambda device, val: val >= 0.0 and val <= SCPI.SCPI_DEVICES[device]['max_voltage'],
                  'device_check_msg' : lambda device: 'Для %s значение напряжения должно быть числом в диапазоне от 0.0 В до %.1f В' % (device, SCPI.SCPI_DEVICES[device]['max_voltage']) 
                }
            ],
            'cmd' : 'SOUR:VOLT %f'
        }),
        ('ЗапрТок', {
            'id' : 5,
            'description' : 'Запрос тока в амперах',
            'cmd' : 'MEAS:CURR?',
            'unpackResponce' : lambda device, data: float(data.decode('ascii').strip())
        }),
        ('УстТок', {
            'id' : 6,
            'description' : 'Установка тока в амперах.\nПараметры:\n' + \
                            '  - current(float): значение тока в Амперах',
            'params' : [
                { 'name' : 'current', 
                  'type' : float,
                  'default' : '0.5', 
                  #'check' : lambda val: val >= 0.0 and val <= 38.0, 
                  #'check_msg' : 'Значение тока должно быть числом в диапазоне от 0.0 А до 38.0 А',
                  'device_check' : lambda device, val: val >= 0.0 and val <= SCPI.SCPI_DEVICES[device]['max_current'],
                  'device_check_msg' : lambda device: 'Для %s значение тока должно быть числом в диапазоне от 0.0 А до %.1f А' % (device, SCPI.SCPI_DEVICES[device]['max_current']) 
                }
            ],
            'cmd' : 'SOUR:CURR %f'
        })
    )

    @staticmethod
    def MsgById(msg_id):
        for k, v in SCPI.MESSAGES_TO_SCPI.items():
            if v['id'] == msg_id:
                return k, v
        return None, None

    def __init__(self, name, **kwargs):
        msg = None
        if isinstance(name, str) and name in SCPI.MESSAGES_TO_SCPI:
            msg = SCPI.MESSAGES_TO_SCPI[name]
        elif isinstance(name, int):
            name, msg = SCPI.MsgById(name)
        if msg is None:
            raise Exception('Неопознанный код команды "%s"' % str(name))
        
        param_values = []
        self.kwargs = None
        if 'params' in msg:
            self.kwargs = kwargs
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
                param_values.append(val)
        
        
        self.name = name
        self.msg = msg
        self.unencoded_stream = (msg['cmd'] if 'params' not in msg else msg['cmd'] % tuple(param_values)) + '\r\n'
        self.stream = self.unencoded_stream.encode('ascii')
    
    def deviceCheck(self, device):
        if self.kwargs is not None:
            for param in self.msg['params']:
                val = self.kwargs[param['name']]
                if 'device_check' in param and not param['device_check'](device, val):
                    raise Exception(param['device_check_msg'](device))
        if 'custom_terminator' in SCPI.SCPI_DEVICES[device]:
            self.stream = self.unencoded_stream.replace('\r\n', SCPI.SCPI_DEVICES[device]['custom_terminator']).encode('ascii')

    
class SCPIResponce:
    def __init__(self, device, data=None):
        self.data = None
        self.msg = None
        self.name = None
        self.unpacked = None
        self.device = device
        if data is not None:
            self.data = data
            recv_queue = SCPI.SCPI_DEVICES[device]['recv_queue']
            if not recv_queue.empty():
                queue_elem = recv_queue.get()
                self.name, self.msg = SCPI.MsgById(queue_elem['msg_id'])
                if self.msg:
                    self.unpacked = self.msg['unpackResponce'](device, data)
                    #print('RECV_UNPACK %d' % self.msg['id'])
                else:
                    self.unpack_error = "data %s, msg_id %s, Msg found %s, name found %s" % (str(self.data), str(queue_elem['msg_id']), str(self.msg), str(self.name))
                    print('RECV_ERROR %s' % self.unpack_error)
            else:
                self.unpack_error = "data %s, recv queue empty" % str(self.data)
                print('RECV_ERROR %s' % self.unpack_error)
    
    def printInfo(self):
        if self.unpacked is not None:
            print("%s, %s, %s, %s" % (self.device, self.name, str(self.unpacked), str(self.data)))
        else:
            print("%s, %s, %s" % (self.device, str(self.data), self.unpack_error))
    
    def onData(self):
        if self.unpacked is not None:
            config.updData('scpi_%s_%s' % (self.device, self.name), self.unpacked)


    @staticmethod
    def FromRedis(device, name):
        return config.getData('scpi_%s_%s' % (device, name))
    
    @staticmethod
    def GetMsgFieldsDict():
        d = config.odict()
        messages = [name for name, msg in SCPI.MESSAGES_TO_SCPI.items() if 'unpackResponce' in msg]
        for device in SCPI.SCPI_DEVICES:
            d[device] = messages
        return d
