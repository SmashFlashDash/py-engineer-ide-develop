import re
from datetime import datetime
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QDockWidget, QSplitter, QWidget, QLabel, QBoxLayout, QListWidget, \
    QListWidgetItem, QMenu, QAction, QFileDialog
from PyQt5.QtGui import QColor, QTextCursor, QIcon, QFontMetrics, QFont, QBrush
from PyQt5.QtCore import Qt, QEventLoop, QObject, pyqtSignal

from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder


class ConsoleWidget(QDockWidget):
    def __init__(self, parent, title, settings_keyword):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.settings_keyword = settings_keyword
        self.setWidget(IvkConsole(self, lambda: False, lambda: True))
        self.hide()

    def closeEvent(self, event):
        if hasattr(self.parent(), 'onDockClose'):
            self.parent().onDockClose(self)
        super().closeEvent(event)

    def settingsKeyword(self):
        return self.settings_keyword

    def saveSettings(self):
        # pass
        self.widget().saveSettings()

    def restoreSettings(self, settings):
        self.widget().restoreSettings(settings)
        # pass


class IvkConsole(QWidget):
    WRITE_NORMAL = 1
    WRITE_ERROR = 2
    WRITE_PDB = 3
    WRITE_INPUT = 4

    MAIN_COLOR = QColor(255, 255, 255)
    ERROR_COLOR = QColor(255, 92, 133)
    TIME_COLOR = QColor(174, 219, 164)

    colorWriteSignal = pyqtSignal(str, int)
    inputRequestedSignal = pyqtSignal(bool, str)
    inputEndedSignal = pyqtSignal(str)

    addSubThreadSignal = pyqtSignal(object)
    removeSubThreadSignal = pyqtSignal(object, bool)
    subThreadSuspendSignal = pyqtSignal(str)
    subThreadSelectedSignal = pyqtSignal(object)

    def __init__(self, parent, isPdbModeFunc, printTimeFunc):
        super().__init__(parent)
        self.isPdbModeFunc = isPdbModeFunc
        self.printTimeFunc = printTimeFunc

        self.colorWriteSignal.connect(self.__colorWrite)
        self.inputRequestedSignal.connect(self.__onInputRequest)
        self.inputEndedSignal.connect(lambda command: self.onInputEnded())

        self.line_edit_normal_css = 'normalInput'
        self.line_edit_pdb_css = 'pdbInput'
        self.waiting_input = False
        self.input_from_pdb = False

        self.console = QTextEdit(self)
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.NoWrap)
        self.console.setObjectName('console')
        self.console.setContextMenuPolicy(Qt.CustomContextMenu)
        self.console.customContextMenuRequested.connect(self.__showContextMenu)

        self.pdb_console = QTextEdit(self)
        self.pdb_console.setReadOnly(True)
        self.pdb_console.setLineWrapMode(QTextEdit.NoWrap)
        self.pdb_console.setObjectName('pdbConsole')

        self.sub_thread_list = QListWidget(self)
        self.sub_thread_list.setCursor(Qt.ArrowCursor)
        self.sub_thread_list.setSelectionMode(QListWidget.SingleSelection)

        self.console_splitter = QSplitter(Qt.Horizontal, self)
        self.console_splitter.setChildrenCollapsible(False)
        self.console_splitter.addWidget(self.sub_thread_list)
        self.console_splitter.addWidget(self.console)
        self.console_splitter.addWidget(self.pdb_console)

        self.line_edit_label = QLabel('Ввод:')
        self.line_edit_label.setStyleSheet('font: 14pt "Consolas"; font-weight: bold;')
        self.line_edit_label.setVisible(False)
        self.line_edit_label_font_metrics = QFontMetrics(QFont("Consolas", 14, QFont.Bold))

        self.line_edit = CommandLineEdit(self)
        self.line_edit.setObjectName(self.line_edit_normal_css)

        lb = QBoxLayoutBuilder(self, QBoxLayout.TopToBottom, margins=(3, 3, 3, 3), spacing=5)
        lb.add(self.console_splitter) \
            .hbox(spacing=2) \
            .add(self.line_edit_label).fix() \
            .add(self.line_edit)

        self.line_edit.inputEndSignal.connect(self.__lineEditInputEnded)
        self.addSubThreadSignal.connect(self.__addSubThread)
        self.removeSubThreadSignal.connect(self.__removeSubThread)
        self.subThreadSuspendSignal.connect(self.__subThreadSuspended)
        self.sub_thread_list.currentItemChanged.connect(self.__subThreadCurrentChanged)

    def writeNormal(self, stream):
        self.colorWriteSignal.emit(stream, IvkConsole.WRITE_NORMAL)

    def writeInput(self, stream):
        self.colorWriteSignal.emit('{#b5fff5}%s' % stream, IvkConsole.WRITE_INPUT)

    def writeError(self, stream):
        self.colorWriteSignal.emit(stream, IvkConsole.WRITE_ERROR)

    def writePdb(self, stream):
        self.colorWriteSignal.emit(stream, IvkConsole.WRITE_PDB)

    def sendContinue(self):
        self.line_edit.command = '!c'
        self.line_edit.inputEndSignal.emit()

    def sendNext(self):
        self.line_edit.command = '!n'
        self.line_edit.inputEndSignal.emit()

    def sendPause(self):
        self.inputEndedSignal.emit('!p')

    def onExecutionStart(self):
        self.waiting_input = False

    def __onInputRequest(self, from_pdb, label):
        self.input_from_pdb = from_pdb

        self.line_edit.setObjectName(self.line_edit_normal_css if not from_pdb else self.line_edit_pdb_css)
        self.line_edit.style().unpolish(self.line_edit)
        self.line_edit.style().polish(self.line_edit)
        self.line_edit.clear()
        self.line_edit.update()

        self.line_edit_label.setText(label)
        self.line_edit_label.setFixedWidth(self.line_edit_label_font_metrics.width(label) + 10)

        if from_pdb and self.isPdbModeFunc() or not from_pdb:
            self.line_edit.setVisible(True)
            self.line_edit_label.setVisible(True)
            self.pdb_console.setVisible(from_pdb)
            if from_pdb:
                self.console_splitter.setSizes(self.console_splitter.real_sizes)
            self.line_edit.setFocus(Qt.MouseFocusReason)
            self.pdb_console.ensureCursorVisible()
            self.console.ensureCursorVisible()

        self.waiting_input = True

    def __lineEditInputEnded(self):
        if self.waiting_input:
            self.waiting_input = False
            command = self.line_edit.command
            if self.input_from_pdb:
                thread = self.sub_thread_list.currentItem().thread
                self.writePdb(
                    '[КОМАНДА ПОТОКУ %s "%s"] <<< %s\n' % (thread['thread_id'], thread['thread_name'], command))
            else:
                self.writeNormal('{#b5fff5}%s\n' % command)
            if self.sub_thread_list.currentItem():
                self.sub_thread_list.currentItem().setBackground(QColor(255, 255, 255))
            self.inputEndedSignal.emit(command)

    def onInputEnded(self):
        self.waiting_input = False
        if self.pdb_console.isVisible():
            self.console_splitter.real_sizes = self.console_splitter.sizes()
        self.pdb_console.setVisible(False)
        self.line_edit.setVisible(False)
        self.line_edit_label.setVisible(False)
        self.update()

    def __colorWrite(self, text, mode):
        if mode == IvkConsole.WRITE_PDB:
            self.pdb_console.insertPlainText(text)
            self.pdb_console.moveCursor(QTextCursor.End)
            if '\n' in text:
                self.pdb_console.ensureCursorVisible()
        else:
            if mode == IvkConsole.WRITE_NORMAL and self.printTimeFunc() and text.strip():
                self.console.moveCursor(QTextCursor.End)
                self.console.setTextColor(IvkConsole.TIME_COLOR)
                self.console.insertPlainText('[%s] ' % datetime.now().strftime(r'%d-%m-%Y %H:%M:%S.%f')[:-3])
            istart = text.find('{#')
            if istart != -1:
                while istart != -1:
                    icolor = text.find('}', istart + 2)
                    iend = text.find('{#', icolor + 1)
                    self.console.moveCursor(QTextCursor.End)
                    self.console.setTextColor(QColor(text[istart + 1:icolor]))
                    self.console.insertPlainText(text[icolor + 1:] if iend == -1 else text[icolor + 1:iend])
                    istart = iend
            else:
                self.console.moveCursor(QTextCursor.End)
                self.console.setTextColor(
                    IvkConsole.ERROR_COLOR if mode == IvkConsole.WRITE_ERROR else IvkConsole.MAIN_COLOR)
                self.console.insertPlainText(text)
            self.console.moveCursor(QTextCursor.End)
            if '\n' in text:
                self.pdb_console.ensureCursorVisible()

    def onPdbModeChanged(self, pdb_mode):
        if self.pdb_console.isVisible() and not pdb_mode:
            self.console_splitter.real_sizes = self.console_splitter.sizes()
        if pdb_mode and self.waiting_input and self.input_from_pdb and not self.pdb_console.isVisible():
            self.pdb_console.setVisible(True)
            self.console_splitter.setSizes(self.console_splitter.real_sizes)
        self.pdb_console.setVisible(pdb_mode and self.waiting_input and self.input_from_pdb)
        self.line_edit.setVisible(pdb_mode if self.input_from_pdb and self.waiting_input else self.waiting_input)
        self.line_edit_label.setVisible(pdb_mode if self.input_from_pdb and self.waiting_input else self.waiting_input)
        self.pdb_console.ensureCursorVisible()
        self.console.ensureCursorVisible()

    ###################################################################################################################
    ############################################# SUB THREAD LIST #####################################################
    ###################################################################################################################

    def onSubThreadsCheckboxStateChanged(self, checked):
        if self.sub_thread_list.isVisible() and not checked:
            self.console_splitter.real_sizes = self.console_splitter.sizes()
        if checked and not self.sub_thread_list.isVisible():
            self.sub_thread_list.setVisible(True)
            self.console_splitter.setSizes(self.console_splitter.real_sizes)
        else:
            self.sub_thread_list.setVisible(checked)

    def __addSubThread(self, thread):
        item = QListWidgetItem(thread['thread_name'], self.sub_thread_list)
        item.thread = thread
        self.sub_thread_list.addItem(item)

    def __removeSubThread(self, thread, is_main_thread):
        if is_main_thread:
            self.sub_thread_list.clear()
        else:
            for row in range(self.sub_thread_list.count()):
                if self.sub_thread_list.item(row).thread is thread:
                    self.sub_thread_list.takeItem(row)
                    break

    def __subThreadSuspended(self, thread_id):
        for row in range(self.sub_thread_list.count()):
            item = self.sub_thread_list.item(row)
            if item.thread['thread_id'] == thread_id:
                self.sub_thread_list.setCurrentItem(item)
                item.setBackground(QColor(255, 251, 184) if item.thread['waiting_pdb_input'] else QColor(168, 255, 255))
                break

    def __subThreadCurrentChanged(self, current, previous):
        if current:
            if previous and previous.thread['waiting_input'] and not current.thread['waiting_input']:
                self.sub_thread_list.setCurrentItem(previous)
                self.sub_thread_list.update()
                return
            if current.thread['waiting_input']:
                self.__onInputRequest(False, 'Ввод (%s)' % current.thread['thread_name'])
            elif current.thread['waiting_pdb_input']:
                self.__onInputRequest(True, 'DBG (%s)' % current.thread['thread_name'])
            else:
                self.onInputEnded()
            self.subThreadSelectedSignal.emit(current.thread)

    ###################################################################################################################
    ########################################### SHOW/HIDE/SETTINGS ####################################################
    ###################################################################################################################

    def showEvent(self, event):
        if not hasattr(self.console_splitter, 'real_sizes'):
            self.console_splitter.real_sizes = self.console_splitter.sizes()
            self.pdb_console.setVisible(False)
            self.line_edit.setVisible(False)
            self.sub_thread_list.setVisible(False)
        super().showEvent(event)

    def saveSettings(self):
        return {'console_sizes': self.console_splitter.real_sizes}

    def restoreSettings(self, settings):
        if 'console_sizes' in settings.keys():
            self.console_splitter.real_sizes = settings['console_sizes']
            self.console_splitter.setSizes(self.console_splitter.real_sizes)
            self.pdb_console.setVisible(False)
            self.line_edit.setVisible(False)
            self.sub_thread_list.setVisible(
                'sub_threads_check_state' in settings and settings['sub_threads_check_state'] == Qt.Checked)

    # контекстное меню для консоли
    def __showContextMenu(self, pos):
        context_menu = QMenu(self)
        claer_log_action = QAction(QIcon('res/cleaning.png'), "Очистить лог")
        save_text_file = QAction(QIcon('res/save_as.png'), "Сохранить лог в файл", self.console)
        claer_log_action.triggered.connect(self.console.clear)
        save_text_file.triggered.connect(self.__saveLogConsole)
        context_menu.addAction(claer_log_action)
        context_menu.addAction(save_text_file)
        context_menu.exec(self.mapToGlobal(pos))

    # запись лог из консоли в файл
    def __saveLogConsole(self):
        try:
            save_file = QFileDialog.getSaveFileName(None, 'SaveTextFile', "/", "Text Files (*.txt)")
            logText = self.console.toPlainText()
            if save_file[0]:
                with open(save_file[0], 'w') as file:
                    file.write(logText)
        except Exception:
            from ui.components.commons import Commons
            Commons.WarningBox('Ошибка', 'Невозможно сохранить файл в данную папку.\nПопробуйте в Домашней директории пользователя.')


class CommandLineEdit(QLineEdit):
    inputEndSignal = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.command = ''

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.command = self.text()
            self.clear()
            self.inputEndSignal.emit()
        return super().keyPressEvent(event)
