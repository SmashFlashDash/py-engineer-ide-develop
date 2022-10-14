from datetime import datetime
import re, threading, sys, time
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QBoxLayout, \
    QDockWidget, QLabel, QPushButton, QComboBox, QCheckBox, QTabWidget, QVBoxLayout
from PyQt5.QtGui import QColor, QTextCursor, QFontMetrics, QIcon, QPixmap, QPalette
from PyQt5.QtCore import Qt, QEventLoop, QObject, pyqtSignal

from ivk.scOMKA.controll_iccell import ICCELL
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.labels import TrueFalseNoneIconLabel, AlignLabel, StyledLabel, GifLabelSaveSpace
from ivk import config


class IcCellWidget(QDockWidget):
    iccellSignal = pyqtSignal(object)
    disconnectSignal = pyqtSignal()
    loadingSignal = pyqtSignal(str, bool)

    def __init__(self, parent, tabs_widget):
        super().__init__(parent)
        self.setWindowTitle('Ячейка ПИ')
        self.tabs_widget = tabs_widget
        self.iccellSignal.connect(self.updateUi)
        self.disconnectSignal.connect(lambda: [self.checkStateChanged(msg, Qt.Unchecked) for msg in (
        'ЗапрСост', 'ЗапрСопрИзол', 'ЗапрНараб', 'ЗапрНапряжСигТЛМ', 'ЗапрНапряж', 'ЗапрТемпАБ')])
        self.loadingSignal.connect(self.onLoadingSignal)

        self.colored_labels = {}
        self.colored_labels_dispatcher_thread = threading.Thread(target=self.dispatchLabelColors, daemon=True)
        self.colored_labels_dispatcher_thread.start()
        self.colored_labels_lock = threading.Lock()

        self.sost_checkbox = QCheckBox('ЗапрСост', self)
        self.sost_checkbox.stateChanged.connect(lambda state: self.checkStateChanged('ЗапрСост', state))
        self.sost_loading = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)

        self.sopriz_checkbox = QCheckBox('ЗапрСопрИзол', self)
        self.sopriz_checkbox.stateChanged.connect(lambda state: self.checkStateChanged('ЗапрСопрИзол', state))
        self.sopriz_loading = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)

        self.narab_checkbox = QCheckBox('ЗапрНараб', self)
        self.narab_checkbox.stateChanged.connect(lambda state: self.checkStateChanged('ЗапрНараб', state))
        self.narab_loading = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)

        self.naprtlm_checkbox = QCheckBox('ЗапрНапряжСигТЛМ', self)
        self.naprtlm_checkbox.stateChanged.connect(lambda state: self.checkStateChanged('ЗапрНапряжСигТЛМ', state))
        self.naprtlm_loading = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)

        self.napr_checkbox = QCheckBox('ЗапрНапряж', self)
        self.napr_checkbox.stateChanged.connect(lambda state: self.checkStateChanged('ЗапрНапряж', state))
        self.napr_loading = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)

        self.tempab_checkbox = QCheckBox('ЗапрТемпАБ', self)
        self.tempab_checkbox.stateChanged.connect(lambda state: self.checkStateChanged('ЗапрТемпАБ', state))
        self.tempab_loading = GifLabelSaveSpace('res/loading_green_16.gif', visible=False)

        self.icon_ka_powered = TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                      'Питание подано', 'Питание не подано', 'Неизвестно', None,
                                                      align=Qt.AlignLeft)
        self.icon_emergency_button = TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                            'Кнопка нажата', 'Кнопка не нажата', 'Неизвестно', None,
                                                            align=Qt.AlignLeft)
        self.icon_p24V_converter1 = TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                           'Есть питание', 'Нет питания', 'Неизвестно', None,
                                                           align=Qt.AlignLeft)
        self.icon_p24V_converter2 = TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                           'Есть питание', 'Нет питания', 'Неизвестно', None,
                                                           align=Qt.AlignLeft)
        self.icon_ivk_counter_ok = TrueFalseNoneIconLabel('res/ok.png', 'res/error.png', 'res/unknown.png',
                                                          'Счетчик исправен', 'Счетчик неисправен', 'Неизвестно', None,
                                                          align=Qt.AlignLeft)
        self.icon_ka_counter_ok = TrueFalseNoneIconLabel('res/ok.png', 'res/error.png', 'res/unknown.png',
                                                         'Счетчик исправен', 'Счетчик неисправен', 'Неизвестно', None,
                                                         align=Qt.AlignLeft)
        self.label_run_time_ivk = StyledLabel('?', object_name='consolasBoldFont')
        self.label_run_time_ka = StyledLabel('?', object_name='consolasBoldFont')
        self.label_ka_voltage = StyledLabel('?', object_name='consolasBoldFont')
        self.label_resist_SEP_plus = StyledLabel('?', object_name='consolasBoldFont')
        self.label_resist_SEP_minus = StyledLabel('?', object_name='consolasBoldFont')

        self.led_connected_KI1 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_KI2 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_KI3 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_KI4 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_KMM = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_IPD = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_KST = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_IZD = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_IT = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                       'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                       align=Qt.AlignCenter)
        self.led_connected_IDT1 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                         'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                         align=Qt.AlignCenter)
        self.led_connected_IDT2 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                         'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                         align=Qt.AlignCenter)
        self.led_connected_IDT11 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                          'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)
        self.led_connected_IDT12 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                          'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)
        self.led_connected_IDT13 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                          'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)
        self.led_connected_IDT14 = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                          'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)
        self.led_connected_PST = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_IIK = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                        'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                        align=Qt.AlignCenter)
        self.led_connected_IN = TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png', 'res/led_grey.png',
                                                       'Есть связь', 'Нет связи', 'Неизвестно', None,
                                                       align=Qt.AlignCenter)

        self.icon_mode_IGBF = TrueFalseNoneIconLabel('res/automatic.png', 'res/manual.png', 'res/unknown.png',
                                                     'Автоматический режим', 'Ручной режим', 'Неизвестно', None,
                                                     align=Qt.AlignCenter)
        self.icon_mode_IAB = TrueFalseNoneIconLabel('res/automatic.png', 'res/manual.png', 'res/unknown.png',
                                                    'Автоматический режим', 'Ручной режим', 'Неизвестно', None,
                                                    align=Qt.AlignCenter)
        self.icon_mode_DV = TrueFalseNoneIconLabel('res/automatic.png', 'res/manual.png', 'res/unknown.png',
                                                   'Автоматический режим', 'Ручной режим', 'Неизвестно', None,
                                                   align=Qt.AlignCenter)
        self.icon_mode_ZD = TrueFalseNoneIconLabel('res/automatic.png', 'res/manual.png', 'res/unknown.png',
                                                   'Автоматический режим', 'Ручной режим', 'Неизвестно', None,
                                                   align=Qt.AlignCenter)
        self.icon_mode_MM = TrueFalseNoneIconLabel('res/automatic.png', 'res/manual.png', 'res/unknown.png',
                                                   'Автоматический режим', 'Ручной режим', 'Неизвестно', None,
                                                   align=Qt.AlignCenter)
        self.icon_mode_DS = TrueFalseNoneIconLabel('res/automatic.png', 'res/manual.png', 'res/unknown.png',
                                                   'Автоматический режим', 'Ручной режим', 'Неизвестно', None,
                                                   align=Qt.AlignCenter)

        self.commutations_outs = config.odict(
            ('commutation_IGBF_1', {'title': 'ИГБФ1', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_2', {'title': 'ИГБФ2', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_3', {'title': 'ИГБФ3', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_4', {'title': 'ИГБФ4', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_5', {'title': 'ИГБФ5', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_6', {'title': 'ИГБФ6', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_7', {'title': 'ИГБФ7', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_8', {'title': 'ИГБФ8', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_9', {'title': 'ИГБФ9', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                       'res/unknown_on_off.png',
                                                                                       'Выход включен',
                                                                                       'Выход отключен', 'Неизвестно',
                                                                                       None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_10', {'title': 'ИГБФ10', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_11', {'title': 'ИГБФ11', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_12', {'title': 'ИГБФ12', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_13', {'title': 'ИГБФ13', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_14', {'title': 'ИГБФ14', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_15', {'title': 'ИГБФ15', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_16', {'title': 'ИГБФ16', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_17', {'title': 'ИГБФ17', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_18', {'title': 'ИГБФ18', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_19', {'title': 'ИГБФ19', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_20', {'title': 'ИГБФ20', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_21', {'title': 'ИГБФ21', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_22', {'title': 'ИГБФ22', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_23', {'title': 'ИГБФ23', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_24', {'title': 'ИГБФ24', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_25', {'title': 'ИГБФ25', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_26', {'title': 'ИГБФ26', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_27', {'title': 'ИГБФ27', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_28', {'title': 'ИГБФ28', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_29', {'title': 'ИГБФ29', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_30', {'title': 'ИГБФ30', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_31', {'title': 'ИГБФ31', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),
            ('commutation_IGBF_32', {'title': 'ИГБФ32', 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png',
                                                                                         'res/unknown_on_off.png',
                                                                                         'Выход включен',
                                                                                         'Выход отключен', 'Неизвестно',
                                                                                         None, align=Qt.AlignCenter)}),

            ('commutation_IAB', {'title': 'ИАБ',
                                 'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                                  'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                                  align=Qt.AlignCenter)}),
            ('commutation_MM_X1', {'title': 'MM_X1',
                                   'widget': TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png',
                                                                    'res/led_grey.png', 'Положительная полярность',
                                                                    'Отрицательная полярность', 'Неизвестно', None,
                                                                    align=Qt.AlignCenter)}),
            ('commutation_MM_X2', {'title': 'MM_X2',
                                   'widget': TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png',
                                                                    'res/led_grey.png', 'Положительная полярность',
                                                                    'Отрицательная полярность', 'Неизвестно', None,
                                                                    align=Qt.AlignCenter)}),
            ('commutation_MM_Y1', {'title': 'MM_Y1',
                                   'widget': TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png',
                                                                    'res/led_grey.png', 'Положительная полярность',
                                                                    'Отрицательная полярность', 'Неизвестно', None,
                                                                    align=Qt.AlignCenter)}),
            ('commutation_MM_Y2', {'title': 'MM_Y2',
                                   'widget': TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png',
                                                                    'res/led_grey.png', 'Положительная полярность',
                                                                    'Отрицательная полярность', 'Неизвестно', None,
                                                                    align=Qt.AlignCenter)}),
            ('commutation_MM_Z1', {'title': 'MM_Z1',
                                   'widget': TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png',
                                                                    'res/led_grey.png', 'Положительная полярность',
                                                                    'Отрицательная полярность', 'Неизвестно', None,
                                                                    align=Qt.AlignCenter)}),
            ('commutation_MM_Z2', {'title': 'MM_Z2',
                                   'widget': TrueFalseNoneIconLabel('res/led_green.png', 'res/led_red.png',
                                                                    'res/led_grey.png', 'Положительная полярность',
                                                                    'Отрицательная полярность', 'Неизвестно', None,
                                                                    align=Qt.AlignCenter)}),
            (' ', {'title': ' ', 'widget': AlignLabel(' ', Qt.AlignCenter)}),

            ('out_DS1', {'title': 'ДС1',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS2', {'title': 'ДС2',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS3', {'title': 'ДС3',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS4', {'title': 'ДС4',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS5', {'title': 'ДС5',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS6', {'title': 'ДС6',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS7', {'title': 'ДС7',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_DS8', {'title': 'ДС8',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),

            ('out_DV', {'title': 'ДВ',
                        'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                         'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                         align=Qt.AlignCenter)}),
            ('out_ZD1', {'title': 'ЗД1',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_ZD2', {'title': 'ЗД2',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_ZD3', {'title': 'ЗД3',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),
            ('out_ZD4', {'title': 'ЗД4',
                         'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                          'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                          align=Qt.AlignCenter)}),

            ('out_1otklBS', {'title': '1ОтклБС',
                             'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                              'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                              align=Qt.AlignCenter)}),
            ('out_2otklBS', {'title': '2ОтклБС',
                             'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                              'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                              align=Qt.AlignCenter)}),
            ('out_1kotd', {'title': '1Котд',
                           'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                            'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                            align=Qt.AlignCenter)}),
            ('out_2kotd', {'title': '2Котд',
                           'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                            'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                            align=Qt.AlignCenter)}),
            ('out_blokBS', {'title': 'БлокБС',
                            'widget': TrueFalseNoneIconLabel('res/on.png', 'res/off.png', 'res/unknown_on_off.png',
                                                             'Выход включен', 'Выход отключен', 'Неизвестно', None,
                                                             align=Qt.AlignCenter)})
        )
        self.label_volt_chan_1 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_2 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_3 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_4 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_5 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_6 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_7 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_volt_chan_8 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')

        self.label_temp_ab_chan_1 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_2 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_3 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_4 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_5 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_6 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_7 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_8 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_9 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_10 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_11 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')
        self.label_temp_ab_chan_12 = AlignLabel('?', Qt.AlignCenter, object_name='consolasBoldFont')

        hint1 = QLabel('Напряжение БС КА').sizeHint().width() + 4
        hint2 = QLabel('Счетчик наработки ИВК').sizeHint().width() + 2
        hint3 = QLabel('Сопротивление СЭП+').sizeHint().width() + 2
        hint4 = QLabel('ИДТ1№4').sizeHint().width() + 2
        hint5 = QLabel('ИГБФ').sizeHint().width() + 2

        l = QLabel('88.888 В')
        l.setStyleSheet('font: 10pt "Consolas";')
        hint6 = l.sizeHint().width() + 2
        l.setText('-888.8 °С')
        hint7 = l.sizeHint().width() + 2

        self.setWidget(QWidget(self))
        lb = QBoxLayoutBuilder(self.widget(), QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        lb.hbox(spacing=5, margins=(5, 5, 5, 5), title='Мониторинг') \
            .vbox(spacing=5, aligment=Qt.AlignTop) \
            .hbox(spacing=3).add(self.sost_checkbox).add(self.sost_loading).fix(16, 16).up() \
            .hbox(spacing=3).add(self.sopriz_checkbox).add(self.sopriz_loading).fix(16, 16).up() \
            .up(fix_w=hint1).stretch() \
            .vbox(spacing=5, aligment=Qt.AlignTop) \
            .hbox(spacing=3).add(self.narab_checkbox).add(self.narab_loading).fix(16, 16).up() \
            .hbox(spacing=3).add(self.naprtlm_checkbox).add(self.naprtlm_loading).fix(16, 16).up() \
            .up(fix_w=hint2).stretch() \
            .vbox(spacing=5, aligment=Qt.AlignTop) \
            .hbox(spacing=3).add(self.napr_checkbox).add(self.napr_loading).fix(16, 16).up() \
            .hbox(spacing=3).add(self.tempab_checkbox).add(self.tempab_loading).fix(16, 16).up() \
            .up(fix_w=hint3) \
            .up() \
            .hbox(spacing=5, margins=(5, 5, 5, 5), title='Основные') \
            .vbox(spacing=5, aligment=Qt.AlignTop) \
            .hbox(spacing=5).add(AlignLabel('Питание КА', Qt.AlignRight), fix_w=hint1).add(self.icon_ka_powered).up() \
            .hbox(spacing=5).add(AlignLabel('Аварийная кнопка', Qt.AlignRight), fix_w=hint1).add(
            self.icon_emergency_button).up() \
            .hbox(spacing=5).add(AlignLabel('Напряжение БС КА:', Qt.AlignRight), fix_w=hint1).add(
            self.label_ka_voltage).up() \
            .up(fix_w=hint1).stretch() \
            .vbox(spacing=5, aligment=Qt.AlignTop) \
            .hbox(spacing=5).add(AlignLabel('Счетчик наработки КА', Qt.AlignRight), fix_w=hint2).add(
            self.icon_ka_counter_ok).up() \
            .hbox(spacing=5).add(AlignLabel('Счетчик наработки ИВК', Qt.AlignRight), fix_w=hint2).add(
            self.icon_ivk_counter_ok).up() \
            .hbox(spacing=5).add(AlignLabel('Наработка КА:', Qt.AlignRight), fix_w=hint2).add(
            self.label_run_time_ka).up() \
            .hbox(spacing=5).add(AlignLabel('Наработка ИВК:', Qt.AlignRight), fix_w=hint2).add(
            self.label_run_time_ivk).up() \
            .up(fix_w=hint2).stretch() \
            .vbox(spacing=5, aligment=Qt.AlignTop) \
            .hbox(spacing=5).add(AlignLabel('Питание 24В ПР1', Qt.AlignRight), fix_w=hint3).add(
            self.icon_p24V_converter1).up() \
            .hbox(spacing=5).add(AlignLabel('Питание 24В ПР2', Qt.AlignRight), fix_w=hint3).add(
            self.icon_p24V_converter2).up() \
            .hbox(spacing=5).add(AlignLabel('Сопротивление СЭП+', Qt.AlignRight), fix_w=hint3).add(
            self.label_resist_SEP_plus).up() \
            .hbox(spacing=5).add(AlignLabel('Сопротивление СЭП-', Qt.AlignRight), fix_w=hint3).add(
            self.label_resist_SEP_minus).up() \
            .up(fix_w=hint3) \
            .up()

        tab_widget = QTabWidget(self.widget())
        tab_widget.setMovable(False)
        tab_widget.setTabsClosable(False)
        lb.add(tab_widget)

        w = QWidget(tab_widget)
        lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)

        lb.vbox(spacing=5, margins=(5, 5, 5, 5), title='Наличие связи') \
            .hbox(spacing=5) \
            .add(AlignLabel('КИ№1', Qt.AlignCenter)).stretch().add(AlignLabel('КИ№2', Qt.AlignCenter)).stretch().add(
            AlignLabel('КИ№3', Qt.AlignCenter)).stretch().add(AlignLabel('КИ№4', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('КММ', Qt.AlignCenter)).stretch().add(AlignLabel('ИПД', Qt.AlignCenter)).stretch().add(
            AlignLabel('КСТ', Qt.AlignCenter)).stretch().add(AlignLabel('ИЗД', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('ИТ', Qt.AlignCenter)) \
            .up(fix_w=hint4) \
            .hbox(spacing=5) \
            .add(self.led_connected_KI1).stretch().add(self.led_connected_KI2).stretch().add(
            self.led_connected_KI3).stretch().add(self.led_connected_KI4).stretch() \
            .add(self.led_connected_KMM).stretch().add(self.led_connected_IPD).stretch().add(
            self.led_connected_KST).stretch().add(self.led_connected_IZD).stretch() \
            .add(self.led_connected_IT) \
            .up(fix_w=hint4) \
            .hbox(spacing=5) \
            .add(AlignLabel('ИДТ№1', Qt.AlignCenter)).stretch().add(AlignLabel('ИДТ№2', Qt.AlignCenter)).stretch().add(
            AlignLabel('ИДТ1№1', Qt.AlignCenter)).stretch().add(AlignLabel('ИДТ1№2', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('ИДТ1№3', Qt.AlignCenter)).stretch().add(
            AlignLabel('ИДТ1№4', Qt.AlignCenter)).stretch().add(AlignLabel('ПСТ', Qt.AlignCenter)).stretch().add(
            AlignLabel('ИИК', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('ИН', Qt.AlignCenter)) \
            .up(fix_w=hint4) \
            .hbox(spacing=5) \
            .add(self.led_connected_IDT1).stretch().add(self.led_connected_IDT2).stretch().add(
            self.led_connected_IDT11).stretch().add(self.led_connected_IDT12).stretch() \
            .add(self.led_connected_IDT13).stretch().add(self.led_connected_IDT14).stretch().add(
            self.led_connected_PST).stretch().add(self.led_connected_IIK).stretch() \
            .add(self.led_connected_IN) \
            .up(fix_w=hint4) \
            .up() \
            .vbox(spacing=5, margins=(5, 5, 5, 5), title='Режимы управления выходами') \
            .hbox(spacing=5) \
            .add(AlignLabel('ИГБФ', Qt.AlignCenter)).stretch().add(AlignLabel('ИАБ', Qt.AlignCenter)).stretch().add(
            AlignLabel('ДВ', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('ЗД', Qt.AlignCenter)).stretch().add(AlignLabel('ММ', Qt.AlignCenter)).stretch().add(
            AlignLabel('ДС', Qt.AlignCenter)) \
            .up(fix_w=hint5) \
            .hbox(spacing=5) \
            .add(self.icon_mode_IGBF).stretch().add(self.icon_mode_IAB).stretch().add(self.icon_mode_DV).stretch() \
            .add(self.icon_mode_ZD).stretch().add(self.icon_mode_MM).stretch().add(self.icon_mode_DS) \
            .up(fix_w=hint5) \
            .up() \
            .stretch()
        tab_widget.addTab(w, 'Связь/Режимы')

        w = QWidget(tab_widget)
        lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)

        lb.vbox(spacing=5, margins=(5, 5, 5, 5), title='Напряжение сигналов аналоговой ТМИ') \
            .hbox(spacing=5) \
            .add(AlignLabel('Канал 1', Qt.AlignCenter)).stretch().add(
            AlignLabel('Канал 2', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 3', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('Канал 4', Qt.AlignCenter)).stretch().add(
            AlignLabel('Канал 5', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 6', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('Канал 7', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 8', Qt.AlignCenter)) \
            .up(fix_w=hint6) \
            .hbox(spacing=5) \
            .add(self.label_volt_chan_1).stretch().add(self.label_volt_chan_2).stretch().add(
            self.label_volt_chan_3).stretch() \
            .add(self.label_volt_chan_4).stretch().add(self.label_volt_chan_5).stretch().add(
            self.label_volt_chan_6).stretch() \
            .add(self.label_volt_chan_7).stretch().add(self.label_volt_chan_8) \
            .up(fix_w=hint6) \
            .up() \
            .vbox(spacing=5, margins=(5, 5, 5, 5), title='Температура АБ') \
            .hbox(spacing=5) \
            .add(AlignLabel('Канал 1', Qt.AlignCenter)).stretch().add(
            AlignLabel('Канал 2', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 3', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('Канал 4', Qt.AlignCenter)).stretch().add(
            AlignLabel('Канал 5', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 6', Qt.AlignCenter)) \
            .up(fix_w=hint7) \
            .hbox(spacing=5) \
            .add(self.label_temp_ab_chan_1).stretch().add(self.label_temp_ab_chan_2).stretch().add(
            self.label_temp_ab_chan_3).stretch() \
            .add(self.label_temp_ab_chan_4).stretch().add(self.label_temp_ab_chan_5).stretch().add(
            self.label_temp_ab_chan_6) \
            .up(fix_w=hint7) \
            .hbox(spacing=5) \
            .add(AlignLabel('Канал 7', Qt.AlignCenter)).stretch().add(
            AlignLabel('Канал 8', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 9', Qt.AlignCenter)).stretch() \
            .add(AlignLabel('Канал 10', Qt.AlignCenter)).stretch().add(
            AlignLabel('Канал 11', Qt.AlignCenter)).stretch().add(AlignLabel('Канал 12', Qt.AlignCenter)) \
            .up(fix_w=hint7) \
            .hbox(spacing=5) \
            .add(self.label_temp_ab_chan_7).stretch().add(self.label_temp_ab_chan_8).stretch().add(
            self.label_temp_ab_chan_9).stretch() \
            .add(self.label_temp_ab_chan_10).stretch().add(self.label_temp_ab_chan_11).stretch().add(
            self.label_temp_ab_chan_12) \
            .up(fix_w=hint7) \
            .up() \
            .stretch()
        tab_widget.addTab(w, 'Напряжение/Температура')

        w = QWidget(tab_widget)
        lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=8)

        LINES_PER_TAB = 4
        ITEMS_PER_LINE = 8
        i = 0
        for name, out in self.commutations_outs.items():
            if i % (LINES_PER_TAB * ITEMS_PER_LINE) == 0:
                if i > 0:
                    lb.up().stretch()
                    tab_widget.addTab(w, 'Выходы ИГБФ')
                    w = QWidget(tab_widget)
                    lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=8)
                lb.hbox(spacing=5)
            elif i % ITEMS_PER_LINE == 0:
                if i > 0:
                    lb.up()
                lb.hbox(spacing=5)
            lb.vbox(spacing=3) \
                .hbox(spacing=3) \
                .stretch() \
                .add(AlignLabel(out['title'], Qt.AlignCenter)) \
                .stretch() \
                .up() \
                .hbox(spacing=3) \
                .stretch() \
                .add(out['widget']) \
                .stretch() \
                .up() \
                .up()
            i += 1
        if i % (LINES_PER_TAB * ITEMS_PER_LINE) != 0:
            while i % ITEMS_PER_LINE != 0:
                lb.vbox(spacing=3) \
                    .hbox(spacing=3) \
                    .stretch().add(AlignLabel("", Qt.AlignCenter)).stretch() \
                    .up() \
                    .up()
                i += 1
            lb.up().stretch()
            tab_widget.addTab(w, 'Другие выходы')

        self.hide()

    def iccellIncome(self, iccell_responce):
        self.iccellSignal.emit(iccell_responce)

    def iccellDisconnect(self):
        self.disconnectSignal.emit()

    def setLoading(self, msg, loading):
        self.loadingSignal.emit(msg, loading)

    def onLoadingSignal(self, msg, loading):
        if msg == 'ЗапрСост':
            self.sost_loading.setVisible(loading)
        elif msg == 'ЗапрСопрИзол':
            self.sopriz_loading.setVisible(loading)
        elif msg == 'ЗапрНараб':
            self.narab_loading.setVisible(loading)
        elif msg == 'ЗапрНапряжСигТЛМ':
            self.naprtlm_loading.setVisible(loading)
        elif msg == 'ЗапрНапряж':
            self.napr_loading.setVisible(loading)
        elif msg == 'ЗапрТемпАБ':
            self.tempab_loading.setVisible(loading)

    def updateUi(self, iccell_responce):
        if iccell_responce.unpacked is None:
            return
        obj = iccell_responce.unpacked



        if ICCELL.MESSAGES_TO_ICCELL['ЗапрТемпАБ']['responce_id'] == iccell_responce.packet_code:
            self.setLabelText(self.label_temp_ab_chan_1, '%.1f °С' % (obj.temp_chan_1 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_2, '%.1f °С' % (obj.temp_chan_2 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_3, '%.1f °С' % (obj.temp_chan_3 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_4, '%.1f °С' % (obj.temp_chan_4 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_5, '%.1f °С' % (obj.temp_chan_5 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_6, '%.1f °С' % (obj.temp_chan_6 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_7, '%.1f °С' % (obj.temp_chan_7 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_8, '%.1f °С' % (obj.temp_chan_8 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_9, '%.1f °С' % (obj.temp_chan_9 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_10, '%.1f °С' % (obj.temp_chan_10 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_11, '%.1f °С' % (obj.temp_chan_11 / 10.0,))
            self.setLabelText(self.label_temp_ab_chan_12, '%.1f °С' % (obj.temp_chan_12 / 10.0,))
            self.tempab_loading.setVisible(False)

        if ICCELL.MESSAGES_TO_ICCELL['ТемператураАБ']['responce_id'] == iccell_responce.packet_code:
            self.setLabelText(self.label_temp_ab_chan_1, '%.1f °С' % (obj.temp_chan_1,))
            self.setLabelText(self.label_temp_ab_chan_2, '%.1f °С' % (obj.temp_chan_2,))
            self.setLabelText(self.label_temp_ab_chan_3, '%.1f °С' % (obj.temp_chan_3,))
            self.setLabelText(self.label_temp_ab_chan_4, '%.1f °С' % (obj.temp_chan_4,))
            self.setLabelText(self.label_temp_ab_chan_5, '%.1f °С' % (obj.temp_chan_5,))
            self.setLabelText(self.label_temp_ab_chan_6, '%.1f °С' % (obj.temp_chan_6,))
            self.setLabelText(self.label_temp_ab_chan_7, '%.1f °С' % (obj.temp_chan_7,))
            self.setLabelText(self.label_temp_ab_chan_8, '%.1f °С' % (obj.temp_chan_8,))
            self.setLabelText(self.label_temp_ab_chan_9, '%.1f °С' % (obj.temp_chan_9,))
            self.setLabelText(self.label_temp_ab_chan_10, '%.1f °С' % (obj.temp_chan_10,))
            self.setLabelText(self.label_temp_ab_chan_11, '%.1f °С' % (obj.temp_chan_11,))
            self.setLabelText(self.label_temp_ab_chan_12, '%.1f °С' % (obj.temp_chan_12,))
            self.tempab_loading.setVisible(False)

        if ICCELL.MESSAGES_TO_ICCELL['ЗапрНапряжСигТЛМ']['responce_id'] == iccell_responce.packet_code:
            self.setLabelText(self.label_volt_chan_1, '%.3f В' % (obj.voltage_chan_1 / 1000.0,))
            self.setLabelText(self.label_volt_chan_2, '%.3f В' % (obj.voltage_chan_2 / 1000.0,))
            self.setLabelText(self.label_volt_chan_3, '%.3f В' % (obj.voltage_chan_3 / 1000.0,))
            self.setLabelText(self.label_volt_chan_4, '%.3f В' % (obj.voltage_chan_4 / 1000.0,))
            self.setLabelText(self.label_volt_chan_5, '%.3f В' % (obj.voltage_chan_5 / 1000.0,))
            self.setLabelText(self.label_volt_chan_6, '%.3f В' % (obj.voltage_chan_6 / 1000.0,))
            self.setLabelText(self.label_volt_chan_7, '%.3f В' % (obj.voltage_chan_7 / 1000.0,))
            self.setLabelText(self.label_volt_chan_8, '%.3f В' % (obj.voltage_chan_8 / 1000.0,))
            self.naprtlm_loading.setVisible(False)

        if ICCELL.MESSAGES_TO_ICCELL['ЗапрСопрИзол']['responce_id'] == iccell_responce.packet_code:
            self.setLabelText(self.label_resist_SEP_plus, '%d кОм' % obj.resist_SEP_plus)
            self.setLabelText(self.label_resist_SEP_minus, '%d кОм' % obj.resist_SEP_minus)
            self.sopriz_loading.setVisible(False)

        if ICCELL.MESSAGES_TO_ICCELL['ЗапрНапряж']['responce_id'] == iccell_responce.packet_code:
            self.setLabelText(self.label_ka_voltage, '%.3f В' % (obj.voltage / 1000.0,))
            self.napr_loading.setVisible(False)

        elif ICCELL.MESSAGES_TO_ICCELL['ЗапрНараб']['responce_id'] == iccell_responce.packet_code:
            self.setLabelText(self.label_run_time_ka, '%.1f сек' % (obj.run_time_KA / 4.0,))
            self.setLabelText(self.label_run_time_ivk, '%.1f сек' % (obj.run_time_IVK / 4.0,))
            self.narab_loading.setVisible(False)

        elif ICCELL.MESSAGES_TO_ICCELL['ЗапрСост']['responce_id'] == iccell_responce.packet_code:
            self.icon_ka_powered.setState(obj.ka_powered == 1)
            self.icon_emergency_button.setState(obj.emergency_button == 1)
            self.icon_p24V_converter1.setState(obj.p24V_converter1 == 1)
            self.icon_p24V_converter2.setState(obj.p24V_converter2 == 1)
            self.icon_ivk_counter_ok.setState(obj.ivk_counter_ok == 0)
            self.icon_ka_counter_ok.setState(obj.ka_counter_ok == 0)

            self.led_connected_KI1.setState(obj.KI1_connected == 1)
            self.led_connected_KI2.setState(obj.KI2_connected == 1)
            self.led_connected_KI3.setState(obj.KI3_connected == 1)
            self.led_connected_KI4.setState(obj.KI4_connected == 1)
            self.led_connected_KMM.setState(obj.KMM_connected == 1)
            self.led_connected_IPD.setState(obj.IPD_connected == 1)
            self.led_connected_KST.setState(obj.KST_connected == 1)
            self.led_connected_IZD.setState(obj.IZD_connected == 1)
            self.led_connected_IT.setState(obj.IT_connected == 1)
            self.led_connected_IDT1.setState(obj.IDT1_connected == 1)
            self.led_connected_IDT2.setState(obj.IDT2_connected == 1)
            self.led_connected_IDT11.setState(obj.IDT11_connected == 1)
            self.led_connected_IDT12.setState(obj.IDT12_connected == 1)
            self.led_connected_IDT13.setState(obj.IDT13_connected == 1)
            self.led_connected_IDT14.setState(obj.IDT14_connected == 1)
            self.led_connected_PST.setState(obj.PST_connected == 1)
            self.led_connected_IIK.setState(obj.IIK_connected == 1)
            self.led_connected_IN.setState(obj.IN_connected == 1)

            self.icon_mode_IGBF.setState(obj.IGBF_pwr == 0)
            self.icon_mode_IAB.setState(obj.IAB_pwr == 0)
            self.icon_mode_DV.setState(obj.DV_pwr == 0)
            self.icon_mode_ZD.setState(obj.ZD_pwr == 0)
            self.icon_mode_MM.setState(obj.MM_pwr == 0)
            self.icon_mode_DS.setState(obj.DS_pwr == 0)

            for name, out in self.commutations_outs.items():
                if name.strip():
                    out['widget'].setState(getattr(obj, name) == 1)

            self.sost_loading.setVisible(False)

    def setLabelText(self, label, text):
        if text != label.text():
            label.setText(text)

            self.colored_labels_lock.acquire()
            self.colored_labels[label] = {'dt': datetime.now(), 'colored': True}
            self.colored_labels_lock.release()

            label.setAutoFillBackground(True)
            pal = label.palette()
            pal.setColor(QPalette.Window, QColor('#5effb1'))
            label.setPalette(pal)
            # label.setStyleSheet("background-color: rgb(255, 0, 0);")

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
                    # label.setStyleSheet("background-color: rgb(0, 0, 255);")
            self.colored_labels_lock.release()

    def checkStateChanged(self, msg, state):
        if state != Qt.Unchecked:
            return
        if msg == 'ЗапрСост':
            self.icon_ka_powered.setState(None)
            self.icon_emergency_button.setState(None)
            self.icon_p24V_converter1.setState(None)
            self.icon_p24V_converter2.setState(None)
            self.icon_ivk_counter_ok.setState(None)
            self.icon_ka_counter_ok.setState(None)

            self.led_connected_KI1.setState(None)
            self.led_connected_KI2.setState(None)
            self.led_connected_KI3.setState(None)
            self.led_connected_KI4.setState(None)
            self.led_connected_KMM.setState(None)
            self.led_connected_IPD.setState(None)
            self.led_connected_KST.setState(None)
            self.led_connected_IZD.setState(None)
            self.led_connected_IT.setState(None)
            self.led_connected_IDT1.setState(None)
            self.led_connected_IDT2.setState(None)
            self.led_connected_IDT11.setState(None)
            self.led_connected_IDT12.setState(None)
            self.led_connected_IDT13.setState(None)
            self.led_connected_IDT14.setState(None)
            self.led_connected_PST.setState(None)
            self.led_connected_IIK.setState(None)
            self.led_connected_IN.setState(None)

            self.icon_mode_IGBF.setState(None)
            self.icon_mode_IAB.setState(None)
            self.icon_mode_DV.setState(None)
            self.icon_mode_ZD.setState(None)
            self.icon_mode_MM.setState(None)
            self.icon_mode_DS.setState(None)

            for name, out in self.commutations_outs.items():
                if name.strip():
                    out['widget'].setState(None)

            self.sost_loading.setVisible(False)

        elif msg == 'ЗапрСопрИзол':
            self.label_resist_SEP_plus.setText('?')
            self.label_resist_SEP_minus.setText('?')
            self.sopriz_loading.setVisible(False)

        elif msg == 'ЗапрНараб':
            self.label_run_time_ka.setText('?')
            self.label_run_time_ivk.setText('?')
            self.narab_loading.setVisible(False)

        elif msg == 'ЗапрНапряжСигТЛМ':
            self.label_volt_chan_1.setText('?')
            self.label_volt_chan_2.setText('?')
            self.label_volt_chan_3.setText('?')
            self.label_volt_chan_4.setText('?')
            self.label_volt_chan_5.setText('?')
            self.label_volt_chan_6.setText('?')
            self.label_volt_chan_7.setText('?')
            self.label_volt_chan_8.setText('?')
            self.naprtlm_loading.setVisible(False)

        elif msg == 'ЗапрНапряж':
            self.label_ka_voltage.setText('?')
            self.napr_loading.setVisible(False)

        elif msg == 'ЗапрТемпАБ':
            self.label_temp_ab_chan_1.setText('?')
            self.label_temp_ab_chan_2.setText('?')
            self.label_temp_ab_chan_3.setText('?')
            self.label_temp_ab_chan_4.setText('?')
            self.label_temp_ab_chan_5.setText('?')
            self.label_temp_ab_chan_6.setText('?')
            self.label_temp_ab_chan_7.setText('?')
            self.label_temp_ab_chan_8.setText('?')
            self.label_temp_ab_chan_9.setText('?')
            self.label_temp_ab_chan_10.setText('?')
            self.label_temp_ab_chan_11.setText('?')
            self.label_temp_ab_chan_12.setText('?')
            self.tempab_loading.setVisible(False)

    def showEvent(self, event):
        super().showEvent(event)

    def closeEvent(self, event):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)
        super().closeEvent(event)

    def saveSettings(self):
        return {
            'sost_check_state': self.sost_checkbox.checkState(),
            'sopriz_check_state': self.sopriz_checkbox.checkState(),
            'narab_check_state': self.narab_checkbox.checkState(),
            'naprtlm_check_state': self.naprtlm_checkbox.checkState(),
            'napr_check_state': self.napr_checkbox.checkState(),
            'tempab_check_state': self.tempab_checkbox.checkState()
        }

    def restoreSettings(self, settings):
        pass
        self.sost_checkbox.setCheckState(settings['sost_check_state'])
        self.sopriz_checkbox.setCheckState(settings['sopriz_check_state'])
        self.narab_checkbox.setCheckState(settings['narab_check_state'])
        self.naprtlm_checkbox.setCheckState(settings['naprtlm_check_state'])
        self.napr_checkbox.setCheckState(settings['napr_check_state'])
        self.tempab_checkbox.setCheckState(settings['tempab_check_state'])

    def settingsKeyword(self):
        return 'MKAICCELLWidget'

    def getMenuParams(self):
        return {
            'icon': 'res/server_icon.png',
            'text': 'Окно ячейки ПИ МКА',
            'status_tip': 'Окно мониторинга ячейки ПИ шкафа ИВК МКА'
        }
