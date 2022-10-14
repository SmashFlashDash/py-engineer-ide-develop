import ctypes, struct, time
from ivk import config
from cpi_framework.utils.BinaryStream import BinaryStreamLE
from cpi_framework.utils.basecpi_abc import AsciiHex
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ivk.pydevd_runner import PyDevDRunner

def getSimpleCommandsDP():
    commands = [
        {
            'name' : 'DP1',
            'translation' : 'УЦО1',
            'import_string' : 'from ivk.sc505.simplifications import DP1',
            'description' : 'Отправка данных в УЦО1',
            'params' : ['data', 'timeout', 'aes_key', 'iv'],
            'values' : ['None', '11', '[0xAA for i in range(32)]', 'None'],
            'keyword' : [False, True, True, True],
            'cat' : 'Общие',
            'ex_send' : False
        },
        {
            'name' : 'DP2',
            'translation' : 'УЦО2',
            'import_string' : 'from ivk.sc505.simplifications import DP2',
            'description' : 'Отправка данных в УЦО2',
            'params' : ['data', 'timeout', 'aes_key', 'iv'],
            'values' : ['None', '11', '[0xAA for i in range(32)]', 'None'],
            'keyword' : [False, True, True, True],
            'cat' : 'Общие',
            'ex_send' : False
        },
        {
            'name' : 'GET_RCD',
            'translation' : 'Получить данные ИОК',
            'import_string' : 'from ivk.sc505.simplifications import GET_RCD',
            'description' : 'Получает данные ИОК УЦО из общего хранилища по названию (при передачи ключа шифрования, отличного от None, будет произведена дешифровка тела ИОК в decrypted_body)',
            'params' : ['name', 'aes_key'],
            'values' : ['"ИОК_2_10"', None],
            'keyword' : [False, False],
            'cat' : 'Общие',
            'ex_send' : False
        },
        {
            'name' : 'SEND_KEY_ROKOT',
            'translation' : 'Ключ в ROKOT',
            'import_string' : 'from ivk.sc505.simplifications import SEND_KEY_ROKOT',
            'description' : 'Отправить новый ключ шифрования в ROKOT (в виде байт)',
            'params' : ['key'],
            'values' : ['b\'\''],
            'keyword' : [False],
            'cat' : 'Общие',
            'ex_send' : False
        }
    ]
    return commands

def DP1(data, timeout=11, aes_key=bytes([0xAA for i in range(32)]), iv=None):
    return config.get_exchange().send('УЦО1', data, timeout, aes_key, iv)

def DP2(data, timeout=11, aes_key=bytes([0xAA for i in range(32)]), iv=None):
    return config.get_exchange().send('УЦО2', data, timeout, aes_key, iv)

def SEND_KEY_ROKOT(key):
    config.updData('ROKOT_NEW_AES_KEY', str(AsciiHex(key)))

def GET_RCD(name, aes_key=None):
    if not name.startswith('ИОК_'):
        raise Exception("Название ИОК должно начинаться с \"ИОК_\"")
    
    if config.getData('RCD_SEMAPHORE') is not None:
        while config.getData('RCD_SEMAPHORE'):
            time.sleep(0.05)
    config.updData('RCD_SEMAPHORE', True)
    data = config.getData(name)
    config.updData(name, None)
    config.updData('RCD_SEMAPHORE', False)

    if data is None:
        return None
    rcd = RCD()
    rcd.fromDict(data)

    if aes_key is not None:
        aad = rcd.total.bytes[:6]
        crypt_data = rcd.total.bytes[6:60]
        iv = int.from_bytes(rcd.total.bytes[60:], byteorder='little')
        iv = iv << 2
        hack_iv = iv.to_bytes(5, byteorder='little') + struct.pack('b', 0)*7
        aesgcm = AESGCM(aes_key)
        rcd.decrypted_body = aesgcm.decrypt(hack_iv, crypt_data, aad)  # TODO Изменить aesgcm.decrypt (Длина MAC: 16->8)
    return rcd


class RCD(BinaryStreamLE):
    _fields_ = [
        ('num', ctypes.c_uint16, 6),
        ('addnum', ctypes.c_uint16, 5),
        ('wordcount', ctypes.c_uint16, 5),
        ('body', ctypes.c_uint16*31)
    ]

    _field_names_ = [
        ('num', 'номер_ИОК'),
        ('addnum', 'подномер_ИОК'),
        ('wordcount', 'колво_слов'),
        ('body', 'данные')
    ]

    _additional_fields_ = [
        'total'
    ]