import ntpath
import os
import threading

import PyQt5
from PyQt5 import Qt as qt
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QCheckBox, QPushButton, QSplitter, QBoxLayout

from ivk import cpi_framework_connections as cfc
from ivk.global_log import GlobalLog
from ivk.log_db import DbLog
from ivk.pydevd_runner import PyDevDRunner
from ui.components.labels import GifLabelSaveSpace
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.consoleWidget import IvkConsole
from ui.textEditor import TextEditor


class TabWidget(QWidget):
    modifiedStateChanged = pyqtSignal(int)
    execStarting = pyqtSignal()
    execEnded = pyqtSignal(int, str)

    def __init__(self, parent, file, text, breakpoints, search_options, need_to_update_func, execute_update_func):
        super().__init__(parent)
        self.index = None
        self.runner = None
        self.initUI(file, text, breakpoints, search_options, need_to_update_func, execute_update_func)

        self.execStarting.connect(self.text_edit.beforeScriptStart)
        self.execStarting.connect(self.__executionStarted)
        self.execEnded.connect(self.text_edit.afterScriptEnd)
        self.execEnded.connect(self.__executionEnded)

        self.console.inputRequestedSignal.connect(lambda from_pdb, label: self.__inputRequested(from_pdb))
        self.console.inputEndedSignal.connect(lambda command: self.__inputEnded())
        self.console.inputEndedSignal.connect(lambda command: self.runner.sendInput(command))
        self.console.subThreadSelectedSignal.connect(lambda thread: self.runner.onThreadChanged(thread))
        self.console.subThreadSelectedSignal.connect(self.__subThreadChanged)

        self.show_pdb_checkbox.stateChanged.connect(lambda state: self.console.onPdbModeChanged(state == Qt.Checked))
        self.show_sub_threads_checkbox.stateChanged.connect(
            lambda state: self.console.onSubThreadsCheckboxStateChanged(state == Qt.Checked))

        self.text_edit.lintingEnded.connect(
            lambda lints, line_correction, run_func, fail_func: self.loading_widget.setVisible(False))
        self.text_edit.selectionChanged.connect(
            lambda: self.run_button.setText("Запуск выделенного" if self.text_edit.hasSelectedText() else "Запуск"))

    def initUI(self, file, text, breakpoints, search_options, need_to_update_func, execute_update_func):
        self.text_edit = TextEditor(self,
                                    file,
                                    text,
                                    breakpoints,
                                    search_options,
                                    {'need_to_update': need_to_update_func,
                                     'execute_update': execute_update_func},
                                    lambda: self.modifiedStateChanged.emit(self.index),
                                    self.updateExecutorBreakpoint
                                    )

        self.ac = qt.QAction('', self)
        self.ac.setShortcut(qt.QKeySequence('Ctrl+.'))
        self.addAction(self.ac)
        self.ac.triggered.connect(self.setComment)

        self.loading_widget = GifLabelSaveSpace('res/loading_orange_16.gif', visible=False, fix_w=16, fix_h=16)

        self.console = IvkConsole(self, lambda: self.show_pdb_checkbox.checkState() == Qt.Checked,
                                  lambda: self.print_time_checkbox.checkState() == Qt.Checked)

        self.show_pdb_checkbox = QCheckBox('Показать окно отладки', self)
        self.show_sub_threads_checkbox = QCheckBox('Показать потоки', self)
        self.print_time_checkbox = QCheckBox('Печать времени', self)
        self.print_time_checkbox.setChecked(True)

        self.run_button = QPushButton(QIcon('res/start.png'), "Запуск выделенного")
        self.run_button.clicked.connect(self.runScript)

        self.continue_button = QPushButton(QIcon('res/btn_continue.png'), '')
        self.continue_button.setToolTip('Продолжить')
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self.console.sendContinue)

        self.pause_button = QPushButton(QIcon('res/btn_pause.png'), '')
        self.pause_button.setToolTip('Пауза')
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.console.sendPause)

        self.stop_button = QPushButton(QIcon('res/btn_stop.png'), '')
        self.stop_button.setToolTip('Стоп')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(lambda: self.runner.terminate())

        self.next_button = QPushButton(QIcon('res/btn_next.png'), '')
        self.next_button.setToolTip('Далее')
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.console.sendNext)

        self.bottom_widget = QWidget(self)
        lb = QBoxLayoutBuilder(self.bottom_widget, QBoxLayout.TopToBottom, margins=(3, 3, 3, 3), spacing=5)
        lb.hbox(spacing=5) \
            .add(self.run_button).fix() \
            .add(self.show_sub_threads_checkbox).fix() \
            .add(self.print_time_checkbox).fix().stretch() \
            .add(self.show_pdb_checkbox).fix() \
            .add(self.continue_button).fix() \
            .add(self.pause_button).fix() \
            .add(self.stop_button).fix() \
            .add(self.next_button).fix() \
            .up() \
            .add(self.console)
        self.run_button.setText("Запуск")

        self.splitter = QSplitter(Qt.Vertical, self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.text_edit)
        self.splitter.addWidget(self.bottom_widget)

        lb = QBoxLayoutBuilder(self, QBoxLayout.TopToBottom, spacing=5)
        lb.add(self.splitter)


    def modified(self):
        return self.text_edit.modified

    def text(self, line=None):
        return self.text_edit.text() if line is None else self.text_edit.text(line)

    def executing(self):
        return self.text_edit.executing

    def breakpoints(self):
        return self.text_edit.breakpoints

    def selectedText(self):
        return self.text_edit.selectedText()

    def undo(self):
        self.text_edit.undo()

    def redo(self):
        self.text_edit.redo()

    def filepath(self, file_path=None):
        if file_path:
            self.text_edit.file = file_path
        else:
            return self.text_edit.file

    def checkModified(self):
        self.text_edit.checkModified()

    def lintText(self, run_func=None, fail_func=None):
        if run_func is None and fail_func is None:
            fail_func = lambda: self.execEnded.emit(-1, '')
        self.loading_widget.setVisible(True)
        self.run_button.setEnabled(False)
        self.text_edit.lintText(run_func, fail_func)

    def searchNext(self):
        self.text_edit.searchNext()

    def searchPrev(self):
        self.text_edit.searchPrev()

    def replaceNext(self):
        self.text_edit.replaceNext()

    def replaceAll(self):
        self.text_edit.replaceAll()

    def getSearchOptions(self):
        return self.text_edit.search_options

    def insertText(self, text):
        self.text_edit.insertText(text)

    def needToUpdateSearchIndicators(self, text_edit):
        return self.text_edit == text_edit

    def updateSearchIndicators(self):
        return self.text_edit.updateSearchIndicators()

    def requestConsoleInput(self, thread_id, line, from_pdb, label):
        self.text_edit.onPdbBreakpoint(line - self.line_correction - 1, from_pdb)
        self.console.inputRequestedSignal.emit(from_pdb, label)
        self.console.subThreadSuspendSignal.emit(thread_id)

    def updateExecutorBreakpoint(self, line, add):
        cfc
        if not cfc.is_breakpoint_line(self.text(line)) and self.runner:
            self.runner.updateBreakpoint(line + self.line_correction + 1, add)

    def runScript(self):
        if self.executing():
            return
        self.execStarting.emit()
        self.lintText(run_func=self.__runScript, fail_func=lambda: self.execEnded.emit(-1, ''))

    def __runScript(self):
        t = threading.Thread(target=self.____runScript, daemon=True)
        t.start()

    def ____runScript(self):
        error_line = -1
        error_text = ''
        global_source = 'скрипт без имени' if not os.path.isfile(self.filepath()) else 'скрипт ' + ntpath.basename(
            self.filepath())

        db_log_source = 'скрипт_без_имени' if not os.path.isfile(self.filepath()) else ntpath.basename(self.filepath())
        db_log_path = self.filepath() if os.path.isfile(self.filepath()) else None

        lineFrom, _, lineTo, lengthLineTo = self.text_edit.getSelection()

        # проверка находится ли курсор на следующей строке после выделения
        if lengthLineTo == 0:
            lineTo -= 1

        txt = self.text() if lineFrom == -1 else '\n'.join(self.text().splitlines()[lineFrom:lineTo + 1])

        self.script, self.line_correction = cfc.generate_pdb_script(
            txt,
            db_log_source,
            db_log_path
        )
        self.selection_correction = 0 if lineFrom == -1 else lineFrom
        self.line_correction -= self.selection_correction

        file_name = cfc.get_pdb_file_name(self.script)
        file = open(file_name, mode='w', encoding='utf-8')
        file.write(self.script)
        file.close()

        self.console.onExecutionStart()
        self.runner = PyDevDRunner(
            outNormalFunc=lambda char: self.console.writeNormal(char),
            outErrorFunc=lambda char: self.console.writeError(char),
            outInputFunc=lambda char: self.console.writeInput(char),
            outPdbFunc=lambda char: self.console.writePdb(char),
            requsetInputFunc=self.requestConsoleInput,
            onThreadCreateFunc=self.console.addSubThreadSignal.emit,
            onThreadKillFunc=self.console.removeSubThreadSignal.emit,
            getScriptDataFunc=lambda line: [global_source, line - self.line_correction,
                                            self.text(line - self.line_correction - 1).strip()]
        )

        # кнлопки управляющие процессом PyDevDRunner
        self.stop_button.setEnabled(True)
        self.pause_button.setEnabled(True)

        breakpoints = []
        input_breakpoints = []
        txt_lines = txt.splitlines()
        for line in range(len(txt_lines)):
            if cfc.is_breakpoint_line(txt_lines[line]) or line + self.selection_correction in self.breakpoints():
                breakpoints.append(line + self.selection_correction + self.line_correction + 1)
            if 'input(' in txt_lines[line].strip():
                input_breakpoints.append(line + self.selection_correction + self.line_correction + 1)

        traceback = self.runner.runScript(file_name, breakpoints, input_breakpoints)
        self.runner = None

        if traceback != '':
            print(traceback)
            error_line, error_text = PyDevDRunner.ParseTraceback(traceback, self.line_correction)
            GlobalLog.log(threading.get_ident(), global_source,
                          '%s (line %s)\n' % (error_text, str(error_line + 1) if error_line is not None else 'unknown'),
                          True)
            DbLog.log(db_log_source, error_text, True, db_log_path, traceback)

        os.remove(file_name)
        self.execEnded.emit(error_line, error_text)

    def __subThreadChanged(self, thread):
        if thread:
            self.stop_button.setEnabled(True)
            self.pause_button.setEnabled(not thread['waiting_input'] and not thread['waiting_pdb_input'])
            self.continue_button.setEnabled(thread['waiting_pdb_input'])
            self.next_button.setEnabled(thread['waiting_pdb_input'])
            if thread['waiting_input'] or thread['waiting_pdb_input']:
                self.text_edit.onPdbBreakpoint(thread['suspend_line'] - self.line_correction - 1,
                                               thread['waiting_pdb_input'])
            else:
                self.text_edit.onPdbContinue()

    def __inputRequested(self, from_pdb):
        self.stop_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.continue_button.setEnabled(from_pdb)
        self.next_button.setEnabled(from_pdb)

    def __inputEnded(self):
        self.stop_button.setEnabled(True)
        self.pause_button.setEnabled(True)
        self.continue_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.text_edit.onPdbContinue()

    def __executionStarted(self):
        self.run_button.setEnabled(False)
        # self.stop_button.setEnabled(True)
        # self.pause_button.setEnabled(True)
        self.continue_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def __executionEnded(self, *args):
        self.console.onInputEnded()
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        self.next_button.setEnabled(False)

    def setComment(self):
        lineFrom, _, lineTo, lengthLineTo = self.text_edit.getSelection()
        if lengthLineTo == 0:
            lineTo -= 1
        if lineFrom > -1:
            res = ""
            l = 0
            for line in range(lineFrom, lineTo + 1):
                text, l = self.comment(line)
                res += text
            self.text_edit.setSelection(lineFrom, 0, lineTo, l)
            self.text_edit.replaceSelectedText(res)
        else:
            # номер строки на которой находится курсор
            line, _ = self.text_edit.getCursorPosition()
            res, l = self.comment(line)
            self.text_edit.setSelection(line, 0, line, l)
            self.text_edit.replaceSelectedText(res)
            self.text_edit.setCursorPosition(line, 0)

    def comment(self, line):
        textLine = self.text_edit.text(line)
        if textLine[:2] != '# ':
            textLine = '# ' + textLine
            return textLine, len(textLine) - 2
        else:
            textLine = textLine[2:]
            return textLine, len(textLine) + 2

    def showEvent(self, event):
        self.splitter.real_sizes = None
        super().showEvent(event)

    def closeHandler(self):
        pass

    def saveSettings(self):
        settings = self.console.saveSettings()
        settings['sizes'] = self.splitter.real_sizes or self.splitter.sizes()
        settings['pbd_check_state'] = self.show_pdb_checkbox.checkState()
        settings['sub_threads_check_state'] = self.show_sub_threads_checkbox.checkState()
        settings['print_time_check_state'] = self.print_time_checkbox.checkState()
        return settings

    def restoreSettings(self, settings):
        self.console.restoreSettings(settings)
        self.show_pdb_checkbox.setCheckState(settings['pbd_check_state'])
        self.show_sub_threads_checkbox.setCheckState(settings['sub_threads_check_state'])
        self.print_time_checkbox.setCheckState(settings['print_time_check_state'])
        self.splitter.real_sizes = settings['sizes']
        self.splitter.setSizes(self.splitter.real_sizes)