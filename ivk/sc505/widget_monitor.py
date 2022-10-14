from datetime import datetime
import functools
import re, threading, sys, time
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QBoxLayout, QDockWidget, QLabel, QPushButton, QComboBox, QCheckBox, QTabWidget,QVBoxLayout
from PyQt5.QtGui import QColor, QTextCursor, QFontMetrics, QIcon, QPixmap, QPalette 
from PyQt5.QtCore import Qt, QEventLoop, QObject, pyqtSignal

from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.labels import TrueFalseNoneIconLabel, AlignLabel, StyledLabel

from ivk.sc505.control_td import TerminalDevice
from ivk import config


class MonitorWidget(QDockWidget):
    monitorSignal = pyqtSignal(object)
    disconnectSignal = pyqtSignal()
    
    def __init__(self, parent, tabs_widget):
        super().__init__(parent)
        self.setWindowTitle('Монитор ОУ')
        self.tabs_widget = tabs_widget
        self.monitorSignal.connect(self.__updateUi)
        self.disconnectSignal.connect(lambda: [device['led'].setState(None) for device in self.device.values()])

        self.colored_labels = { }
        self.colored_labels_dispatcher_thread = threading.Thread(target=self.dispatchLabelColors, daemon=True)
        self.colored_labels_dispatcher_thread.start()
        self.colored_labels_lock = threading.Lock()

        self.devices = { }
        td_hint = 10
        for name, queue in config.getConf('amqp_queues').items():
            led = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png', 'Включен', 'Отключен', 'Неизвестно', None)
            
            label = QLabel(name)
            w = label.sizeHint().width() + 4
            if w > td_hint:
                td_hint = w

            button_on = QPushButton("Включить")
            button_on.clicked.connect(functools.partial(lambda dest, msg: config.get_exchange().send(dest, TerminalDevice.MSG(msg)), name, 'Старт'))
            button_off = QPushButton("Отключить")
            button_off.clicked.connect(functools.partial(lambda dest, msg: config.get_exchange().send(dest, TerminalDevice.MSG(msg)), name, 'Стоп'))
            
            label_counter_cpi = StyledLabel('?', object_name='consolasBoldFont') if queue != 'BOI' else None
            
            self.devices[queue] = {
                'name' : name,
                'led' : led,
                'label' : label,
                'button_on' : button_on,
                'button_off' : button_off,
                'label_counter_cpi' : label_counter_cpi
            }

        self.setWidget(QWidget(self))
        lb = QBoxLayoutBuilder(self.widget(), QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        
        for device in self.devices.values():
            lb.hbox(spacing=5) \
                .add(device['led']) \
                .add(device['label'], fix_w=td_hint) \
                .add(device['button_on']) \
                .add(device['button_off'])
            if device['label_counter_cpi'] is None:
                lb.stretch().up()
            else:
                lb.add(QLabel("Счетчик КПИ:")).add(device['label_counter_cpi']).stretch().up()
        lb.stretch()

        self.hide()
    
    def updateStatus(self, status):
        self.monitorSignal.emit(status)
    
    def disconnect(self):
        self.disconnectSignal.emit()

    def __updateUi(self, status):
        if 'queue' not in status:
            return
        if 'counter_cpi' in status:
            self.setLabelText(self.devices[status['queue']]['label_counter_cpi'], str(status['counter_cpi']))
        elif 'status' in status:
            self.devices[status['queue']]['led'].setState(status['status'])

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

    def showEvent(self, event):
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
        return '505MonitorWidget'
    
    def getMenuParams(self):
        return {
            'icon' : 'res/server_icon.png',
            'text' : 'Монитор ОУ',
            'status_tip' : 'Окно мониторинга оконечных устройств'
        }