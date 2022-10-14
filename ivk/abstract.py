from abc import ABC, abstractmethod

class AbstractExchange(ABC):

    @staticmethod
    @abstractmethod  
    def init():
        '''Открытие приложение, инициализация модуля обмена'''
        pass
    
    @staticmethod 
    @abstractmethod 
    def onClose():
        '''Закрытие приложения'''
        pass
    
    @staticmethod 
    @abstractmethod 
    def getRootCommandNodeName():
        '''Определение названия для группы комманд в панели комманд, например:
        return 'МКА'
        '''
        pass

    @staticmethod 
    @abstractmethod 
    def getRootCommandNodeDescription():
        '''Определение описания для группы комманд в панели комманд, например:
        return 'Команды категории "МКА" предназначны для выдачи в КПА КПИ и РК.'
        '''
        pass
    
    @staticmethod
    @abstractmethod 
    def getModuleFilter():
        '''Определение списка классов, которые нужно подтянуть из cpi_framework, например:
        return ['omka']
        '''
        pass


    @staticmethod
    @abstractmethod 
    def getAdditionalCommands():
        '''Определение дополнительных комманд, которые нужно добавить в панельку:
        return [{
            'name' : 'sleep',
            'import_string' : 'from time import sleep',
            'description' : 'Выполняет задержку на указанное число секунд \nнапример sleep(0.2) выполнит задержку на 200мс',
            'params' : ['seconds'],
            'values' : ['0.5'],
            'keyword' : [False],
            'translation' : 'Задержка',
            'cat' : 'Общие'
        }]
        '''
        pass
    
    @staticmethod
    @abstractmethod 
    def getCpiFrameworkDestinations():
        '''Определение списка пунктов назначения для команд из cpi_framework, например:
        return ['ТКС', 'УЦО1', 'УЦО2']
        '''
        pass
    
    @staticmethod
    @abstractmethod 
    def send(queue_label, data):
        '''Отправка комманды по назначению, параметры:
        queue_label - пункт назначения
        data - данные для отправки
        '''
        pass
    
    @staticmethod
    @abstractmethod  
    def initDocks(parent, tabs_widget):
        '''Инициализация док-виджетов, возвращает массив с виджетами'''
        pass