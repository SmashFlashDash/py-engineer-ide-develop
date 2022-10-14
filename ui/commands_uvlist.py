import pathlib

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, \
    QLineEdit, QLabel, QComboBox, QCompleter, QSizePolicy, QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
import sys
import json
from json import JSONDecoder
import re
from ui.components.commons import Commons


# TODO: make get_data - parsing method with try catch that don't fall app
# TODO: в окне поиска УВ чтобы select item сигналил по MouseHover
# TODO: добавить лейбл буттон рядом с LineEdit переключайющий поиск по номеру УВ на поиск по слову в description uv
# TODO: выдать комманду не из списка можно только с вкладки all
# TODO: добавить SOTC в виджет чтобы автомато перключалась выдача на SOTC с вкладки

class ClickableLineEdit(QLineEdit):
    '''QLineEdit with mouse clicks'''
    clicked = pyqtSignal()
    db_clicked = pyqtSignal()
    enter_key = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.timeout_single_click)
        self.click_count = 0

    def timeout_single_click(self):
        # clicks behavior
        self.timer.stop()
        if self.click_count == 1:
            self.clicked.emit()
        elif self.click_count > 1:
            self.db_clicked.emit()
        self.click_count = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_count += 1
            if not self.timer.isActive():
                self.timer.start()

    def mouseDoubleClickEvent(self, event) -> None:
        self.click_count += 2
        if not self.timer.isActive():
            self.timer.start()

    def keyPressEvent(self, event) -> None:
        if Qt.Key_Enter in [event.key(), event.key() + 1]:
            self.enter_key.emit()
        return super().keyPressEvent(event)


class UV:
    '''класс параметров УВ из list_UV'''

    def __init__(self, uv_hex, params, device):
        # names of parametr uv in json
        self.uv_hex = None
        self.uv_int = None
        self.uv_num_device = None
        self.description = None
        self.obts = None
        self.args = None
        self.device = None
        arguments = self.__dict__

        # Validate parametrs name
        if not (re.compile(r'^0x[\dA-Fa-f]+$').search(uv_hex)):
            raise ValueError('Недопустимый формат hex: %s' % uv_hex)
        wrong_fields = [x[0] for x in params if x[0] not in arguments.keys()]
        if len(wrong_fields) != 0:
            raise ValueError('УВ \'%s\' имеет недопустимое поле: %s' % (uv_hex, wrong_fields))

        # To object
        self.uv_hex = uv_hex
        self.uv_int = int(self.uv_hex, 16)
        self.device = device
        for item in params:
            arguments[item[0]] = item[1]
        if self.description in [None, '']:
            self.description = 'Нет описания УВ'

    def get_uv_hex(self):
        return self.uv_hex

    def get_device(self):
        return self.device

    def get_description(self):
        return self.description

    def __hash__(self):
        return hash(self.device)

    def __eq__(self, other):
        return self.uv_int == other.uv_int

    def __str__(self):
        return 'УВ: %s\n' % self.uv_hex + '\n'.join(['%s: %s' % (x, self.__dict__[x]) for x in self.__dict__])


class Data_list_uv:
    uv_dict = None
    device_dict = None
    uv_list = None
    device_list = None
    status = None

    def parse_object_pairs(self, pairs):
        return pairs

    def __init__(self):
        path = ['engineers_src', 'list_uv.json']
        with open('/'.join(path), 'r', encoding='utf-8') as f:
            file = json.load(f, object_pairs_hook=self.parse_object_pairs)
        self.uv_dict, self.uv_list, self.device_dict, self.device_list, = self.parse(file)

    def parse(self, file):
        '''Парсинг json в lists без совпадений'''
        '''Провека полей УВ в классе UV'''
        device_dict = {}
        uv_dict = {}

        for keys in file:
            device = keys[0]
            arguments = keys[1]
            # not add repeat devices
            if device_dict.get(device) is not None:
                raise ValueError('Поптыка повторно добавить устройство: device-%s' % device)
            else:
                device_dict[device] = {'description': '', 'list_uv': []}
                for key_argsuments in arguments:
                    key = key_argsuments[0]
                    params = key_argsuments[1]
                    if key == 'description' and isinstance(params, str):
                        device_dict[device][key] = params
                    elif isinstance(params, list) and key.strip().startswith('0x'):
                        uv_hex = key.strip()
                        uv = UV(uv_hex, params, device)  # перевод в обьект
                        # not add repeat UV
                        if uv_dict.get(uv_hex) is not None:
                            raise ValueError('Поптыка повторно добавить УВ: %s' % uv)
                        uv_dict[uv_hex] = uv
                        device_dict[device]['list_uv'].append(uv_hex)
                    else:
                        raise ValueError('Недопустимое поле: device-%s, key-%s' % (device, key))
                # description not ''
                if device_dict[device]['description'] == '':
                    device_dict[device]['description'] = 'Нет описания устройства'
        device_list = sorted(device_dict.keys())
        uv_list = sorted(uv_dict.keys())
        device_list.insert(0, 'all')
        device_dict['all'] = {'description': 'Все УВ', 'list_uv': uv_list}
        return uv_dict, uv_list, device_dict, device_list


class UV_search_widget(QWidget):
    '''Можно сделать через qLayoutBuilder'''
    data = None
    args_widget = None
    info_widget = None
    device_box = None
    line_cmd = None
    line_obts = None
    line_args = None
    current_device = None
    status_parsed = None

    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent=parent)
        self.args_widget = parent
        self.setObjectName('autoCompeteInfoFrame')

        # layout
        layoutV = QVBoxLayout()
        layoutV.setContentsMargins(0, 0, 0, 0)
        layoutV.setSpacing(5)
        layoutV.addLayout(self._init_1st_layoyt())
        layoutV.addLayout(self._init_2d_layoyt())
        layoutV.addLayout(self._init_3d_layoyt())
        self.setLayout(layoutV)

        # set arguments completter and clicks
        self.completer = QCompleter([])
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)
        self.line_cmd.setCompleter(self.completer)
        self.line_cmd.clicked.connect(self.clicked_cmd)
        self.line_cmd.db_clicked.connect(self.db_clicked_cmd)
        self.line_cmd.enter_key.connect(self.bring_obts_args)
        self.line_cmd.textChanged.connect(self.cmd_text_changed)

        # functional
        self.device_box.currentIndexChanged.connect(self.device_box_changed)
        self.completer.highlighted.connect(self.show_description_uv)
        self.completer.activated.connect(self.bring_obts_args)

        self.hide()

    def clicked_cmd(self):
        self.cmd_set_min_text()
        self.completer.setCompletionPrefix(self.line_cmd.text())
        self.completer.complete()

    def db_clicked_cmd(self):
        self.line_cmd.setText('0x')
        self.completer.setCompletionPrefix('0x')
        self.completer.complete()

    def cmd_set_min_text(self):
        text = self.line_cmd.text()
        if len(text) <= 2 and text != '0x':
            self.line_cmd.setText('0x')

    def cmd_text_changed(self, new_text):
        self.cmd_set_min_text()
        self.clear_uv_lines()

    def clear_uv_lines(self):
        self.line_obts.clear()
        self.line_args.clear()

    def device_box_changed(self):
        self.current_device = self.device_box.currentText()
        self._set_info_widget_text(self.data.device_dict[self.current_device]['description'])
        self.completer.model().setStringList(self.data.device_dict[self.current_device]['list_uv'])
        self.line_cmd.setText('0x')
        self.clear_uv_lines()

    def show_description_uv(self, uv_hex):
        uv = self.data.uv_dict.get(uv_hex)
        if uv is not None:
            self._set_info_widget_text(uv.description)
        else:
            self._set_info_widget_text(self.data.device_dict[self.current_device]['description'])

    def bring_obts_args(self):
        def take_arg(line: QLineEdit, param, mask):
            if param in [None, False, '']:
                pass
            elif param is True:
                line.setText(mask)
            elif isinstance(param, str):
                line.setText(param)
            else:
                raise ValueError('Неизвестный тип аргумента: %s' % param)

        uv = self.data.uv_dict.get(self.line_cmd.text().strip())
        if uv is not None:
            take_arg(self.line_obts, uv.obts, 'OBTS('')')
            take_arg(self.line_args, uv.args, 'AsciiHex(\'0x 0000 0000\')')
            self._set_info_widget_text(uv.description)
        else:
            self._set_info_widget_text('Ошибка выбора УВ')
            self.cmd_set_min_text()

    def parse_list_uv(self):
        self.status_parsed = None
        if self.data is not None:
            return
        try:
            self.data = Data_list_uv()
        except FileNotFoundError as e:
            self.status_parsed = e
            return
        except (ValueError, Exception) as e:
            self.status_parsed = e
            return
        self.device_box.addItems(self.data.device_list)  # set box items
        self.device_box.setCurrentIndex(1)  # set index on first element
        self.device_box.setCurrentIndex(0)  # set index on first element

    def set_info_widget(self, widget):
        self.info_widget = widget

    def connect_to_args_widget(self):
        self.args_widget.arg_editors.append(self.line_cmd)
        self.args_widget.arg_editors.append(self.line_obts)
        self.args_widget.arg_editors.append(self.line_args)
        self.args_widget.skip_arg_checkboxes.extend([None, None, None])

    def _init_1st_layoyt(self):
        '''1st row'''
        layoutH = QHBoxLayout()

        label = QLabel('Блок')
        label.setObjectName('consolasBoldFont')
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        layoutH.addWidget(label)

        self.device_box = QComboBox(self)
        self.device_box.setObjectName('consolasFont')
        self.device_box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        layoutH.addWidget(self.device_box)

        label = QLabel('cmd')
        label.setObjectName('consolasBoldFont')
        layoutH.addWidget(label)

        self.line_cmd = ClickableLineEdit()
        self.cmd_set_min_text()
        self.line_cmd.setObjectName('consolasFont')
        layoutH.addWidget(self.line_cmd)
        return layoutH

    def _init_2d_layoyt(self):
        '''2d row'''
        layoutH = QHBoxLayout()
        label = QLabel('obts')
        label.setObjectName('consolasBoldFont')
        layoutH.addWidget(label)
        self.line_obts = QLineEdit()
        self.line_obts.setObjectName('consolasFont')
        layoutH.addWidget(self.line_obts)
        return layoutH

    def _init_3d_layoyt(self):
        '''2d row'''
        layoutH = QHBoxLayout()
        label = QLabel('args')
        label.setObjectName('consolasBoldFont')
        self.line_args = QLineEdit()
        self.line_args.setObjectName('consolasFont')
        layoutH.addWidget(label)
        layoutH.addWidget(self.line_args)
        return layoutH

    def _set_info_widget_text(self, text):
        self.info_widget.setText(text)
        self.info_widget.setFixedHeight(100)

    # def _set_info_widget_text_clear(self):
    #     self.info_widget.clear()
    #     self.info_widget.setFixedHeight(30)


if __name__ == '__main__':
    import sys, os, getpass
    from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton
    from PyQt5.QtCore import Qt, QCoreApplication
    from PyQt5.QtGui import QIcon
    import pathlib


    class MainWindow(QMainWindow):
        def __init__(self):
            super(MainWindow, self).__init__()
            self.button = None
            self.textWdiget = None
            self.searchWidget = None
            QCoreApplication.setApplicationName('Search-Bar')
            QCoreApplication.setOrganizationName('VNIIEM')
            QCoreApplication.setOrganizationDomain('mcc.vniiem.ru')

            self.initUI()
            self.initParseBtn()
            self.initTextTab()
            self.initSearchWidg()
            self.button.clicked.connect(self.searchWidget.parse_list_uv)
            self.centralWidget().setLayout(self.layout())

        def initUI(self):
            self.setWindowTitle("IVK-NG Next [%s]" % getpass.getuser())
            self.setDockOptions(QMainWindow.AnimatedDocks)
            self.statusBar().show()
            self.setCentralWidget(QWidget(self))

            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)
            self.centralWidget().setLayout(layout)

        def initParseBtn(self):
            self.button = QPushButton()
            self.centralWidget().layout().addWidget(self.button)

            self.button.setText('Спарсить')
            self.button.setStyleSheet("color: blue;"
                                 "background-color: rgb(%1,%2,%3);"
                                 "selection-color: yellow;"
                                 "selection-background-color: blue;")
            # ("background-color: rgb(1%,2%,3%);"
            #  "border-style: outset;"
            #  "border-width: 2px;"
            #  "border-radius: 10px;"
            #  "font: bold 14px;"
            #  "min-width: 10em;"
            #  "padding: 6px;")

        def initTextTab(self):
            self.textWdiget = QTextEdit()
            self.textWdiget.setObjectName('autoCompeteInfoFrame')
            self.textWdiget.setReadOnly(True)
            self.textWdiget.setLineWrapMode(QTextEdit.WidgetWidth)
            self.textWdiget.setText('Описание')
            self.centralWidget().layout().addWidget(self.textWdiget)

        def initSearchWidg(self):
            self.searchWidget = UV_search_widget()
            self.searchWidget.show()
            self.searchWidget.set_info_widget(self.textWdiget)
            self.centralWidget().layout().addWidget(self.searchWidget)


    os.chdir(pathlib.Path.cwd().parent)
    app = QApplication(sys.argv)
    app.setStyleSheet(open('styles.css', mode='r', encoding='utf-8').read())
    app.setWindowIcon(QIcon("res/mainicon.png"))

    window = MainWindow()
    window.setGeometry(1400, 800, 800, 400)
    window.show()
    sys.exit(app.exec_())
