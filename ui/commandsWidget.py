import functools
import re
import sys
import threading
import traceback
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics, QIcon
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QBoxLayout, \
    QDockWidget, QLabel, QPushButton, QComboBox, QCheckBox, QMenu, QAction, QFileDialog, QScrollArea

import ivk.cpi_framework_connections as cf
from ivk import config
from ivk.global_log import GlobalLog
from ivk.log_db import DbLog
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder

from ui.commandsSearcherCMD import SelectUVwidget

from ivk.config import updData
from cpi_framework.utils.toolsForCPI import readBinFile


class CommandsWidget(QDockWidget):
    executionSig = pyqtSignal(bool)

    def __init__(self, parent, console_widget, tabs_widget):
        super().__init__(parent)
        self.DataRead = None
        self.setWindowTitle('Команды')
        self.tabs_widget = tabs_widget
        self.console_widget = console_widget

        self.executing = False
        self.executionSig.connect(self.executionLock)

        # Контекстное меню для выгрузки команд в latex
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__showContextMenu)

        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(1)
        self.populateTree(cf.get_commands_imports(), self.tree_widget)
        self.tree_widget.currentItemChanged.connect(self.__currentItemChanged)

        self.args_widget = QWidget(self)
        self.args_widget.setObjectName('consolasBoldFont')
        self.args_widget.arg_editors = []
        self.args_widget.skip_arg_checkboxes = []
        self.args_widget.get_msg_combo = None
        self.args_widget.get_field_combo = None
        self.args_widget.wait_msg_controls = []
        self.args_widget.wait_timeout_editor = None
        self.args_widget.lb = QBoxLayoutBuilder(self.args_widget, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5),
                                                spacing=5)

        self.exchange_checkbox = QCheckBox('Послать в:', self)
        self.exchange_checkbox.setChecked(True)
        self.exchange_checkbox.setEnabled(False)

        self.hex_checkbox = QCheckBox('Hex', self)
        self.hex_checkbox.setChecked(False)
        self.hex_checkbox.setEnabled(True)

        self.log_checkbox = QCheckBox('Print log', self)
        self.log_checkbox.setChecked(True)
        self.log_checkbox.setEnabled(True)
        # сразу обновляем разрешение для вывода лога
        updData('Log', self.log_checkbox.isChecked())

        self.exchange_combo = QComboBox(self)
        self.exchange_combo.setEnabled(False)

        self.delay_combo = QComboBox(self)
        self.delay_combo.setEnabled(True)
        self.delay_combo.addItems(['0', '0.5', '1', '1.5', '2.0'])

        self.simple_checkbox = QCheckBox('Упрощенный', self)
        self.simple_checkbox.setChecked(True)
        self.simple_checkbox.setVisible(False)

        self.run_button = QPushButton(QIcon('res/start.png'), "Выполнить")
        self.run_button.clicked.connect(self.runCommand)
        self.run_button.setEnabled(False)

        self.insert_button = QPushButton(QIcon('res/insert.png'), "В скрипт")
        self.insert_button.clicked.connect(self.insertCommand)
        self.insert_button.setEnabled(False)

        self.openFile_button = QPushButton("Файл")
        self.openFile_button.clicked.connect(self.selectFile)
        self.openFile_button.setEnabled(False)
        self.openFile_button.setFixedWidth(80)

        self.delay_checkbox = QCheckBox('Задержка выдачи КПИ', self)
        self.delay_checkbox.setChecked(False)
        self.delay_checkbox.setVisible(True)


        buttons_widget = QWidget(self)
        lb = QBoxLayoutBuilder(buttons_widget, QBoxLayout.TopToBottom, spacing=6)
        lb.hbox(spacing=6).add(self.exchange_checkbox).add(self.exchange_combo).stretch().add(
            self.openFile_button).add(self.insert_button).add(self.run_button).fixW(100).up()
        lb.hbox(spacing=6).add(self.hex_checkbox).add(self.log_checkbox).add(self.simple_checkbox).stretch().up()
        lb.hbox(spacing=6).add(self.delay_checkbox).add(self.delay_combo).stretch().up()


        self.info_widget = QTextEdit()
        self.info_widget.setObjectName('autoCompeteInfoFrame')
        self.info_widget.setReadOnly(True)
        self.info_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.info_widget.setFixedHeight(30)

        self.args_widget.uv_widget = SelectUVwidget(infowidg=self.info_widget, parent=self.args_widget)

        # скролл для self.args_widget
        self.scroll_args = QScrollArea(self)
        self.scroll_args.setWidget(self.args_widget)
        self.scroll_args.setWidgetResizable(True)
        self.scroll_args.setFrameShape(0)

        bottom_widget = QWidget(self)
        lb = QBoxLayoutBuilder(bottom_widget, QBoxLayout.TopToBottom, spacing=5)
        lb.add(self.info_widget).add(self.scroll_args).add(buttons_widget)
        self.splitter = QSplitter(Qt.Vertical, self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.tree_widget)
        self.splitter.addWidget(bottom_widget)

        self.setWidget(QWidget(self))
        lb = QBoxLayoutBuilder(self.widget(), QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        lb.add(self.splitter)
        self.adjustSize()
        self.hide()

        self.hex_checkbox.clicked.connect(lambda: updData('HEX', self.hex_checkbox.isChecked()))
        self.log_checkbox.clicked.connect(lambda: updData('Log', self.log_checkbox.isChecked()))
        self.delay_checkbox.clicked.connect(lambda: (updData('DelayCheck', self.delay_checkbox.isChecked()), updData('DelayTime', self.delay_combo.currentText())))
        self.delay_combo.activated.connect(lambda: updData('DelayTime', self.delay_combo.currentText()))


    def getCommand(self):
        if not self.tree_widget.currentItem() or 'name' not in self.tree_widget.currentItem().command:
            return None

        command_params = self.tree_widget.currentItem().command
        command = command_params['name']

        if command_params['name'] == '{GET}':
            command = "Ex.get('%s', '%s', '%s')" % (
                self.exchange_combo.currentText(), self.args_widget.get_msg_combo.currentText(),
                self.args_widget.get_field_combo.currentText())
        elif command_params['name'] == '{WAIT}':
            if not self.args_widget.wait_msg_controls:
                return
            expression = ' and '.join(['{%s.%s} %s %s' % (
                c['combo_msg'].currentText(), c['combo_field'].currentText(), c['combo_operation'].currentText(),
                c['line_edit'].text() if c['line_edit'].text().strip() else 'None') for c in
                                       self.args_widget.wait_msg_controls])
            command = "Ex.wait('%s', '%s', %s)" % (
                self.exchange_combo.currentText(), expression, self.args_widget.wait_timeout_editor.text())
        else:
            command = command_params[
                'name'] if 'simple_name' not in command_params or not self.simple_checkbox.isChecked() else \
                command_params['simple_name']
            command += '(' if 'is_function' not in command_params or command_params['is_function'] else ''
            for i, arg in enumerate(self.args_widget.arg_editors):
                if self.args_widget.skip_arg_checkboxes[i] is not None and not self.args_widget.skip_arg_checkboxes[i].isChecked():
                    continue
                if arg.text():
                    if 'keyword' in command_params and command_params['keyword'][i] and not(command_params['name'] == 'CPIMD' and command_params['params'][i] == 'data'):
                        command += command_params['params'][i] + '=' + arg.text()
                    elif command_params['name'] == 'CPIMD' and command_params['params'][i] == 'data':
                        command += 'data=' + (self.DataRead if not (self.DataRead is None) else arg.text())
                    else:
                        command += arg.text()
                    if i != len(self.args_widget.arg_editors) - 1:
                        command += ', '
            if command.endswith(', '):
                command = command[:-2]

            if self.exchange_checkbox.isChecked() and self.exchange_checkbox.isEnabled() and (
                    'ex_send' not in command_params or command_params['ex_send']) and (
                    'simple_name' not in command_params or not self.simple_checkbox.isChecked()):

                command = 'Ex.send(\'%s\', %s)' % (self.exchange_combo.currentText(), command + (
                    ')' if 'is_function' not in command_params or command_params['is_function'] else ''))
            elif 'is_function' not in command_params or command_params['is_function']:
                command += ')'

        return command

    # def readBinFile(self, path, cpibase=False):
    #     s = path.split('.')[-1]
    #     if s == 'bin':
    #         with open(path, 'rb') as file:
    #             data = file.read()
    #             if cpibase and len(data) > 64:
    #                 data = data[21: 21+64]
    #             self.DataRead = "AsciiHex('0x" + data.hex() + "')"
    #     elif s == 'hex':
    #         with open(path, 'r', encoding='utf-8') as file:
    #             lines = file.readlines()
    #             data = []
    #             for line in lines:
    #                 words = line.split(r"\n")[0].split("#")[0]
    #                 for b in words.split():
    #                     data.append(b[2:] + b[:2])
    #             self.DataRead = "AsciiHex('0x" + "".join(data) + "')"
    #     return self.DataRead

    def insertCommand(self):
        command = self.getCommand()
        if not command:
            return
        self.tabs_widget.insertTextToCurrentTab(command + '\n')

    def selectFile(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Выбрать файл КПИ', os.getcwd(),
                                                  "Bin Files (*.bin);;Hex Files (*.hex)")
        if not filename:
            return

        if len(self.args_widget.arg_editors) == 1:
            cpidata = readBinFile(filename, cpibase=True, commandW=True)
            self.DataRead = cpidata
            self.args_widget.arg_editors[0].setText(cpidata)
        elif len(self.args_widget.arg_editors) == 2:
            cpipz = readBinFile(filename, cpibase=False, commandW=True)
            self.DataRead = cpipz
            self.args_widget.arg_editors[1].setText(cpipz)
        elif len(self.args_widget.arg_editors) == 3:
            cpiMDdata = readBinFile(filename, cpibase=False, commandW=True)
            self.DataRead = cpiMDdata
            self.args_widget.arg_editors[1].setText(cpiMDdata)

        DbLog.log('одиночная команда', 'выбран бинарный файл ' + filename, False, None, None)

    def runCommand(self, command=None):
        command = command if command else self.getCommand()  # передать комманду
        # command = self.getCommand()
        if not command or self.executing:
            return
        self.executing = True
        if isinstance(command, (list, tuple)):
            t = threading.Thread(target=lambda: self.__runCommandGroup(command), daemon=True)
            t.start()
        else:
            t = threading.Thread(target=lambda: self.__runCommand(command), daemon=True)
            t.start()

    def __runCommand(self, command):
        self.executionSig.emit(True)

        script, line_correction = cf.generate_command_widget_script(command, "одиночная_команда")

        self.console_widget.onExecutionStart()
        # self.console_widget.writeNormal('{#d6ff59}Начало выполнения скрипта "одиночная_команда"\n')
        DbLog.log('одиночная_команда', "Начало выполнения скрипта", False, None, script)

        cmd_stdout = CommandStdOut()
        cmd_stdout.redirect()

        try:
            exec(script, {}, {})
            self.console_widget.writeNormal(cmd_stdout.total_buffer)
        except Exception as exc:
            self.console_widget.writeError('Ошибка: %s\n' % str(exc))
            GlobalLog.log(threading.get_ident(), 'одиночная команда', str(exc) + '\n', True)
            DbLog.log('одиночная_команда', str(exc), True, None, traceback.format_exc())

        cmd_stdout.revert()

        # self.console_widget.writeNormal('{#ffcd57}Конец выполнения скрипта "одиночная_команда"\n')
        DbLog.log('одиночная_команда', "Конец выполнения скрипта", False, None, cmd_stdout.total_buffer)

        self.executionSig.emit(False)
        self.executing = False

    def __runCommandGroup(self, commands_group):
        self.executionSig.emit(True)
        DbLog.log('одиночная_команда', "Начало выполнения скрипта", False, None, str(commands_group))
        for command in commands_group:
            isSleep = False
            command = command.strip()
            if command.startswith('sleep'):
                isSleep = True
            script, line_correction = cf.generate_command_widget_script(command, "одиночная_команда")
            self.console_widget.onExecutionStart()
            cmd_stdout = CommandStdOut()
            cmd_stdout.redirect()
            try:
                exec(script, {}, {})
                if not isSleep:
                    self.console_widget.writeNormal(cmd_stdout.total_buffer)
            except Exception as exc:
                self.console_widget.writeError('Ошибка: %s\n' % str(exc))
                cmd_stdout.revert()
                GlobalLog.log(threading.get_ident(), 'одиночная команда', str(exc) + '\n', True)
                DbLog.log('одиночная_команда', str(exc), True, None, traceback.format_exc())
                break
            finally:
                cmd_stdout.revert()
                DbLog.log('одиночная_команда', "Конец выполнения скрипта", False, None, cmd_stdout.total_buffer)
        self.executionSig.emit(False)
        self.executing = False

    def executionLock(self, executing):
        self.run_button.setEnabled(not executing)
        self.insert_button.setEnabled(not executing)
        self.exchange_checkbox.setEnabled(not executing)
        self.exchange_combo.setEnabled(not executing)
        self.tree_widget.setEnabled(not executing)
        self.args_widget.setEnabled(not executing)
        for btn in self.parentWidget().exchange_docks[0].buttons_list:
            btn.setEnabled(not executing)

    def populateTree(self, commands, widget):
        for command in commands:
            text = command[
                'category' if 'category' in command else 'translation' if 'translation' in command else 'name']
            item = QTreeWidgetItem(widget, [text])
            item.command = command
            if 'children' in command:
                self.populateTree(command['children'], item)
            if isinstance(widget, QTreeWidget):
                widget.addTopLevelItem(item)
            else:
                widget.addChild(item)

    def __currentItemChanged(self, current, previous):
        # Очистка интерфейса args_widget и сохраненных элементов
        self.exchange_combo.clear()
        self.args_widget.lb.clearAll(protected_widgets=[self.args_widget.uv_widget])  # не убирать SearchUvWidget
        self.args_widget.arg_editors.clear()
        self.args_widget.skip_arg_checkboxes.clear()
        self.args_widget.get_msg_combo = None
        self.args_widget.get_field_combo = None
        self.args_widget.wait_msg_controls.clear()
        self.args_widget.wait_timeout_editor = None
        self.args_widget.uv_widget.hide()

        height = 5
        # Создание интерфейса для команды получения
        if 'name' in current.command and current.command['name'] == '{GET}':
            self.args_widget.get_msg_combo = QComboBox(self.args_widget)
            self.updCombo(self.args_widget.get_msg_combo, list(current.command['msg_fields'].keys()))
            self.args_widget.get_field_combo = QComboBox(self.args_widget)
            self.updCombo(self.args_widget.get_field_combo,
                          current.command['msg_fields'][next(iter(current.command['msg_fields']))])
            self.args_widget.get_msg_combo.currentTextChanged.connect(
                lambda text: self.updCombo(self.args_widget.get_field_combo,
                                           self.tree_widget.currentItem().command['msg_fields'][text]))
            self.args_widget.lb.hbox(spacing=5).add(self.args_widget.get_msg_combo, object_name='consolasBoldFont').add(
                self.args_widget.get_field_combo, object_name='consolasBoldFont').up()
            height += 30

        # Создание интерфейса для команды получения
        elif 'name' in current.command and current.command['name'] == '{WAIT}':
            self.args_widget.wait_timeout_editor = QLineEdit(str(current.command['default_timeout']), self.args_widget)
            add_btn = QPushButton(QIcon('res/plus.png'), '', self.args_widget)
            add_btn.clicked.connect(self.addMsgFieldArgControls)
            self.args_widget.lb.hbox(spacing=5).add(QLabel('timeout'), object_name='consolasBoldFont').add(
                self.args_widget.wait_timeout_editor, object_name='consolasBoldFont').fixW(100).stretch().add(
                add_btn).fix(23, 23).up()
            height += 30

        # Показать интерфейс SearchUvWidget
        elif 'searcher_type' in current.command:
            if self.args_widget.uv_widget.parse_err is not None:
                self.info_widget.setText(str(self.args_widget.uv_widget.parse_err))
                self.args_widget.uv_widget.setDisabled(True)
            else:
                self.args_widget.uv_widget.setDisabled(False)
                self.args_widget.uv_widget.change_data_type(current.command['searcher_type'])
                self.args_widget.lb.addWidget(self.args_widget.uv_widget)
                self.args_widget.uv_widget.connect_to_args_widget(self.args_widget.arg_editors,
                                                                  self.args_widget.skip_arg_checkboxes)
                self.args_widget.uv_widget.show()
                height += self.args_widget.uv_widget.minimumHeight()


        # Создание интерфейса для команды отправки
        elif 'params' in current.command and current.command['params']:
            fm = QFontMetrics(self.args_widget.font())
            label_w = max(fm.width(param) for param in current.command['params'])
            for i, param in enumerate(current.command['params']):
                label = QLabel(param, self.args_widget)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                line_edit = QLineEdit(current.command['values'][i], self.args_widget)
                skip_checkbox = None

                if 'skip_params' in current.command and current.command['skip_params'][i]:
                    skip_checkbox = QCheckBox(current.command['skip_params'][i], self)
                    skip_checkbox.setChecked(True)
                    skip_checkbox.stateChanged.connect(
                        functools.partial(lambda le, state: le.setEnabled(state != Qt.Unchecked), line_edit))

                if skip_checkbox is not None:
                    self.args_widget.lb.hbox(spacing=5).add(label, object_name='consolasBoldFont').fixW(label_w).add(
                        line_edit, object_name='consolasFont').fixH(23).add(skip_checkbox).up()
                    self.args_widget.skip_arg_checkboxes.append(skip_checkbox)
                else:
                    self.args_widget.lb.hbox(spacing=5).add(label, object_name='consolasBoldFont').fixW(label_w).add(
                        line_edit, object_name='consolasFont').fixH(23).up()
                    self.args_widget.skip_arg_checkboxes.append(None)
                self.args_widget.arg_editors.append(line_edit)
                height += 30

        self.args_widget.setFixedHeight(height)

        # Создание интерфейса для описания
        if 'description' in current.command and current.command['description']:
            self.info_widget.setText(current.command['description'])
            self.info_widget.setFixedHeight(
                150)  # дабы вертикальный скорлл влиял на wordWrap только когда необходимо (при достижении макс высоты textedit)
            fm = QFontMetrics(self.info_widget.font())
            lines = 0
            block = self.info_widget.document().begin()
            while block.isValid():
                if not block.layout():
                    continue
                lines += block.layout().lineCount()
                block = block.next()
            h = fm.lineSpacing() * lines + 15
            self.info_widget.setFixedHeight(150 if h > 150 else h)
        elif 'searcher_type' in current.command:
            self.info_widget.setFixedHeight(100)
        else:
            self.info_widget.clear()
            self.info_widget.setFixedHeight(30)

        # Наполнение комбобокса пунктов назначения
        if 'queues' in current.command:
            self.exchange_combo.addItems(current.command['queues'])
            self.exchange_combo.setCurrentIndex(0)

        # Видимость чекбокса для упрощенных команд
        self.simple_checkbox.setVisible('simple_name' in current.command)
        self.simple_checkbox.setChecked('simple_name' in current.command)

        # Врубание/вырубание кнопок в зависимоит от команды
        self.run_button.setEnabled(current and 'name' in current.command and current.command['name'] != 'OBTS' and (
                'is_function' not in current.command or current.command['is_function']))
        self.insert_button.setEnabled(current and 'name' in current.command)
        self.exchange_checkbox.setEnabled(
            current and 'name' in current.command and current.command['name'] != 'OBTS' and (
                    'ex_send' not in current.command or current.command['ex_send']))
        self.exchange_combo.setEnabled(current and 'name' in current.command and (
                'ex_send' not in current.command or current.command[
            'ex_send']) and 'queues' in current.command and len(current.command['queues']) > 1)
        # self.openFile_button.setEnabled(current and 'name' in current.command and
        #                                 'params' in current.command and 'path' in current.command['params'])
        self.openFile_button.setEnabled(current and 'name' in current.command and
                                        'params' in current.command and 'name' in current.command and current.command[
                                            'name'] in ('CPIMD', 'CPIBASE', 'CPIPZ'))

        # очищаем Данные КПИМД при выборе любой ддругой команды
        self.__dataIsNone()



    def addMsgFieldArgControls(self):
        controls = config.odict()
        cmd = self.tree_widget.currentItem().command

        combo_msg = QComboBox(self.args_widget)
        self.updCombo(combo_msg, list(cmd['msg_fields'].keys()))
        controls['combo_msg'] = combo_msg

        combo_field = QComboBox(self.args_widget)
        self.updCombo(combo_field, cmd['msg_fields'][next(iter(cmd['msg_fields']))])
        controls['combo_field'] = combo_field

        combo_msg.currentTextChanged.connect(lambda text: self.updCombo(combo_field, cmd['msg_fields'][text]))

        combo_operation = QComboBox(self.args_widget)
        combo_operation.addItems(['==', '!=', '>', '>=', '<', '<='])
        controls['combo_operation'] = combo_operation

        line_edit = QLineEdit(self.args_widget)
        controls['line_edit'] = line_edit

        btn = QPushButton(QIcon('res/minus.png'), '', self.args_widget)
        btn.clicked.connect(lambda: self.removeMsgFieldArgControls(controls))
        controls['btn'] = btn

        self.args_widget.lb.hbox(spacing=5).add(combo_msg, object_name='consolasBoldFont').fixW('+30').add(combo_field,
                                                                                                           object_name='consolasBoldFont').fixW(
            '+30').add(combo_operation, object_name='consolasBoldFont').fixW('+30').add(line_edit,
                                                                                        object_name='consolasBoldFont').add(
            btn).fix(23, 23).up()
        self.args_widget.wait_msg_controls.append(controls)
        self.args_widget.setFixedHeight(self.args_widget.height() + 30)

    def removeMsgFieldArgControls(self, controls):
        for w in controls.values():
            self.args_widget.lb.removeWidgetRecursive(w)
        self.args_widget.wait_msg_controls.remove(controls)
        self.args_widget.setFixedHeight(self.args_widget.height() - 30)

    def updCombo(self, combo, new_items):
        combo.clear()
        combo.addItems(new_items)
        combo.setCurrentIndex(0)

    def commandsToLatex(self):
        filename = QFileDialog.getSaveFileName(self, 'Сохранить файл', None, 'Latex файлы (*.tex)')[
            0]  # @UndefinedVariable
        if filename != '':
            if not filename.endswith('.tex'):
                filename += '.tex'

            tex = self.__commandsToLatex(cf.get_commands_imports(), '')
            if tex:
                tex += '\\end{longtable} \n\n'

            f = open(filename, mode='w', encoding='utf-8')
            f.write(tex)
            f.close()

    def __commandsToLatex(self, commands, tex):
        for command in commands:
            if 'category' in command:
                table_index = 1
                if tex:
                    tex += '\\end{longtable} \n\n'
                    i = tex.rfind('label{table')
                    if i != -1:
                        table_index = int(tex[i + 20:tex.find('}', i + 20)]) + 1
                if 'description' in command:
                    tex += '%s Такие команды представлены в таблице \\ref{table:commands%d}. \n\n' % (
                        command['description'].replace('"', "''").replace('_', '\\_').replace('{', '\\{').replace('}',
                                                                                                                  '\\}'),
                        table_index)
                tex += '\\begin{longtable}{|m{0.3\\textwidth}|m{0.65\\textwidth}|} \n'
                tex += '    \\caption{Команды категории \'\'%s\'\'} \n' % command['category']
                tex += '    \\label{table:commands%d} \\\\ \n' % table_index
                tex += '    \\hline \n'
                tex += '    Название & Описание \\\\ \\hline \n'

            else:
                name = command['translation' if 'translation' in command else 'name']
                name = name.replace('"', "''").replace('_', '\\_').replace('{', '\\{').replace('}', '\\}')

                # Разбор описания и создание списка параметров
                description = command['description'] if 'description' in command else ' '
                if description != ' ':
                    description = description.replace('"', "''").replace('_', '\\_').replace('{', '\\{').replace('}',
                                                                                                                 '\\}')
                    itemized_description = ''
                    params_level = ''
                    for line in description.splitlines():
                        if re.match(r'^\s+-', line):
                            spaces = ' ' * (len(line) - len(line.lstrip(' ')))
                            if params_level != spaces:
                                itemized_description += '\\begin{itemize}\n' if len(params_level) < len(
                                    spaces) else '\\end{itemize}\n'
                                params_level = spaces
                            itemized_description += '\\item[--] \\texttt{%s}%s\n' % (
                                line[len(params_level) + 1:line.find(':')], line[line.find(':'):])
                        else:
                            itemized_description += line + '\n'
                    while params_level:
                        itemized_description += '\\end{itemize}\n'
                        params_level = params_level[:-2]
                    description = itemized_description
                # Добавление имени и описания
                tex += '    %s & %s \n    \\\\ \\hline \n' % (name, description)

                # Добавление примера, если есть
                if 'example' in command:
                    tex += '\\multicolumn{2}{|}{} \n' + \
                           '\\hfill \\begin{minipage}{0.97\\textwidth} \n' + \
                           '\\begin{lstlisting}[style=talbestyle] \n' + \
                           command['example'] + ' \n' + \
                           '\\end{lstlisting}  \n' + \
                           '\\end{minipage} \\hfill\\vline \n' + \
                           '\\\\ \\hline \n'

            if 'children' in command:
                tex = self.__commandsToLatex(command['children'], tex)
        return tex

    def __dataIsNone(self):
        self.DataRead = None

    def __showContextMenu(self, pos):
        context_menu = QMenu(self)
        latex_action = QAction(QIcon('res/save.png'), 'Выгрузить команды в Latex', self)
        latex_action.triggered.connect(self.commandsToLatex)
        context_menu.addAction(latex_action)
        context_menu.exec(self.mapToGlobal(pos))

    def showEvent(self, event):
        self.splitter.real_sizes = None
        super().showEvent(event)

    def closeEvent(self, event):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)
        self.splitter.real_sizes = self.splitter.sizes()
        super().closeEvent(event)

    def saveSettings(self):
        return {'sizes': self.splitter.real_sizes or self.splitter.sizes()}

    def restoreSettings(self, settings):
        self.splitter.real_sizes = settings['sizes']
        self.splitter.setSizes(self.splitter.real_sizes)

    def settingsKeyword(self):
        return 'CommandsWidget'


class CommandStdOut:
    def __init__(self):
        self.real_stdout = sys.stdout
        self.total_buffer = ""

    def write(self, stream):
        self.real_stdout.write(stream)
        self.total_buffer += stream
        if "\n" in stream:
            self.flush()

    def flush(self):
        self.real_stdout.flush()

    def redirect(self):
        sys.stdout = self

    def revert(self):
        sys.stdout = self.real_stdout
