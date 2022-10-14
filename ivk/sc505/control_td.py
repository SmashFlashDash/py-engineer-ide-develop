from ivk import config

class TerminalDevice:
    MESSAGES_TO_TD = {
        'Старт' : {
            'cmd' : 'START',
            'description' : 'Включение оконечного устройства'
        },
        'Стоп' : {
            'cmd' : 'STOP',
            'description' : 'Отключение оконечного устройства'
        },
        'Статус' : {
            'cmd' : 'STATUS',
            'description' : 'Проверка состояния окончного устройства'
        }
        # 'ВыходИБГФ' : {
        #     'id' : 0x01,
        #     'description' : 'Управление коммутацией выходов ИГБФ (имитатор генератора батареи фотоэлектрической). Четыре 8ми битовых целых числа, каждый бит (0-7) ' +
        #                     'отвечает за состояние соответствующего выхода (1-8 для первого числа, 9-16 для второго числа, 17-24 для третьего числа, ' +
        #                     '25-32 для четвертого числа соответственно). Значение битов: 0 выход отключен, 1 выход включен',
        #     'params' : [
        #         { 'name' : 'out', 
        #           'type' : list,
        #           'subtype' : int,
        #           'default' : '[0xFF, 0xFF, 0xFF, 0xFF]', 
        #           'check' : lambda lst: len(lst) == 4 and all(x >= 0 and x <= 0xFF for x in lst), 
        #           'check_msg' : 'Список должен содержать 4 числа и каждое число должно находиться в диапазоне от 0x0 до 0xFF',
        #           'to_data' : lambda lst: struct.pack('>4B', *lst)}
        #     ],
        #     'responce_id' : 0x81,
        #     'get_responce_class' : lambda: IBGFResponce()
        # },
    }

    @staticmethod
    def MSG(name, **kwargs):
        if name not in TerminalDevice.MESSAGES_TO_TD:
            raise Exception('Неопознанный код команды "%s"' % name)
        msg = TerminalDevice.MESSAGES_TO_TD[name]
        result = {'cmd' : msg['cmd']}
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
                result[param['name']] = param['to_data'](val)
        return result
