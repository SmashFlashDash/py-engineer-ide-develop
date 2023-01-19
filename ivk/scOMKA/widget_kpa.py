import os
import threading
import time
import psutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPalette
from PyQt5.QtWidgets import QGridLayout, QWidget, QBoxLayout, QDockWidget, QLabel, QPushButton, QMenu, QAction, \
    QFileDialog, QScrollArea

from PyQt5.QtWidgets import QMessageBox

from ivk import config
from ivk.scOMKA.controll_kpa import KPAResponce
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder


class KpaWidget(QDockWidget):
    receiver_speed = config.odict((0, '16 кбит/с'), (1, '32 кбит/с'), (2, '300 кбит/с'), (3, '600 кбит/с'))
    transmiter_modulation = config.odict((0, 'данные ЗК'), (2, 'данные ЗК + дальнометрия'), (3, 'дальнометрия'),
                                         (4, 'технологический'), (5, 'технологический'))
    receiver_input = config.odict((1, 'XW2'), (2, 'XW4'))
    transmiter_output = config.odict((1, 'XW1'), (2, 'XW3'))
    is_receiving = config.odict((0, 'отсутствует'), (1, 'наличие приема'))

    kpaSignal = pyqtSignal(object)

    def __init__(self, parent, tabs_widget):
        super().__init__(parent)

        self.setWindowTitle('КПА КИС')
        self.tabs_widget = tabs_widget
        self.kpaSignal.connect(self.updateUi)

        # Создать ivk_dump dir
        folder_dump = Path(os.getcwd()).parent.joinpath('ivk_dump')
        if not folder_dump.exists():
            Path.mkdir(folder_dump)

        # Контекстное меню для сохранени дампов ТМИ
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)
        self.dump_file_path = None  # folder_dump.joinpath('TMI_DUMP %s.bin' % datetime.now().strftime('%Y.%m.%d %H_%M_%S'))
        self.write_dump = False

        self.autoLog()

        self.colored_labels = {}
        self.colored_labels_dispatcher_thread = threading.Thread(target=self.dispatchLabelColors, daemon=True)
        self.colored_labels_dispatcher_thread.start()
        self.colored_labels_lock = threading.Lock()

        self.label_queue = QLabel('?')
        self.label_letter = QLabel('?')
        self.label_receiver_frequency = QLabel('?')
        self.label_receiver_power = QLabel('?')
        self.label_receiver_speed = QLabel('?')
        self.label_transmiter_modulation = QLabel('?')
        self.label_receiver_input = QLabel('?')
        self.label_transmiter_output = QLabel('?')
        self.label_ka_id = QLabel('?')
        self.label_transmiter_power = QLabel('?')
        self.label_is_receiving = QLabel('?')
        self.label_count_msg_from_ivk = QLabel('?')
        self.label_last_ivk_msg_number = QLabel('?')
        self.label_ka_estimate_range = QLabel('?')
        self.label_ka_estimate_speed = QLabel('?')

        self.label_time = QLabel('?')

        self.widgetButtons = QWidget()
        self.widgetButtons.setLayout(QGridLayout())
        self.buttons_json = None
        self.buttons_list = None
        self.updateButtonsLayout()

        # self.setWidget(QWidget(self))
        widget = QWidget(self)
        lb = QBoxLayoutBuilder(widget, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        lb.hbox(spacing=5).add(QLabel("КА ИД:")).add(self.label_ka_id).add(QLabel("Сеанс:")).add(
            self.label_is_receiving).stretch().up() \
            .hbox(spacing=5).add(QLabel("Времени до конца сеанса")).add(self.label_time).stretch().up() \
            .hbox(spacing=5).add(QLabel("Получено сообщений от ИВК:")).add(self.label_count_msg_from_ivk).stretch().up() \
            .hbox(spacing=5).add(QLabel("Номер последнего сообщения:")).add(
            self.label_last_ivk_msg_number).stretch().up() \
            .hbox(spacing=5).add(QLabel("Литера:")).add(self.label_letter).add(QLabel("Очередь ЗК:")).add(
            self.label_queue).stretch().up() \
            .hbox(spacing=5).add(QLabel("Отстройка частоты ПРМ:")).add(self.label_receiver_frequency).stretch().up() \
            .hbox(spacing=5).add(QLabel("Мощность, поступающая на ПРМ:")).add(self.label_receiver_power).stretch().up() \
            .hbox(spacing=5).add(QLabel("Скорость декодера ПРМ:")).add(self.label_receiver_speed).stretch().up() \
            .hbox(spacing=5).add(QLabel("Режим модуляции ПРД:")).add(self.label_transmiter_modulation).stretch().up() \
            .hbox(spacing=5).add(QLabel("Вход ПРМ:")).add(self.label_receiver_input).add(QLabel("Выход ПРД:")).add(
            self.label_transmiter_output).stretch().up() \
            .hbox(spacing=5).add(QLabel("Выходная мощность ПРД:")).add(self.label_transmiter_power).stretch().up() \
            .hbox(spacing=5).add(QLabel("Оценка дальности по КА:")).add(self.label_ka_estimate_range).stretch().up() \
            .hbox(spacing=5).add(QLabel("Оценка скорости движения по КА:")).add(
            self.label_ka_estimate_speed).stretch().up() \
            .hbox(spacing=5).add(self.widgetButtons).stretch().up() \
            .stretch()
        self.hide()

        # Добавит в скролл
        scroll = QScrollArea()
        scroll.setWidget(widget)
        self.setWidget(scroll)

    # TODO: опрделить сайз кнопок
    def updateButtonsLayout(self):
        # отчитстить лэйоут от кнопок или можно юзнуть QBoxLAyoutBulder.clearAll
        self.buttons_list = []
        layout = self.widgetButtons.layout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item.widget():
                layout.removeWidget(item.widget())
        # прочитать json
        import json
        try:
            with open('/'.join(['engineers_src', 'kpa_btns.json']), 'r', encoding='utf-8') as f:
                self.buttons_json = json.load(f, object_pairs_hook=OrderedDict)
        except IOError:
            return
        # добавить кнопи
        row = 0
        column = 0
        for btn_name, cmd in self.buttons_json.items():
            btn = QPushButton()
            self.buttons_list.append(btn)
            btn.setText(btn_name)
            btn.adjustSize()
            btn.clicked.connect(self.clickButton)
            layout.addWidget(btn, row, column)
            if column <= 2:
                column += 1
            else:
                column = 0
                row += 1

    # автоматическое включение логирования
    def autoLog(self):
        if psutil.disk_usage('/').percent < 90:
            self.__saveDumpChecked(True)
            self.write_dump = True
        else:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setText("Свободного места меньше 10% автоматическое логирование ТМИ отключено")
            self.msg.setWindowTitle("Information MessageBox")
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.exec_()

    def clickButton(self, btn):
        btn = self.sender()
        command = self.buttons_json[btn.text()]
        # TODO: первый вариант послать через subprocess __runScript
        # если создать tabWidget то можно заполить текст и выполнить run_command как сабпроцесс скрипт
        # но так кнопка не будет работать если запущен скрипт их надо в disable ставить когда скрипт идет
        # from ui.tabWidget import TabWidget
        # w = TabWidget(None, file='', text='', breakpoints=None, search_options=None, need_to_update_func=None,
        #               execute_update_func=None)

        # TODO: второй вариант послать через commandsWsidget.runScript
        ## в commandsWsidget прописана функция запускающая list в потоке
        ## лучше попроовать через runscript первый вариант но как будут блочиться кнопки
        ## и поток если запущена АИП инженерская
        commands_widget = self.parentWidget().commands_dock_widget
        if not command or commands_widget.executing:
            return
        try:
            command = command.split(';')
            commands_widget.runCommand(command)
        except Exception as ex:
            print(ex)
            commands_widget.executing = False

    def updateUi(self, kpa_responce):
        if kpa_responce.unpacked is None:
            return
        if kpa_responce.msg_type == KPAResponce.RESPONCES_FROM_KPA['ДИ_КПА']['msg_type']:
            dikpa = kpa_responce.unpacked
            self.setLabelText(self.label_queue, '%d' % dikpa.queue_count)
            self.setLabelText(self.label_letter, '№%d' % dikpa.letter)
            self.setLabelText(self.label_receiver_frequency, '%.3f Гц' % dikpa.receiver_frequency)
            self.setLabelText(self.label_receiver_power, '%.3f дБм' % dikpa.receiver_power)
            # На случай кривого kpa_responce.unpacked
            if dikpa.receiver_speed in KpaWidget.receiver_speed:
                self.setLabelText(self.label_receiver_speed,
                                  '%d - %s' % (dikpa.receiver_speed, KpaWidget.receiver_speed[dikpa.receiver_speed]))
            if dikpa.transmiter_modulation in KpaWidget.transmiter_modulation:
                self.setLabelText(self.label_transmiter_modulation, '%d - %s' % (
                    dikpa.transmiter_modulation, KpaWidget.transmiter_modulation[dikpa.transmiter_modulation]))
            if dikpa.receiver_input in KpaWidget.receiver_input:
                self.setLabelText(self.label_receiver_input,
                                  '%d - %s' % (dikpa.receiver_input, KpaWidget.receiver_input[dikpa.receiver_input]))
            if dikpa.transmiter_output in KpaWidget.transmiter_output:
                self.setLabelText(self.label_transmiter_output, '%d - %s' % (
                    dikpa.transmiter_output, KpaWidget.transmiter_output[dikpa.transmiter_output]))
            self.setLabelText(self.label_ka_id, '%d' % dikpa.ka_id)
            self.setLabelText(self.label_transmiter_power, '%.3f дБ' % dikpa.transmiter_power)
            if dikpa.is_receiving in KpaWidget.is_receiving:
                self.setLabelText(self.label_is_receiving, '%s' % KpaWidget.is_receiving[dikpa.is_receiving])
                # обновление оставшегося времени до конца сеанса
                if not config.getData('StartSession') is None and dikpa.is_receiving == 1:
                    timeStart = datetime.strptime(config.getData('StartSession'), "%Y:%m:%d:%H:%M:%S")
                    timeCurrent = datetime.today()
                    self.setLabelText(self.label_time, '%.3f' % (15 - (timeCurrent - timeStart).seconds / 60))
                else:
                    self.setLabelText(self.label_time, '?')

            self.setLabelText(self.label_count_msg_from_ivk, '%d' % dikpa.count_msg_from_ivk)
            self.setLabelText(self.label_last_ivk_msg_number, '%d' % dikpa.last_ivk_msg_number)
            self.setLabelText(self.label_ka_estimate_range, '%9s м' % str(dikpa.ka_estimate_range) if abs(
                dikpa.ka_estimate_range) > 99999999 else '%.3f м' % dikpa.ka_estimate_range)
            self.setLabelText(self.label_ka_estimate_speed, '%9s м/c' % str(dikpa.ka_estimate_speed) if abs(
                dikpa.ka_estimate_speed) > 99999999 else '%.3f м/c' % dikpa.ka_estimate_speed)

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

    def kpaIncome(self, kpa_responce):
        self.kpaSignal.emit(kpa_responce)

    def __showContextMenu(self, pos):
        context_menu = QMenu(self)

        save_dump_action = QAction(QIcon('res/registry-editor.png'), 'Писать дамп ТМИ ОК_ОБР', self)
        save_dump_action.setCheckable(True)
        save_dump_action.setChecked(self.write_dump)
        save_dump_action.triggered.connect(self.__saveDumpChecked)
        context_menu.addAction(save_dump_action)

        dump_file_action = QAction(QIcon('res/save.png'), 'Сохранить дамп в новый файл', self)
        dump_file_action.triggered.connect(self.__dumpSaveDialog)
        context_menu.addAction(dump_file_action)

        context_menu.exec(self.mapToGlobal(pos))

    def __saveDumpChecked(self, checked):
        self.write_dump = checked
        self.dump_file_path = Path(os.getcwd()).parent.joinpath('ivk_dump', 'TMI_DUMP %s.bin' % datetime.now().strftime(
            '%Y.%m.%d %H_%M_%S'))

    def __dumpSaveDialog(self):
        path = self.dump_file_path.parent.joinpath('TMI_DUMP %s.bin' % datetime.now().strftime('%Y.%m.%d %H_%M_%S'))
        filename = QFileDialog.getSaveFileName(self, 'Сохранить файл', str(path), 'Бинарные файлы (*.bin)')[
            0]  # @UndefinedVariable
        if filename != '':
            if not filename.endswith('.bin'):
                filename += '.bin'
            self.dump_file_path = Path(filename)

    def showEvent(self, event):
        super().showEvent(event)

    def closeEvent(self, event):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)
        super().closeEvent(event)

    def saveSettings(self):
        return {}

    def restoreSettings(self, settings):
        pass

    def settingsKeyword(self):
        return 'MKAKPAWidget'

    def getMenuParams(self):
        return {
            'icon': 'res/control_interface.png',
            'text': 'Окно КПА МКА',
            'status_tip': 'Окно мониторинга КПА МКА'
        }
