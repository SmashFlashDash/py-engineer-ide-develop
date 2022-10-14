from datetime import datetime
import re, threading, sys, time
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QBoxLayout, QDockWidget, QLabel, QPushButton, QComboBox, QCheckBox, QTabWidget, QVBoxLayout
from PyQt5.QtGui import QColor, QTextCursor, QFontMetrics, QIcon, QPixmap, QPalette 
from PyQt5.QtCore import Qt, QEventLoop, QObject, pyqtSignal

from ivk import config
from ivk.scOMKA.controll_scpi import SCPI, SCPIResponce
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.labels import TrueFalseNoneIconLabel, AlignLabel, StyledLabel, GifLabelSaveSpace


class ScpiWidget(QDockWidget):
    scpiSignal = pyqtSignal(object)
    disconnectSignal = pyqtSignal(str)
    loadingSignal = pyqtSignal(str, bool)

    LINES_PER_TAB = 2
    ITEMS_PER_LINE = 6

    def __init__(self, parent, tabs_widget):
        super().__init__(parent)
        self.setWindowTitle('Источники питания')
        self.tabs_widget = tabs_widget
        self.scpiSignal.connect(self.updateUi)
        self.disconnectSignal.connect(lambda device: self.checkStateChanged(device, Qt.Unchecked))
        self.loadingSignal.connect(self.onLoadingSignal)

        self.colored_labels = { }
        self.colored_labels_dispatcher_thread = threading.Thread(target=self.dispatchLabelColors, daemon=True)
        self.colored_labels_dispatcher_thread.start()
        self.colored_labels_lock = threading.Lock()

        self.monitor_checkbox = QCheckBox('Монитор состояния источников питания', self)
        self.monitor_checkbox.stateChanged.connect(lambda state: self.checkStateChanged(None, state))

        self.tabbed_checkbox = QCheckBox('Разбить по вкладкам', self)
        self.tabbed_checkbox.setChecked(True)
        self.tabbed_checkbox.stateChanged.connect(lambda state: self.buildLayout(state != Qt.Unchecked))

        self.protected_widgets = [self.monitor_checkbox, self.tabbed_checkbox]

        self.setWidget(QWidget(self))
        self.lb = QBoxLayoutBuilder(self.widget(), QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=8)
        self.buildLayout(self.tabbed_checkbox.isChecked())
        self.hide()

    def recreateDevices(self):
        devices = config.odict()
        for name in SCPI.SCPI_DEVICES:
            label_name = AlignLabel(name, Qt.AlignCenter)
            loading_widget = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)
            icon_output = TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                 'Подача питания включена', 'Подача питания отключена', 'Неизвестно',
                                                 None, align=Qt.AlignCenter)
            label_voltage = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
            label_current = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
            devices[name] = {'label_name': label_name, 'icon_output': icon_output, 'label_voltage': label_voltage,
                             'label_current': label_current, 'loading_widget': loading_widget}
        self.devices = devices

    def buildLayout(self, tabbed):
        self.colored_labels.clear()
        self.recreateDevices()
        self.lb.clearAll(self.protected_widgets)
        self.lb.hbox(spacing=5).add(self.monitor_checkbox).stretch().add(self.tabbed_checkbox).up()

        if tabbed:
            tab_widget = QTabWidget(self.widget())
            tab_widget.setMovable(False)
            tab_widget.setTabsClosable(False)
            self.lb.add(tab_widget)

            w = QWidget(tab_widget)
            lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=8)

            i = 0
            first_name = None
            last_name = None
            for name, device in self.devices.items():
                if i % (ScpiWidget.LINES_PER_TAB * ScpiWidget.ITEMS_PER_LINE) == 0:
                    if i > 0:
                        lb.up().stretch()
                        tab_widget.addTab(w, '%s - %s' % (first_name, last_name))
                        w = QWidget(tab_widget)
                        lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=8)
                    lb.hbox(spacing=5)
                    first_name = name
                elif i % ScpiWidget.ITEMS_PER_LINE == 0:
                    if i > 0:
                        lb.up()
                    lb.hbox(spacing=5)
                last_name = name
                lb.vbox(spacing=3) \
                    .hbox(spacing=3) \
                        .stretch() \
                        .add(device['icon_output']).add(device['label_name']).add(device['loading_widget']).fix(16, 16) \
                        .stretch() \
                        .up() \
                    .add(device['label_voltage']) \
                    .add(device['label_current']) \
                    .up()
                i += 1
            if i % (ScpiWidget.LINES_PER_TAB * ScpiWidget.ITEMS_PER_LINE) != 0:
                while i % ScpiWidget.ITEMS_PER_LINE != 0:
                    lb.vbox(spacing=3) \
                        .hbox(spacing=3) \
                        .stretch().add(AlignLabel("", Qt.AlignCenter)).stretch() \
                        .up() \
                        .up()
                    i += 1
                lb.up().stretch()
                tab_widget.addTab(w, '%s - %s' % (first_name, last_name))

        else:
            i = 0
            for name, device in self.devices.items():
                if i % ScpiWidget.ITEMS_PER_LINE == 0:
                    if i > 0:
                        self.lb.up()
                    self.lb.hbox(spacing=5)
                self.lb.vbox(spacing=3) \
                    .hbox(spacing=3) \
                        .stretch() \
                        .add(device['icon_output']).add(device['label_name']).add(device['loading_widget']).fix(16, 16) \
                        .stretch() \
                        .up() \
                    .add(device['label_voltage']) \
                    .add(device['label_current']) \
                    .up()
                i += 1

            while i % ScpiWidget.ITEMS_PER_LINE != 0:
                self.lb.vbox(spacing=3) \
                    .hbox(spacing=3) \
                    .stretch().add(AlignLabel("", Qt.AlignCenter)).stretch() \
                    .up() \
                    .up()
                i += 1
            self.lb.up().stretch()
    
    def scpiIncome(self, scpi_responce):
        self.scpiSignal.emit(scpi_responce)
    def scpiDisconnect(self, device):
        self.disconnectSignal.emit(device)
    def setLoading(self, device, loading):
        self.loadingSignal.emit(device, loading)

    def onLoadingSignal(self, device, loading):
        device = self.devices[device]
        device['loading_widget'].setVisible(loading)

    def updateUi(self, scpi_responce):
        if scpi_responce.unpacked is None:
            return
        device = self.devices[scpi_responce.device]

        if scpi_responce.name == 'ЗапрСост':
            device['icon_output'].setState(scpi_responce.unpacked == 1)
        elif scpi_responce.name == 'ЗапрНапряж':
            self.setLabelText(device['label_voltage'], '%.3f В' % scpi_responce.unpacked)
        elif scpi_responce.name == 'ЗапрТок':
            self.setLabelText(device['label_current'], '%.3f А' % scpi_responce.unpacked)
        
        if SCPI.SCPI_DEVICES[scpi_responce.device]['send_queue'].empty():
            self.onLoadingSignal(scpi_responce.device, False)
       

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
            #label.setStyleSheet("background-color: rgb(255, 0, 0);")
    
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
                    #label.setStyleSheet("background-color: rgb(0, 0, 255);")
            self.colored_labels_lock.release()

    def checkStateChanged(self, device, state):
        if state != Qt.Unchecked:
            return
        if device is None:
            for d in self.devices.values():
                d['icon_output'].setState(None)
                d['label_voltage'].setText('?')
                d['label_current'].setText('?')
                d['loading_widget'].setVisible(False)
        else:
            self.devices[device]['icon_output'].setState(None)
            self.devices[device]['label_voltage'].setText('?')
            self.devices[device]['label_current'].setText('?')
            self.devices[device]['loading_widget'].setVisible(False)
        
            

    def showEvent(self, event):
        super().showEvent(event)
    
    def closeEvent(self, event):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)
        super().closeEvent(event)

    def saveSettings(self):
        return {
            'monitor_check_state' : self.monitor_checkbox.checkState()
        }
    
    def restoreSettings(self, settings):
        self.monitor_checkbox.setCheckState(settings['monitor_check_state'])
        
    def settingsKeyword(self):
        return 'MKASCPIWidget'
    
    def getMenuParams(self):
        return {
            'icon' : 'res/power_supply.png',
            'text' : 'Окно источников питания',
            'status_tip' : 'Окно мониторинга источников питания шкафа ИВК'
        }
