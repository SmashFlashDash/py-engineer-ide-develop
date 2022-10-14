from enum import Enum

from PyQt5.QtWidgets import QMessageBox, QDockWidget
from PyQt5.QtCore import Qt

class Commons:
    '''
    Различные статик-методы для формирования простейших интерфейсов     
    '''
    @staticmethod
    def WarningBox(title, text, parent=None):
        box = QMessageBox(QMessageBox.Warning, title, text, QMessageBox.NoButton, parent)
        box.setAttribute(Qt.WA_DeleteOnClose)
        box.addButton('ОК', QMessageBox.AcceptRole)
        return BoxResult(box.exec())
    
    @staticmethod
    def InfoBox(title, text, parent=None):
        box = QMessageBox(QMessageBox.Information, title, text, QMessageBox.NoButton, parent)
        box.setAttribute(Qt.WA_DeleteOnClose)
        box.addButton('ОК', QMessageBox.AcceptRole)
        return BoxResult(box.exec())

    @staticmethod
    def YesNoCancelBox(title, text, parent=None):
        box = QMessageBox(QMessageBox.Information, title, text, QMessageBox.NoButton, parent)
        box.setAttribute(Qt.WA_DeleteOnClose)
        box.addButton('Да', QMessageBox.YesRole)
        box.addButton('Нет', QMessageBox.NoRole)
        box.addButton('Отмена', QMessageBox.RejectRole)
        return BoxResult(box.exec())

    @staticmethod
    def YesNoBox(title, text, parent=None):
        box = QMessageBox(QMessageBox.Information, title, text, QMessageBox.NoButton, parent)
        box.setAttribute(Qt.WA_DeleteOnClose)
        box.addButton('Да', QMessageBox.YesRole)
        box.addButton('Нет', QMessageBox.NoRole)
        return BoxResult(box.exec())

class BoxResult(Enum):
    '''
    Результат все всплывающих окон
    '''
    YES = 0
    NO = 1
    CANCEL = 2

class Revertable:
    '''
    Представляет собой значение любого типа, 
    которое в любой момент времени можно откатить к предыдущему состоянию
    '''
    def __init__(self, value):
        self.__old_val = value
        self.__cur_val = value
    @property
    def val(self):
        return self.__cur_val
    @val.setter
    def val(self, value):
        self.__old_val = self.__cur_val
        self.__cur_val = value        
    def revert(self):
        self.__cur_val = self.__old_val

class IvkDockWidget(QDockWidget):
    def __init__(self, parent):
        super().__init__(parent)
    
    def closeEvent(self, *args, **kwargs):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)

    