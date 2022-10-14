import struct
from ivk.scOMKA import BCH

class BrkProto():
    
    @staticmethod
    def CreateUDPPacket(dataBytes, packetType):
        '''оборачивает 114 байт в 122 байта'''
        packet = struct.pack(">H", packetType)
        packet += struct.pack(">I", 0)
        packet += struct.pack(">H", len(dataBytes))
        for b in dataBytes:
            packet += struct.pack("B", b)
        return packet

    @staticmethod
    def WrapBCH114(data):
        data = BrkProto.__makeBCH(data)
        data = BrkProto.__make114(data)
        return data
    @staticmethod
    def WrapBF(data, ka_id):
        return BrkProto.WrapBCH114(BrkProto.__wrapTKI(data, ka_id, 63))
    @staticmethod
    def WrapOpenOTC(data, ka_id):
        return BrkProto.WrapBCH114(BrkProto.__wrapTKI(data, ka_id, 61))
    @staticmethod
    def WrapClosedOTC(data, ka_id):
        return BrkProto.WrapBCH114(BrkProto.__wrapTKI(data, ka_id, 0))
    @staticmethod
    def WrapCPI(data, ka_id):
        return BrkProto.WrapBCH114(BrkProto.__wrapTKI(data, ka_id, 3))
    
    @staticmethod
    def __wrapTKI(data, ka_id, typeTKI):
        '''
        Оборачивает данные в 91 байт (пустые байты заполняются нулями)
        typeTKI 0 - РКз, 3 - КПИ, 61-РКо, 63 ХК
        '''
        '''
            !!! реализовать Флаг установки счетчика, и всю бежевую часть для РКз и КПИ
        '''
        alldata = [0x0 for i in range(91)]
        #заполняем 5 байт заголовка ТК запросного канала
        alldata[0] = (ka_id>>8)&3#10 бит - идентификатор КА
        alldata[1] = ka_id&0xff#10 бит - идентификатор КА
        virtual_cnannel_id = typeTKI
        alldata[2] = (virtual_cnannel_id&63)<<2 #старшие 6 бит - идентификатор ВК
        alldata[3] = 90&0xff #константа 90
        if typeTKI == 0 or typeTKI == 3:
            alldata[4] = 0 #номер последовательности - заполняется далее в другом софте
            alldata[5:12+1] = [0 for i in range(8)]#Синхропосылка
            alldata[13:16+1] = [0 for i in range(4)]#Наземное время с момента включения БАРЛ
            alldata[17:18+1] = [0, 0]#Наземный счетчик кадров в текущей секунде
            alldata[19:20+1] = [0, 0]#нули
            alldata[21:84 + 1] = data
            alldata[85:88+1] = [0, 0, 0, 0] #Поле аутентификации
        elif typeTKI == 61 or typeTKI == 63:
            alldata[4] = 0
            alldata[5:89] = data
        crc = BrkProto.__crc16_ccitt(alldata, 89)
        alldata[89] = (crc>>8)&0xff
        alldata[90] = (crc)&0xff
        return alldata
    
    @staticmethod
    def __makeBCH(data):
        '''
        Оборачивает 91 байт кадра в БЧХ на выходе 104 байта
        '''
        BCH_NETTO_SIZE = BCH.CODE_BLOCK_SIZE - 1
        result = []
        counter = 0
        sreg = BCH.encodeStart()
        for b in data:
            if counter == 0:
                sreg = BCH.encodeStart()
            result.append(b)
            sreg = BCH.encodeStep(sreg, b)
            counter += 1
            if counter >= BCH_NETTO_SIZE:
                code = BCH.encodeStop(sreg)
                result.append(code)
                counter = 0
        return result

    @staticmethod
    def __make114(data):
        '''
        Оборачивает 104 байта стартовой и стоповой 
        последовательностью - на выходе 114 байт
        '''
        result = [0xeb, 0x90]
        for  b in data:
            result.append(b)
        #Можно сделать result.extend(b)
        result.extend([0xc5, 0xc5, 0xc5, 0xc5, 0xc5, 0xc5, 0xc5, 0x79])
        return result
    
    @staticmethod
    def __crc16_ccitt(data_p, length):
        '''
        standart CRC16_CCITT implementation with seed 0xffff
        '''
        data = data_p
        if isinstance(data_p, str):
            data = [ord(i) for i in data_p]
        crc = 0xFFFF
        x = 0
        pointer = 0
        while length > 0:
            x = crc >> 8 ^ data[pointer]
            x ^= x>>4
            crc = (crc << 8) ^ ((x << 12)) ^ ((x <<5)) ^ x
            crc = crc & 0xffff
            pointer += 1
            length -= 1   
        return crc&0xffff

#data = BrkProto.WrapCPI()
# if len(data) == 91:
#     data = BrkProto.WrapBF(data)
# elif len(data) == 84:
#     data = BrkProto.WrapOpenOTC(data)
# elif len(data) == 64:
#     data = BrkProto.WrapClosedOTC(data)
# else:
#     data = None
#     sys.stderr.write('\nНе определена РК или ХК')