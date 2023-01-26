from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, \
    QLineEdit, QLabel, QComboBox, QCompleter, QSizePolicy, QTextEdit, QAbstractItemView, QPushButton, QLayout
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QSize, QEvent
from PyQt5.QtGui import QFontMetrics, QFont, QIcon, QPixmap, QPainter, QColor, QStandardItemModel, QStandardItem
import json
import re
from _collections import OrderedDict


class ClickableLineEdit(QLineEdit):
    """QLineEdit with mouse clicks"""
    clicked = pyqtSignal()
    db_clicked = pyqtSignal()
    enter_key = pyqtSignal()
    min_text = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.installEventFilter(self)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.timeout_single_click)
        self.click_count = 0
        self.textChanged.connect(self.cust_textEdited, Qt.QueuedConnection)

    def set_min_text(self, text):
        self.min_text = text
        self.setText(text)

    def cust_textEdited(self, newText):
        if len(newText) < len(self.min_text):
            self.setText(self.min_text)

    def timeout_single_click(self):
        # clicks behavior
        self.timer.stop()
        if self.click_count == 1:
            self.clicked.emit()
        elif self.click_count > 1:
            self.db_clicked.emit()
        self.click_count = 0

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_count += 1
            if not self.timer.isActive():
                self.timer.start()

    def mouseDoubleClickEvent(self, event) -> None:
        self.click_count += 2
        if not self.timer.isActive():
            self.timer.start()

    def keyPressEvent(self, event) -> None:
        super().keyPressEvent(event)
        if Qt.Key_Enter in [event.key(), event.key() + 1]:
            self.enter_key.emit()


class AbstractCMD:
    id = None
    id_hex = None
    obts = None
    args = None
    description = None
    device = None
    cmd_type = None

    @staticmethod
    def parse_arg(param, key):
        def depth(data):
            if isinstance(data, (list, tuple)) and len(data) > 0:
                return 1 + depth(data[0])
            return 0

        def format_item(key, arg):
            mask = None
            if key == 'obts':
                mask = 'OBTS(\'2000:1:1:0:0:0\')'
            elif key == 'args':
                mask = 'AsciiHex(\'0x 0000 0000\')'
            if arg in ('', False, None):
                return None
            elif isinstance(arg, bool):
                return {mask: 'По умолчанию'}
            elif isinstance(arg, str):
                return {arg: 'Нет описания'}

        def parse_item_todict(x):
            item = [None, None]
            for xx in x:
                if xx[0] == 'arg':
                    item[0] = xx[1]
                elif xx[0] == 'description':
                    item[1] = xx[1]
            if item[1] in (False, True, '', None):
                item[1] = 'Нет описания'
            return item

        depth_param = depth(param)
        if depth_param == 0:
            return format_item(key, param)
        elif depth_param == 2:
            item = parse_item_todict(param)
            return {item[0]: item[1]}
        elif depth_param == 3:
            format_params = OrderedDict()
            for x in param:
                item = parse_item_todict(x)
                if format_params.get(item[0]) is not None:
                    raise ValueError('Нельзя добавлять два одинаковых аргумента: %s' % item[0])
                format_params[item[0]] = item[1]
            return format_params
        else:
            raise ValueError('Ошибка при парсинге параметров %s' % param)

    def __hash__(self):
        return hash(self.device)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return '%s: %s\n' % (self.cmd_type, self.id) + \
               '\n'.join(['%s: %s' % (x, self.__dict__[x]) for x in self.__dict__])


class PojoUV(AbstractCMD):
    def __init__(self, cmd_id, params, device, cmd_type):
        arguments = ('obts', 'args', 'description', 'uv_num_device')
        if not (re.compile(r'^0x[\dA-Fa-f]+$').search(cmd_id)) or not 0 < int(cmd_id, 16) <= 65535:
            raise ValueError('Недопустимый параметр: %s : %s' % (cmd_type, cmd_id))
        wrong_fields = [x for x in params if x not in arguments]
        if len(wrong_fields) != 0:
            raise ValueError('%s \'%s\' имеет недопустимое поле: %s' % (cmd_type, cmd_id, wrong_fields))

        self.cmd_type = cmd_type
        self.id_hex = cmd_id
        self.id = int(cmd_id, 16)
        self.device = device
        for key in ('obts', 'args'):
            if params.get(key) is None:
                params[key] = True
        for key, val in params.items():
            if key not in ('uv_num_device', 'description'):
                val = self.parse_arg(val, key)
            setattr(self, key, val)
        if self.description in [None, '']:
            self.description = 'Нет описания ' + self.cmd_type


class PojoSOTC(AbstractCMD):
    def __init__(self, cmd_id, params, device, cmd_type):
        arguments = ('args', 'description')
        if not 1 <= int(cmd_id) < 168:
            raise ValueError('Недопустимый параметр: %s : %s' % (cmd_type, cmd_id))
        wrong_fields = [x for x in params if x not in arguments]
        if len(wrong_fields) != 0:
            raise ValueError('%s: %s имеет недопустимое поле: %s' % (cmd_type, cmd_id, wrong_fields))

        self.cmd_type = cmd_type
        self.id = cmd_id
        self.device = device
        if params.get('args') is None:
            params['args'] = True
        for key, val in params.items():
            if key not in 'description':
                val = self.parse_arg(val, key)
            setattr(self, key, val)
        if self.description in [None, '']:
            self.description = 'Нет описания ' + self.cmd_type


class DataListUV:
    """Класc с даннымы распарссенного list_uv.json"""
    uv_dict = None
    sotc_dict = None
    status = None

    def __init__(self, path):
        with open('/'.join(path), 'r', encoding='utf-8') as f:
            file = json.load(f, object_pairs_hook=lambda x: x)
        self._parse(file)

    # TODO: парсить все в qModel а не словари
    def _parse(self, file):
        for x in file:
            if x[0] == "SCPICMD":
                self._parseSPICMD(x[1])
            elif x[0] == "SOTC":
                self._parseSOTC(x[1])
            else:
                raise ValueError('Неверный конфиг в .json')

    def _parseSPICMD(self, arg):
        device_dict = {}
        for item in arg:
            device = item[0]
            uvs = item[1]
            if device in device_dict:
                raise ValueError('Поптыка повторно добавить устройство: device-%s' % device)
            device_dict[device] = {'description': '', 'list_uv': {}}
            for uv in uvs:
                key = uv[0]
                params = uv[1]
                if key == 'description' and isinstance(params, str):
                    if device_dict[device]['description'] != '':
                        raise Exception('Блок %s имеет несколько \'description\'' % device)
                    device_dict[device]['description'] = params
                else:
                    params = {}
                    for i in uv[1]:
                        params[i[0]] = i[1]
                    uv_hex = key.strip()
                    uv_obj = PojoUV(uv_hex, params, device, 'УВ')  # перевод в обьект
                    if uv_hex in device_dict[device]['list_uv']:
                        raise ValueError('Поптыка повторно добавить УВ: %s' % key)
                    device_dict[device]['list_uv'][uv_hex] = uv_obj
            if device_dict[device]['description'] == '':
                device_dict[device]['description'] = 'Нет описания блока'
        # TODO: говнокод
        all_uvs_links = {}
        for i in list(map(lambda x: x['list_uv'], device_dict.values())):
            all_uvs_links.update(i)
        device_dict['all'] = {'description': 'Все УВ', 'list_uv': all_uvs_links}
        # TODO: соритрвока
        for device, item in device_dict.items():
            device_dict[device]['list_uv'] = OrderedDict(sorted(item['list_uv'].items()))  # соритрвока дикта с УВ
        device_dict = OrderedDict(sorted(device_dict.items(), key=lambda x: str.swapcase(x[0])))  # сортировка словаря
        self.uv_dict = device_dict

    def _parseSOTC(self, arg):
        sotc_dict = {}
        for item in arg:
            key = item[0]
            params = {}
            for i in item[1]:
                params[i[0]] = i[1]
            sotc_id = key.strip()
            sotc_obj = PojoSOTC(sotc_id, params, None, 'SOTC')  # перевод в обьект
            if sotc_id in sotc_dict:
                raise ValueError('Поптыка повторно добавить SOTC: %s' % key)
            sotc_dict[sotc_id] = sotc_obj
        self.sotc_dict = OrderedDict(sorted(sotc_dict.items(), key=lambda x: int(x[0])))

# TODO: вынести parse_list_uv() в внешний метод
#  парсить при создании виджета в QModels, сделать статик метод
#  сюда отправить sel, убрать здесь установку бокса, делать в UI для SOTC и SCPICMD

# TODO: select на mouseHover QListview
#  listView = self.completer.popup()
#  listView.setMouseTracking(True)
#  listView.indexAt()  # и eventFilter на listViewm

# TODO засейвиьть метода cmd_line.text
#  и заменить его чтобы првоерял при взятии что УВ в диапазоне model комплеттра
#  а то можно ввести другой hex без select item и выполнить
#  а в выполнить запрашивается метод text
# TODO: в МИК не работает подсветка при disable виджета

# TODO если сделать в Qmodel то исп прегружныый метод на item
#  index = self.completer.currentIndex()
#  index.sibling(index.row(), 0).data()


class SelectUVwidget(QWidget):
    """Можно сделать через qLayoutBuilder"""
    path_file = ['engineers_src', 'list_uv.json']
    info_widget = None
    device_box = None
    cmd_line = None
    line_obts = None
    line_args = None
    line_obts_label = None
    line_args_label = None
    current_data_item = None
    description_hex = [None, None, None]

    data = None
    data_descrip_keys = None
    cur_data = None
    current_device = None
    parse_err = None

    default_line_obts = 'OBTS(\'2000:1:1:0:0:0\')'
    default_line_args = 'AsciiHex(\'0x 0000 0000\')'

    SCPICMD = 0
    SOTC = 1
    NUMBER = 0
    DESCRIBE = 1

    cur_type = SCPICMD
    cur_type_search = NUMBER

    def eventFilter(self, obj, event) -> bool:
        # TODO: чтобы не зажимать лкм на комплеттере для select а при навоедени на Item Model
        print("%s: %s" % (obj.objectName, event.type()))
        return obj.eventFilter(obj, event)

    # TODO: нужно сделать поля с аргументами с комлеттерами и кликами
    #  первое поле управляется типом поиска по кнопке
    #  второе и третье поле показывает список аргументов и дополняет дескрипшн
    #  s
    #  или первое поле управляет поискои по сумме дескрипшионов девайса и всех аргументов
    #  s
    #  если делать модель перестануть работать скрипты делать второй реализацией

    def __init__(self, infowidg=None, parent=None):
        super(QWidget, self).__init__(parent=parent)
        self.setObjectName('autoCompeteInfoFrame')
        self._initUI()
        self.info_widget = infowidg

        # completters
        completer = QCompleter([])
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        # completer.setCompletionMode(QCompleter.PopupCompletion)
        # completer.model().stringList()   # StringListModel
        completer.setMaxVisibleItems(10)
        #completer.popup().setMaximumWidth(200)
        self.cmd_line.setCompleter(completer)
        completer = QCompleter([])
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.line_obts.setCompleter(completer)
        completer = QCompleter([])
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.line_args.setCompleter(completer)

        # clicks
        self.cmd_line.clicked.connect(self.__clicked_cmd)
        self.cmd_line.db_clicked.connect(self.__db_clicked_cmd)
        self.line_obts.db_clicked.connect(lambda: self.__db_clicked_param(self.line_obts))
        self.line_args.db_clicked.connect(lambda: self.__db_clicked_param(self.line_args))

        # functional
        self.cmd_line.textEdited.connect(self.__cmd_edit)
        self.btn_search.toggled.connect(self.btnSearchToogled)
        self.device_box.currentIndexChanged.connect(self.__device_box_changed)
        self.cmd_line.completer().highlighted.connect(self.__cmd_comp_select)
        self.cmd_line.completer().activated.connect(self.__cmd_comp_activate, Qt.QueuedConnection)
        self.line_obts.completer().highlighted.connect(self.lineOBTS_comp_select)
        self.line_args.completer().highlighted.connect(self.lineArgs_comp_select)

        # override
        self.cmd_line.getText = self.cmd_line.text  # можно декоратором
        self.cmd_line.text = self.__cmd_custom_text

        self.parse_list_uv()
        self.hide()

    def _initUI(self):
        layoutG = QVBoxLayout()
        layoutG.setContentsMargins(0, 0, 0, 0)
        layoutG.setSpacing(5)
        layoutG.setSizeConstraint(layoutG.SetMinimumSize)
        self.setLayout(layoutG)
        # для определения максимальной ширины лейбла
        fm = QFontMetrics(QFont("DejaVu Sans Mono", 10, QFont.Bold))
        label_width = 0
        for text in ['Блок', 'args', 'obts', 'cmd']:
            ln = fm.width(text)
            label_width = ln if ln > label_width else label_width

        # Первая строка
        layout = QHBoxLayout()
        self.device_label = QLabel('Блок')
        self.device_label.setObjectName('consolasBoldFont')
        self.device_label.setFixedWidth(label_width)
        self.device_box = QComboBox(self)
        self.device_box.setObjectName('consolasFont')
        layout.addWidget(self.device_label)
        layout.addWidget(self.device_box)
        self.cmd_label = QLabel('cmd')
        self.cmd_label.setObjectName('consolasBoldFont')
        self.cmd_label.setFixedWidth(label_width)
        layout.addWidget(self.cmd_label)
        self.cmd_line = ClickableLineEdit()
        self.cmd_line.setObjectName('consolasFont')
        layout.addWidget(self.cmd_line)

        # кнопка Search
        pixmap = QPixmap('res/search.png')
        painter = QPainter()
        painter.begin(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor('#0055FF'))
        painter.end()
        pixmap2 = QPixmap('res/search.png')
        icon = QIcon()
        icon.addPixmap(pixmap2, mode=QIcon.Normal, state=QIcon.Off)
        icon.addPixmap(pixmap, mode=QIcon.Normal, state=QIcon.On)
        self.btn_search = QPushButton(icon, "", self)
        self.btn_search.setIconSize(QSize(20, 20))
        self.btn_search.setFixedWidth(30)
        self.btn_search.setFlat(True)
        self.btn_search.setCheckable(True)
        self.btn_search.setFixedHeight(25)
        self.btn_search.setStyleSheet("""
                            QPushButton {background-color: rgba(0,0,0,0);}
                            QPushButton:hover {color: transparent;}""")
        layout.addWidget(self.btn_search)
        layoutG.addLayout(layout)

        # строки аргументов
        lines = [None, None]
        labels = [None, None]
        for idx, name in enumerate(['obts', 'args']):
            layout = QHBoxLayout()
            label = QLabel(name)
            label.setObjectName('consolasBoldFont')
            label.setFixedWidth(label_width)
            labels[idx] = label
            line = ClickableLineEdit()
            line.setObjectName('consolasFont')
            completter = QCompleter([])
            completter.setCaseSensitivity(Qt.CaseInsensitive)
            line.setCompleter(completter)
            lines[idx] = line
            layout.addWidget(label)
            layout.addWidget(lines[idx])
            layoutG.addLayout(layout)
        self.line_obts = lines[0]
        self.line_args = lines[1]
        self.line_obts_label = labels[0]
        self.line_args_label = labels[1]

    def clear_param_lines(self):
        self.info_widget.setText('')
        self.cmd_line.clear()
        self.line_obts.clear()
        self.line_args.clear()

    def __device_box_changed(self):
        self.clear_param_lines()
        self.current_device = self.device_box.currentText()
        self.set_info_widget_text(self.data.uv_dict[self.current_device]['description'])
        self.change_completer_model(self.data.uv_dict[self.current_device]['list_uv'])
        self.btnSearchIsChecked()

    def __cmd_custom_text(self):
        """
        Кастомный text cmdline для запрета выдачи команд с не из выбранной модели данных
        проверяет что выдаваемая команда есть в выбранной модели данных,
        а если девайс бокс активаен и all то не проверяет
        """
        text = self.cmd_line.getText()
        if self.device_box.isEnabled():
            if self.device_box.currentText() != 'all' and text not in self.cur_data:
                return 'нет в выбранной модели'
        else:
            if text not in self.cur_data:
                return 'нет в выбранной модели'
        return text

    def __clicked_cmd(self):
        self.cmd_line.completer().setCompletionPrefix(self.cmd_line.getText())
        self.cmd_line.completer().complete()

    def __db_clicked_cmd(self):
        self.clear_param_lines()
        self.cmd_line.completer().setCompletionPrefix(self.cmd_line.getText())
        self.cmd_line.completer().complete()

    def __cmd_edit(self, text):
        """ввод в поле cmd, парсинг в режиме поиска текста"""
        if self.btn_search.isChecked():
            mathces = []
            for description in self.data_descrip_keys.keys():
                if all((re.search(r'.*\b%s.*' % x.lower(), description.lower()) for x in text.split())):
                    mathces.append(description)
                    if len(mathces) > 20:
                        break
            self.cmd_line.completer().model().setStringList(mathces)
        elif text in self.cur_data:
            self.__cmd_comp_activate(text)
        else:
            self.__line_obts_args_set_default_text()

    def __cmd_comp_select(self, text):
        if self.btn_search.isChecked():
            self.set_info_widget_text(text)
        else:
            self.__cmd_comp_activate(text)

    def __cmd_comp_activate(self, text):
        def take_arg(line, param):
            if param is None:
                line.completer().model().setStringList([])
                return None
            completes = list(param.keys())
            line.completer().model().setStringList(completes)
            line.setText(completes[0])
            return param[completes[0]]

        cmd_text = self.data_descrip_keys[text] if self.btn_search.isChecked() else text.strip()
        key = None
        if self.cur_type == SelectUVwidget.SCPICMD:
            key = self.data.uv_dict[self.current_device]['list_uv'].get(cmd_text)
        elif self.cur_type == SelectUVwidget.SOTC:
            key = self.data.sotc_dict.get(cmd_text)
        if key is not None:
            self.current_data_item = key
            self.cmd_line.setText(key.id_hex if self.cur_type == self.SCPICMD else key.id)
            self.set_info_widget_text([
                key.description,
                take_arg(self.line_obts, key.obts),
                take_arg(self.line_args, key.args)])

    def __db_clicked_param(self, line):
        line.clear()
        line.completer().setCompletionPrefix(line.text())
        line.completer().complete()
        self.__line_obts_args_set_default_text()

    def __line_obts_args_set_default_text(self):
        if self.cur_type == SelectUVwidget.SCPICMD:
            self.line_obts.setText(self.default_line_obts)
            self.line_args.setText(self.default_line_args)

    def lineArgs_comp_select(self, text):
        self.line_args.setText(text)
        self.change_info_widget_text(2, self.current_data_item.args.get(text))

    def lineOBTS_comp_select(self, text):
        self.line_obts.setText(text)
        self.change_info_widget_text(1, self.current_data_item.obts.get(text))

    def parse_list_uv(self):
        self.parse_err = None
        if self.data is not None:
            return
        try:
            self.data = DataListUV(self.path_file)
        except Exception as e:
            self.parse_err = e
            return
        self.device_box.addItems(self.data.uv_dict.keys())

    def change_data_type(self, arg):
        """Изменить поиск виджета по данным"""
        self.clear_param_lines()
        if arg == 'SCPICMD' or arg == SelectUVwidget.SCPICMD:
            self.cur_type = SelectUVwidget.SCPICMD
            self.device_label.show()
            self.device_box.show()
            self.device_box.setEnabled(True)
            self.cmd_line.set_min_text('0x')
            self.change_completer_model(self.data.uv_dict[self.current_device]['list_uv'])
            self.line_obts.show()
            self.line_obts_label.show()
            self.__line_obts_args_set_default_text()
            # self.line_obts.setDisabled(False)
        elif arg == 'SOTC' or arg == SelectUVwidget.SOTC:
            self.cur_type = SelectUVwidget.SOTC
            self.device_label.hide()
            self.device_box.hide()
            self.device_box.setEnabled(False)
            self.cmd_line.set_min_text('')
            self.change_completer_model(self.data.sotc_dict)
            self.line_obts.hide()
            self.line_obts_label.hide()
            # self.line_obts.setDisabled(True)
        self.btn_search.setChecked(False)

    def change_completer_model(self, data):
        self.cur_data = data
        self.data_descrip_keys = OrderedDict((v.description, k) for k, v in self.cur_data.items())
        self.cmd_line.completer().model().setStringList(data)

    def connect_to_args_widget(self, list_args, list_checkboxes):
        """Для поарсинга при исполнении параметров полей"""
        list_args.append(self.cmd_line)
        list_args.append(self.line_obts)
        list_args.append(self.line_args)
        list_checkboxes.extend([None, None, None])

    def btnSearchIsChecked(self):
        if self.btn_search.isChecked():
            self.cur_type_search = self.DESCRIBE
            self.cmd_line.set_min_text('')
            self.cmd_line.completer().model().setStringList(self.data_descrip_keys)
            self.cmd_line.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            # self.cmd_line.completer().setFilterMode(Qt.MatchContains)
        else:
            self.cur_type_search = self.NUMBER
            self.cmd_line.set_min_text('0x' if self.cur_type == SelectUVwidget.SCPICMD else '')
            self.cmd_line.completer().model().setStringList(self.cur_data)
            self.cmd_line.completer().setCompletionMode(QCompleter.PopupCompletion)
            # self.cmd_line.completer().setFilterMode(Qt.MatchStartsWith)
            # self.cmd_line.completer().setCompletionRole(Qt.EditRole)

    def btnSearchToogled(self, checked):
        self.clear_param_lines()
        self.btnSearchIsChecked()

    def set_info_widget_text(self, text):
        if self.info_widget is not None and self.isVisible():
            if isinstance(text, (list, tuple)):
                self.description_hex = text
                self.__set_info_widget_text(self.description_hex)
            else:
                self.description_hex = [text, None, None]
                self.info_widget.setText(text)
            self.info_widget.setFixedHeight(100)

    def change_info_widget_text(self, num, text):
        if self.info_widget is not None and self.isVisible():
            self.description_hex[num] = text
            self.__set_info_widget_text(self.description_hex)

    def __set_info_widget_text(self, text):
        new_text = ''
        for idx, x in enumerate(('%s', '\nOBTS: %s', '\nArgs: %s')):
            if text[idx]:
                new_text += x % text[idx]
        self.info_widget.setText(new_text)




####################### EXAMPLE #######################################
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
            self.runBtn = None
            QCoreApplication.setApplicationName('Search-Bar')
            QCoreApplication.setOrganizationName('VNIIEM')
            QCoreApplication.setOrganizationDomain('mcc.vniiem.ru')

            self.initUI()
            self.initParseBtn()
            self.initBtnsSelect()
            self.initTextTab()
            self.initSearchWidg()
            self.initRunBtn()
            self.button.clicked.connect(self.searchWidget.parse_list_uv)
            self.buttonSCPICMD.clicked.connect(lambda: self.searchWidget.change_data_type(SelectUVwidget.SCPICMD))
            self.buttonSOTC.clicked.connect(lambda: self.searchWidget.change_data_type(SelectUVwidget.SOTC))
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

        def initBtnsSelect(self):
            self.buttonSCPICMD = QPushButton()
            self.buttonSOTC = QPushButton()
            layoutH = QHBoxLayout()
            layoutH.addWidget(self.buttonSCPICMD)
            layoutH.addWidget(self.buttonSOTC)
            self.centralWidget().layout().addLayout(layoutH)
            self.buttonSCPICMD.setText("SCPICMD")
            self.buttonSOTC.setText("SOTC")

        def initTextTab(self):
            self.textWdiget = QTextEdit()
            self.textWdiget.setObjectName('autoCompeteInfoFrame')
            self.textWdiget.setReadOnly(True)
            self.textWdiget.setLineWrapMode(QTextEdit.WidgetWidth)
            self.textWdiget.setText('Описание')
            self.centralWidget().layout().addWidget(self.textWdiget)

        def initSearchWidg(self):
            self.searchWidget = SelectUVwidget(self.textWdiget, self)

            if self.searchWidget.parse_err is not None:
                self.textWdiget.setText(str(self.searchWidget.parse_err))
                self.searchWidget.setDisabled(True)
            else:
                self.searchWidget.setDisabled(False)
                self.searchWidget.show()
            self.centralWidget().layout().addWidget(self.searchWidget)

        def initRunBtn(self):
            self.runBtn = QPushButton()
            self.runBtn.setText('Выполнить')
            self.runBtn.clicked.connect(self._run)
            self.centralWidget().layout().addWidget(self.runBtn)

        def _run(self):
            print('Запуск %s' % self.searchWidget.cmd_line.text())

    os.chdir(pathlib.Path.cwd().parent)
    app = QApplication(sys.argv)
    app.setStyleSheet(open('styles.css', mode='r', encoding='utf-8').read())
    app.setWindowIcon(QIcon("res/mainicon.png"))

    window = MainWindow()
    window.setGeometry(1400, 800, 800, 400)
    window.show()
    sys.exit(app.exec_())
