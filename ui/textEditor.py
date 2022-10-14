import os, time, json, re, threading, sys, pdb, traceback, platform
from datetime import datetime, timedelta
from threading import Thread, Event
from pylint.reporters.json_reporter import JSONReporter
from pylint.lint import PyLinter
import jedi

from PyQt5.QtWidgets import QToolTip, QApplication, QListWidget, QListWidgetItem, QWidget, QPushButton, QBoxLayout, QLabel, QTextEdit
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer, QObject, QSize 
from PyQt5.QtGui import QFont, QColor, QImage, QFontMetrics, QIcon, QGuiApplication
if platform.system() == 'Windows':
    from PyQt5 import sip
else:
    import sip

from ui.components.qIconHoverValueButton import QIconHoverValueButton
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.commons import Commons
from ivk import cpi_framework_connections as cf

from time import sleep

class TextEditor(QsciScintilla):
    lintingEnded = pyqtSignal(list, int, object, object)
    autocompleteCalculated = pyqtSignal(int, int, object)

    LINE_NUMBER_MARGIN = 0
    FOLDING_MARGIN = 1
    BREAKPOINT_MARGIN = 2
    LINE_SELECTION_MARGIN = 3
    ERROR_WARNING_MARGIN = 4
    
    BREAKPOINT_MARKER = 0
    CURRENT_LINE_MARKER = 1
    CURRENT_LINE_BG_MARKER = 2
    DEBUG_LINE_MARKER = 3
    DEBUG_LINE_BG_MARKER = 4
    ERROR_LINE_MARKER = 5
    ERROR_LINE_BG_MARKER = 6
    ERROR_MARKER = 7
    WARNING_MARKER = 8
    ERROR_WARNING_MARKER = 9


    def __init__(self, parent, file, text, breakpoints, search_options, search_functions, modified_state_changed_func, update_executor_breakpoint_func):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.executing = False
        self.modified = False
        self.errors = []
        self.warnings = []
        self.breakpoints = breakpoints if breakpoints else set()

        self.lint_reporter = JSONReporter()
        self.lint_checker = PyLinter(reporter=self.lint_reporter)
        self.lint_checker.load_plugin_modules([
            "pylint.checkers.base", 
            "pylint.checkers.classes", 
            "pylint.checkers.exceptions", 
            "pylint.checkers.imports", 
            "pylint.checkers.python3", 
            "pylint.checkers.stdlib", 
            "pylint.checkers.strings", 
            "pylint.checkers.variables"
        ])
        self.lint_checker.disable("R")
        self.lint_checker.disable("C")
        
        self.search_options = search_options if search_options else {'text' : '', 'replace' : '', 're' : False, 'cs' : False, 'wo' : False, 'wrap' : True}
        self.needToUpdateSearchIndicators = search_functions['need_to_update']
        self.doUpdateSearchIndicators = search_functions['execute_update']
        self.need_to_update_search_indicators = True 

        self.modifiedStateChanged = modified_state_changed_func
        self.updateExecutorBreakpoint = update_executor_breakpoint_func

        self.file = file
        self.initScintilla(text)
        self.initAutoCompletion()

        self.textChanged.connect(self.__textChanged)
        self.cursorPositionChanged.connect(self.__cursorPositionChanged)
        self.autocompleteCalculated.connect(self.__autocompleteCalculated)
        self.marginClicked.connect(self.__marginClicked)
        self.linesChanged.connect(self.__linesChanged)
        self.indicatorClicked.connect(self.__indicatorClicked)
        self.SCN_DWELLSTART.connect(lambda pos, x, y: self.__dwellHandler(pos, x, y, True))
        self.SCN_DWELLEND.connect(lambda pos, x, y: self.__dwellHandler(pos, x, y, False))
        self.lintingEnded.connect(self.__lintingEnded)
       
    def initScintilla(self, text):
        #Текст
        self.setUtf8(True)
        self.setWrapMode(QsciScintilla.WrapNone)
        self.setEolVisibility(False)
        self.setEolMode(QsciScintilla.EolUnix) # только \n в конце строки
        
        #Идентация
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setIndentationGuides(True)
        self.setTabIndents(True)
        self.setBackspaceUnindents(True)
        self.setAutoIndent(True)

        

        #Маркеры (боковая панель + background строки)
        self.markerDefine(QImage("res/breakpoint.png"), TextEditor.BREAKPOINT_MARKER)
        self.markerDefine(QImage("res/error_marker.png"), TextEditor.ERROR_MARKER)
        self.markerDefine(QImage("res/warning_marker.png"), TextEditor.WARNING_MARKER)
        self.markerDefine(QImage("res/error_warning_marker.png"), TextEditor.ERROR_WARNING_MARKER)
        self.markerDefine(QImage("res/line_arrow.png"), TextEditor.CURRENT_LINE_MARKER)
        self.markerDefine(QsciScintilla.Background, TextEditor.CURRENT_LINE_BG_MARKER)
        self.setMarkerBackgroundColor(QColor('#AECDE3'), TextEditor.CURRENT_LINE_BG_MARKER)
        self.markerDefine(QImage("res/debug_arrow.png"), TextEditor.DEBUG_LINE_MARKER)
        self.markerDefine(QsciScintilla.Background, TextEditor.DEBUG_LINE_BG_MARKER)
        self.setMarkerBackgroundColor(QColor('#F8FF9F'), TextEditor.DEBUG_LINE_BG_MARKER)
        self.markerDefine(QImage("res/error_arrow.png"), TextEditor.ERROR_LINE_MARKER)
        self.markerDefine(QsciScintilla.Background, TextEditor.ERROR_LINE_BG_MARKER)
        self.setMarkerBackgroundColor(QColor('#FFB8B8'), TextEditor.ERROR_LINE_BG_MARKER)

        #Боковая панель (марджины)
        self.setMarginsFont(QFont("Consolas", 10, QFont.Normal)) 
        self.setMarginsBackgroundColor(QColor("gainsboro"))
        self.setFolding(QsciScintilla.BoxedFoldStyle, TextEditor.FOLDING_MARGIN)
        
        self.setMarginType(TextEditor.LINE_NUMBER_MARGIN, QsciScintilla.NumberMargin)
        self.setMarginSensitivity(TextEditor.LINE_NUMBER_MARGIN, True)
        self.setMarginWidth(TextEditor.LINE_NUMBER_MARGIN, str(text.count('\n') * 10 if text.count('\n') else 10))
        
        self.setMarginType(TextEditor.BREAKPOINT_MARGIN, QsciScintilla.SymbolMargin)
        self.setMarginSensitivity(TextEditor.BREAKPOINT_MARGIN, True)
        self.setMarginWidth(TextEditor.BREAKPOINT_MARGIN, 20)
        self.setMarginMarkerMask(TextEditor.BREAKPOINT_MARGIN, 1 << TextEditor.BREAKPOINT_MARKER)
        
        self.setMarginType(TextEditor.LINE_SELECTION_MARGIN, QsciScintilla.SymbolMargin)
        self.setMarginSensitivity(TextEditor.LINE_SELECTION_MARGIN, True)
        self.setMarginWidth(TextEditor.LINE_SELECTION_MARGIN, 9)
        self.setMarginMarkerMask(TextEditor.LINE_SELECTION_MARGIN, 1 << TextEditor.CURRENT_LINE_MARKER | 1 << TextEditor.DEBUG_LINE_MARKER | 1 << TextEditor.ERROR_LINE_MARKER)

        self.setMarginType(TextEditor.ERROR_WARNING_MARGIN, QsciScintilla.SymbolMargin)
        self.setMarginSensitivity(TextEditor.ERROR_WARNING_MARGIN, True)
        self.setMarginWidth(TextEditor.ERROR_WARNING_MARGIN, 5)
        self.setMarginMarkerMask(TextEditor.ERROR_WARNING_MARGIN, 1 << TextEditor.ERROR_MARKER | 1 << TextEditor.WARNING_MARKER | 1 << TextEditor.ERROR_WARNING_MARKER)
        
        #Индикаторы (выделение текста)
        self.WARNING_INDICATOR = self.indicatorDefine(QsciScintilla.SquiggleIndicator)
        self.setIndicatorForegroundColor(QColor("#e5bb00"), self.WARNING_INDICATOR)
        self.ERROR_INDICATOR = self.indicatorDefine(QsciScintilla.SquiggleIndicator)
        self.setIndicatorForegroundColor(QColor("#d80000"), self.ERROR_INDICATOR)
        self.SEARCH_INDICATOR = self.indicatorDefine(QsciScintilla.BoxIndicator)
        self.setIndicatorForegroundColor(QColor("#1ea500"), self.SEARCH_INDICATOR)

        #Выделение скобок (с кастомным индикатором)
        self.setBraceMatching(QsciScintilla.StrictBraceMatch)
        self.BRACE_INDICATOR = self.indicatorDefine(QsciScintilla.BoxIndicator)
        self.setIndicatorForegroundColor(QColor("#a230ff"), self.BRACE_INDICATOR)
        self.setMatchedBraceIndicator(self.BRACE_INDICATOR)

        self.SendScintilla(QsciScintilla.SCI_SETMOUSEDWELLTIME, 1000)
        self.setLexer(CustomPythonLexer())
        self.setText(text)

        #Добавляем брейкпоинты
        for line in self.breakpoints:
            self.markerAdd(line, TextEditor.BREAKPOINT_MARKER)
    
    def __clearLineMarkers(self):
        self.markerDeleteAll(TextEditor.CURRENT_LINE_MARKER)
        self.markerDeleteAll(TextEditor.CURRENT_LINE_BG_MARKER)
        self.markerDeleteAll(TextEditor.DEBUG_LINE_MARKER)
        self.markerDeleteAll(TextEditor.DEBUG_LINE_BG_MARKER)
        self.markerDeleteAll(TextEditor.ERROR_LINE_MARKER)
        self.markerDeleteAll(TextEditor.ERROR_LINE_BG_MARKER)
    
    def __setCurrentLineMarker(self, line):
        self.__clearLineMarkers()
        self.markerAdd(line, TextEditor.CURRENT_LINE_MARKER)
        self.markerAdd(line, TextEditor.CURRENT_LINE_BG_MARKER)

    def __setDebugLineMarker(self, line):
        self.__clearLineMarkers()
        self.markerAdd(line, TextEditor.DEBUG_LINE_MARKER)
        self.markerAdd(line, TextEditor.DEBUG_LINE_BG_MARKER)

    def __setErrorLineMarker(self, line):
        self.__clearLineMarkers()
        self.markerAdd(line, TextEditor.ERROR_LINE_MARKER)
        self.markerAdd(line, TextEditor.ERROR_LINE_BG_MARKER)

    def checkModified(self):
        self.modified = not os.path.isfile(self.file) or self.text() != open(self.file, mode='r', encoding='utf-8').read()
        self.modifiedStateChanged()
    
    def __textChanged(self, *args, **kwargs):
        if not self.executing:
            self.checkModified()
            if self.needToUpdateSearchIndicators(self) and self.need_to_update_search_indicators:
                self.doUpdateSearchIndicators()
    
    def __marginClicked(self, margin, line, modifiers):
        if self.markersAtLine(line) >> TextEditor.BREAKPOINT_MARKER & 1:          
                self.markerDelete(line, TextEditor.BREAKPOINT_MARKER)
                if line in self.breakpoints:
                    self.breakpoints.remove(line)
                    if self.executing:
                        self.updateExecutorBreakpoint(line, False)

        else:
            if self.text(line).strip() == '':
                Commons.WarningBox("Ошибка добавляения точки остановки", "Добавление точки остановки к пустой строке невозможно", self)
            elif self.text(line).strip().startswith('@'):
                Commons.WarningBox("Ошибка добавляения точки остановки", "Добавление точки остановки к декоратору невозможно", self)
            elif self.text(line).strip().startswith('def') or self.text(line).strip().startswith('class'):
                Commons.WarningBox("Ошибка добавляения точки остановки", "Добавление точки остановки к определению невозможно", self)
            elif self.text(line).strip() == 'pass':
                Commons.WarningBox("Ошибка добавляения точки остановки", "Добавление точки остановки к пустой инструкции невозможно", self)
            elif self.text(line).strip().startswith('#') or self.text(line).strip().startswith('"""') or self.text(line).strip().startswith("'''"):
                Commons.WarningBox("Ошибка добавляения точки остановки", "Добавление точки остановки к комментарию невозможно", self)
            else:
                self.markerAdd(line, TextEditor.BREAKPOINT_MARKER)
                self.breakpoints.add(line)
                if self.executing:
                    self.updateExecutorBreakpoint(line, True)


    def __linesChanged(self, *args, **kwargs):
        if not self.executing:
            #Перезапись дебаг маркеров
            self.breakpoints.clear()
            for line in range(self.lines()):
                if self.markersAtLine(line) >> TextEditor.BREAKPOINT_MARKER & 1:
                    self.breakpoints.add(line)
        #Ширина поля для номеров строк
        self.setMarginWidth(TextEditor.LINE_NUMBER_MARGIN, str(self.lines() * 10))
    
    def __indicatorClicked(self, line, index, modifiers):
        pass
    
    def __dwellHandler(self, pos, x, y, dwell_start):
        if pos != -1 and dwell_start:
            line, index = self.lineIndexFromPosition(pos)
            message = ""
            #Ошибка и предупреждения
            def func(array, result):
                for value in array:
                    if value['line'] == line and index >= value['column'] and index <= value['column_to']:
                        result.append(value['message'])
            errors = []
            warnings = []
            func(self.errors, errors)
            func(self.warnings, warnings)
            if errors or warnings: # using fact that empty iterable are False
                if errors:
                    message += '<span style="color: #a50303;">Ошибки:<br/>&nbsp;&nbsp;-%s</span>' % ('<br/>&nbsp;&nbsp;-'.join(errors))
                if warnings:
                    message += '%s<span style="color: #a59422;">Предупреждения:<br/>&nbsp;&nbsp;-%s</span>' % ('<br/>' if errors else '', '<br/>&nbsp;&nbsp;-'.join(warnings))        
            
            if message:
                pos = self.positionFromLineIndex(line, index)
                x = self.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, pos)
                y = self.SendScintilla(QsciScintilla.SCI_POINTYFROMPOSITION, 0, pos)
                point = self.mapToGlobal(QPoint(x, y))
                QToolTip.showText(point, message, self, self.rect(), 50000)
        elif not dwell_start:
            QToolTip.hideText()

    def insertText(self, text):
        line, column = self.getCursorPosition()
        self.insertAt(text, line, column)
        if text.endswith('\n'):
            self.setCursorPosition(line+1, 0)
    
    ###################################################################################################################
    ############################################### SEARCH / REPLACE ##################################################
    ###################################################################################################################

    def setSearchOption(self, key, value):
        self.search_options[key] = value
    def searchNext(self):
        self.__doSearch(True)
    def searchPrev(self):
        self.__doSearch(False)
            
    def __doSearch(self, forward):
        lineFrom, indexFrom, lineTo, indexTo = self.getSelection()
        if forward and lineTo != -1 and indexTo != -1:
            self.setCursorPosition(lineTo, indexTo)
        elif not forward and lineFrom != -1 and indexFrom != -1:
            self.setCursorPosition(lineFrom, indexFrom)
        so = self.search_options
        self.findFirst(so['text'], so['re'], so['cs'], so['wo'], so['wrap'], forward)

    def updateSearchIndicators(self, just_wipe=False):
        last_line = self.lines()-1
        last_line_len = len(self.text(last_line))
        self.clearIndicatorRange(0, 0, last_line, last_line_len, self.SEARCH_INDICATOR)
        so = self.search_options
        count = 0
        if not just_wipe and so['text']:
            search_pos = 0
            search_flags = 0          
            if so['re']:
                search_flags |= QsciScintilla.SCFIND_REGEXP
            if so['cs']:
                search_flags |= QsciScintilla.SCFIND_MATCHCASE
            if so['wo']:
                search_flags |= QsciScintilla.SCFIND_WHOLEWORD        
            while True:
                self.SendScintilla(QsciScintilla.SCI_SETTARGETSTART, search_pos)
                self.SendScintilla(QsciScintilla.SCI_SETTARGETEND, self.positionFromLineIndex(last_line, last_line_len))
                self.SendScintilla(QsciScintilla.SCI_SETSEARCHFLAGS, search_flags)
                search_pos = self.SendScintilla(QsciScintilla.SCI_SEARCHINTARGET, len(so['text']), so['text'].encode('utf-8'))
                if search_pos == -1:
                    break
                lineFrom, indexFrom = self.lineIndexFromPosition(search_pos)
                search_pos += len(so['text'])
                lineTo, indexTo = self.lineIndexFromPosition(search_pos)
                self.fillIndicatorRange(lineFrom, indexFrom, lineTo, indexTo, self.SEARCH_INDICATOR)
                count += 1
        return count

    def replaceNext(self):
        if self.selectedText() and self.search_options['replace']:
            self.replaceSelectedText(self.search_options['replace'])
        self.searchNext()

    def replaceAll(self):
        so = self.search_options
        if so['replace'] and so['text']:
            self.need_to_update_search_indicators = False 
            last_line = self.lines()-1
            last_line_len = len(self.text(last_line))
            search_pos = 0
            search_flags = 0
            if so['re']:
                search_flags |= QsciScintilla.SCFIND_REGEXP
            if so['cs']:
                search_flags |= QsciScintilla.SCFIND_MATCHCASE
            if so['wo']:
                search_flags |= QsciScintilla.SCFIND_WHOLEWORD
            while True:
                self.SendScintilla(QsciScintilla.SCI_SETTARGETSTART, search_pos)
                self.SendScintilla(QsciScintilla.SCI_SETTARGETEND, self.positionFromLineIndex(last_line, last_line_len))
                self.SendScintilla(QsciScintilla.SCI_SETSEARCHFLAGS, search_flags)
                search_pos = self.SendScintilla(QsciScintilla.SCI_SEARCHINTARGET, len(so['text']), so['text'].encode('utf-8'))
                if search_pos == -1:
                    break
                self.SendScintilla(QsciScintilla.SCI_REPLACETARGET, len(so['text']), so['replace'].encode('utf-8'))
                search_pos += len(so['replace'])
            self.doUpdateSearchIndicators()
            self.need_to_update_search_indicators = True
    
    ###################################################################################################################
    ##################################################### LINT ########################################################
    ###################################################################################################################
    def lintText(self, run_func=None, fail_func=None):
        self.setReadOnly(True)
        t = threading.Thread(target=lambda: self.__lintText(run_func, fail_func), daemon=True)
        t.start()
        sleep(1)    # рашило проблему с ошибками возникающими при анализе кода программ испытаний(много вкладок)


    def __lintText(self, run_func, fail_func):
        script, line_correction = cf.generate_pdb_script(self.text(), 'PYLINT')
        
        lint_file_name = cf.create_pylint_file(script)

        self.lint_reporter.messages.clear()
        self.lint_checker.check(lint_file_name)

        if os.path.isfile(lint_file_name):
            os.remove(lint_file_name)
            
        if not sip.isdeleted(self):
            self.lintingEnded.emit(self.lint_reporter.messages, line_correction, run_func, fail_func)

    def __lintingEnded(self, lints, line_correction, run_func, fail_func):
        #Чистим индикацию ошибок и варнингов во всем тексте
        last_line = self.lines()-1
        last_line_len = len(self.text(last_line))
        self.clearIndicatorRange(0, 0, last_line, last_line_len, self.ERROR_INDICATOR)
        self.clearIndicatorRange(0, 0, last_line, last_line_len, self.WARNING_INDICATOR)
        #Создаем новую индикацию
        self.errors = []
        self.warnings = []
        for lint in lints:
            lint['line'] -= line_correction + 1
            if lint['line'] < 0:
                continue
            line = self.text(lint['line'])
            lint['column_to'] = len(line)
            if isinstance(lint['column'], int) and lint['column'] < len(line):
                if not line.strip().startswith('import') and not line.strip().startswith('from'):
                    match = re.search(r'\S+' if line[lint['column']] == ' ' else r'\s+', line[lint['column']:])
                    if match:
                        lint['column_to'] = lint['column'] + match.start()
                self.fillIndicatorRange(lint['line'], lint['column'], lint['line'], lint['column_to'], self.ERROR_INDICATOR if lint['type'] != 'warning' else self.WARNING_INDICATOR)
            else:
                self.fillIndicatorRange(lint['line'], 0, lint['line'], len(line), self.ERROR_INDICATOR if lint['type'] != 'warning' else self.WARNING_INDICATOR)
            if lint['type'] != 'warning':
                self.errors.append(lint)
            else:
                self.warnings.append(lint)
        #Обновляем маркеры
        self.markerDeleteAll(TextEditor.ERROR_MARKER)
        self.markerDeleteAll(TextEditor.WARNING_MARKER)
        self.markerDeleteAll(TextEditor.ERROR_WARNING_MARKER)
        markered_lines = []
        for error in self.errors:
            if not error['line'] in markered_lines:
                marker_num = TextEditor.ERROR_MARKER
                for warning in self.warnings:
                    if warning['line'] == error['line']:
                        marker_num = TextEditor.ERROR_WARNING_MARKER
                        break
                self.markerAdd(error['line'], marker_num)
                markered_lines.append(error['line'])
        for warning in self.warnings:
            if not warning['line'] in markered_lines:
                self.markerAdd(warning['line'], TextEditor.WARNING_MARKER)
        #Открываем текст для редактирования или запускаем скрипт
        if run_func or fail_func:
            if self.errors:
                self.setReadOnly(False)
                if fail_func:
                    fail_func()
                if run_func:
                    Commons.WarningBox('Найдены ошибки', 'В программе найдены ошибки, выполнение невозможно', self)
            elif run_func:
                run_func()
            #Случай проверки при открытии для несохраненной вкладки без ошибок
            elif fail_func:
                self.setReadOnly(False)
                fail_func()
        else:
            self.setReadOnly(False)

    ###################################################################################################################
    ################################################# EXECUTION #######################################################
    ###################################################################################################################
    
    def beforeScriptStart(self):
        self.executing = True
        self.__clearLineMarkers()

    def afterScriptEnd(self, error_line, error_text):
        if error_line != -1:
            self.__setErrorLineMarker(error_line)
        else:
            self.__clearLineMarkers()
        if error_text:
            Commons.WarningBox('Найдены ошибки', 'В процессе выполнения произошла ошибка.<br>Сообщение: %s' % error_text, self)
        self.setReadOnly(False)
        self.executing = False

    def onPdbBreakpoint(self, line, debugging):
        self.SendScintilla(QsciScintilla.SCI_ENSUREVISIBLEENFORCEPOLICY, line)
        if debugging:
            self.__setDebugLineMarker(line)
        else:
            self.__setCurrentLineMarker(line)

    def onPdbContinue(self):
        self.__clearLineMarkers()
    
    ###################################################################################################################
    ############################################ AUTOCOMPLETE JEDI ####################################################
    ###################################################################################################################

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and event.modifiers() & Qt.ControlModifier:
            self.autocompleteActivated()
        elif event.key() == Qt.Key_Escape and self.ac_widget.isVisible():
            self.ac_widget.hide()
        elif event.key() == Qt.Key_Down and self.ac_widget.isVisible():
            if not self.ac_widget.currentItem() or self.ac_widget.currentRow() == self.ac_widget.count() - 1:
                self.ac_widget.setCurrentRow(0)
            else:
                self.ac_widget.setCurrentRow(self.ac_widget.currentRow() + 1)
        elif event.key() == Qt.Key_Up and self.ac_widget.isVisible():
            if not self.ac_widget.currentItem():
                super().keyPressEvent(event)
            elif self.ac_widget.currentRow() == 0:
                self.ac_widget.setCurrentRow(self.ac_widget.count() - 1)
            else:
                self.ac_widget.setCurrentRow(self.ac_widget.currentRow() - 1)
        elif event.key() == Qt.Key_Return and self.ac_widget.isVisible() and self.ac_widget.currentItem():
            self.doComplete()
        else:
            super().keyPressEvent(event)
    
    def focusOutEvent(self, event):
        if self.ac_widget.isVisible():
            QTimer.singleShot(100, self.__focusOutTimeout)
        super().focusOutEvent(event)
    
    def __focusOutTimeout(self):
        if self.item_info_clicked_flag:
            self.item_info_clicked_flag = False
        else:
            self.ac_widget.hide()

    def __cursorPositionChanged(self, line, column):
        if self.ac_widget.isVisible():
            if self.ac_widget.line != line:
                self.ac_widget.hide()
            else:
                self.autocompleteActivated()

    def initAutoCompletion(self):
        self.ac_widget = AutoCompleteListWidget(self.doComplete, self)
        self.current_completion_task = None
        self.item_info_clicked_flag = False
    
    def __infoBtnClicked(self, item):
        self.item_info_clicked_flag = True
        self.refreshAutocompletePosition(ensure_visible=False)
        self.ac_widget.setCurrentRow(self.ac_widget.row(item))
        self.ac_widget.showInfo(cf.get_autocomplete_jedi_doc(item.completion))

    def refreshAutocompletePosition(self, ensure_visible=True):
        if not ensure_visible or self.ac_widget.isVisible():
            pos = self.positionFromLineIndex(*self.getCursorPosition())
            x = self.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, pos) 
            y = self.SendScintilla(QsciScintilla.SCI_POINTYFROMPOSITION, 0, pos)
            self.ac_widget.move(self.mapToGlobal(QPoint(x + 2, y + 15)))

    def doComplete(self, completion=None):
        line, column = self.getCursorPosition()
        line_text = self.text(line)
        completion = completion if completion else self.ac_widget.currentItem().completion
        
        typed_len = len(completion.name) - len(completion.complete)
        column -= typed_len
        select = None

        complete = completion.name
        if completion.type == 'function' and not line_text.strip().startswith('import') and not line_text.strip().startswith('from'):
            if QGuiApplication.keyboardModifiers() & Qt.ShiftModifier:
                argumnets = cf.get_autocomplete_jedi_args(completion)
                if argumnets:
                    complete = completion.name + '(' + ', '.join(argumnets) + ')'
                    select = (column + len(completion.name) + 1, column + len(completion.name) + 1 + len(argumnets[0]))
                else:
                    complete = completion.name + '()'
            else:
                complete = completion.name

        self.SendScintilla(QsciScintilla.SCI_DELETERANGE, self.positionFromLineIndex(line, column), typed_len)
        self.insertAt(complete, line, column)
        self.setCursorPosition(line, column + len(complete))
        if select:
            self.setSelection(line, select[0], line, select[1])
        self.ac_widget.hide()
    
    def autocompleteActivated(self):
        self.setReadOnly(True)
        self.refreshAutocompletePosition() #auto ensures visible
        t = threading.Thread(target=self.__autocompleteActivated, daemon=True)
        t.start()

    def __autocompleteActivated(self):
        self.current_completion_task = threading.get_ident()
        line, column = self.getCursorPosition()
        script, line_correction = cf.generate_pdb_script(self.text(), 'JEDI_AUTOCOMPLETE')
        script = jedi.Script(script, line + line_correction + 1, column)  
        completions = script.completions()
        if self.current_completion_task != threading.get_ident():
            return
        self.autocompleteCalculated.emit(line, column, completions)

    def __autocompleteCalculated(self, line, column, completions):
        next_sym = self.text(line)[column] if column < len(self.text(line)) else ' '
        self.setReadOnly(False)

        if not next_sym.isspace():
            self.ac_widget.hide()
            return
        if not completions:
            self.ac_widget.hide()
            return
        
        w = 0
        h = 0
        fm = QFontMetrics(self.ac_widget.font())
        self.ac_widget.clear()
        item_first = None
        for completion in completions:
            item = QListWidgetItem(completion.name, self.ac_widget)
            item.completion = completion
            self.ac_widget.addItem(item)
            item_widget = QWidget(self.ac_widget)
            if item_first is None:
                item_first = item_widget
            info_btn = QIconHoverValueButton(QIcon('res/info.png'), QIcon('res/info_hover.png'), value=item, tooltip='Информация')
            info_btn.setClickedValueConsumer(self.__infoBtnClicked)
            lb = QBoxLayoutBuilder(item_widget, QBoxLayout.LeftToRight, spacing=5, margins=(2, 0, 2, 0))
            lb.stretch().add(info_btn).fix(20, 20)
            
            str_w = fm.width(completion.name) + 20
            w = str_w if str_w > w else w
            h += 20

            item.setSizeHint(QSize(str_w, 20))
            self.ac_widget.setItemWidget(item, item_widget)

        h = 200 if h > 200 else h
        self.refreshAutocompletePosition(ensure_visible=False)
        self.ac_widget.resize(w + 30, h + 5)

        # self.ac_widget.setCurrentRow(0)
        if item_first is not None:
            item_first.setFocus()
            self.item_info_clicked_flag = True
        self.ac_widget.line = line
        self.ac_widget.column = column

        self.ac_widget.show()
        self.ac_widget.raise_()
        
        
class AutoCompleteListWidget(QListWidget):
    def __init__(self, complete_func, parent):
        super().__init__(parent)
        self.setObjectName('autoCompeteWidget')
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setCursor(Qt.PointingHandCursor)
        self.setSelectionMode(QListWidget.SingleSelection)

        self.info_widget = QTextEdit(self)
        self.info_widget.setObjectName('autoCompeteInfoFrame')
        self.info_widget.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.info_widget.setReadOnly(True)
        self.info_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.info_widget.setFixedWidth(300)
        
        self.completeFunc = complete_func
        self.itemClicked.connect(lambda item: self.completeFunc(item.completion))
        self.currentItemChanged.connect(self.__itemChanged)
        self.hide()

    def hide(self):
        self.info_widget.hide()
        super().hide()
    
    def move(self, point):
        self.info_widget.move(point.x() + self.width() + 3, point.y())
        super().move(point)

    def showInfo(self, text):
        h = len(text.splitlines()) * 20
        h = 175 if h > 175 else h
        self.info_widget.setText(text)
        self.info_widget.setFixedHeight(h + 30)
        self.info_widget.show()
        self.info_widget.raise_()

    def __itemChanged(self, current, previous):
        if self.info_widget.isVisible():
            self.showInfo(cf.get_autocomplete_jedi_doc(current.completion))
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isVisible():
            self.hide()
        elif event.key() == Qt.Key_Down and self.isVisible():
            self.setCurrentRow(0 if self.currentRow() == self.count() - 1 else self.currentRow() + 1)
        elif event.key() == Qt.Key_Up and self.isVisible():
            self.setCurrentRow(self.count() - 1 if self.currentRow() == 0 else self.currentRow() - 1)
        elif event.key() == Qt.Key_Return and self.isVisible() and self.currentItem():
            self.completeFunc()
        else:
            super().keyPressEvent(event)


    
        
###################################################################################################################
############################################### PYTHON LEXER ######################################################
###################################################################################################################


class CustomPythonLexer(QsciLexerPython):
    
    def __init__(self):
        super(CustomPythonLexer, self).__init__()
        self.CUSTOM_KEYWORDS = cf.get_commands_keywords()
        
        self.setStringsOverNewlineAllowed(True)
        
        normalFont = QFont('Consolas', 10, QFont.Normal, False)
        italicFont = QFont('Consolas', 10, QFont.Normal, True)
        demiBoldFont = QFont('Consolas', 10, QFont.DemiBold, False)
        
        self.setFont(normalFont)
        self.setColor(QColor('#ad3ea6'), QsciLexerPython.Comment)
        self.setColor(QColor('#ad3ea6'), QsciLexerPython.CommentBlock)
        
        self.setFont(demiBoldFont, QsciLexerPython.Number)
        self.setColor(QColor('#A64800'), QsciLexerPython.Number)
        
        self.setFont(italicFont, QsciLexerPython.DoubleQuotedString)
        self.setColor(QColor('#007018'), QsciLexerPython.DoubleQuotedString)
        self.setFont(italicFont, QsciLexerPython.SingleQuotedString)
        self.setColor(QColor('#007018'), QsciLexerPython.SingleQuotedString)
        
        self.setColor(QColor('#c66d00'), QsciLexerPython.TripleSingleQuotedString)
        self.setColor(QColor('#c66d00'), QsciLexerPython.TripleDoubleQuotedString)
        
        self.setFont(demiBoldFont, QsciLexerPython.Keyword)
        
        self.setFont(demiBoldFont, QsciLexerPython.ClassName)
        self.setColor(QColor('#009792'), QsciLexerPython.ClassName)
        
        self.setFont(demiBoldFont, QsciLexerPython.FunctionMethodName)
        self.setColor(QColor('#7F00B1'), QsciLexerPython.FunctionMethodName)
        
        self.setColor(QColor('#202020'), QsciLexerPython.Identifier)
        
        self.setFont(italicFont, QsciLexerPython.Decorator)
        self.setColor(QColor('#837A00'), QsciLexerPython.Decorator)
        
        self.setFont(demiBoldFont, QsciLexerPython.HighlightedIdentifier)
        
    
    def keywords(self, index):
        keywords = QsciLexerPython.keywords(self, index) or ''
        if index == 1:
            return 'self False True breakpoint ' + keywords
        elif index == 2:
            return self.CUSTOM_KEYWORDS + ' ' + keywords
        return keywords
            