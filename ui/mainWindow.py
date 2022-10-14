import sys, os, datetime, platform, subprocess, getpass

from PyQt5.QtWidgets import QMainWindow, QFrame, QWidget, QDockWidget, QShortcut, QAction, QBoxLayout, QPushButton, QTabWidget, QTabBar
from PyQt5.QtCore import Qt, QCoreApplication, QSettings, QRect, QSize, QByteArray, QPoint, QEvent
from PyQt5.QtGui import QIcon

from ui.tabsWidget import TabsWidget
from ui.commandsWidget import CommandsWidget
from ui.consoleWidget import ConsoleWidget

from ui.components.commons import Revertable
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder

from ivk.global_log import GlobalLog
from ivk.log_db import DbLogWidget
from ivk import config

class MainWindow(QMainWindow):
    EXIT_CODE_NORMAL = 0
    EXIT_CODE_REBOOT = 12345
    def setRebootExitCode(self):
        self.EXIT_CODE = MainWindow.EXIT_CODE_REBOOT

    def __init__(self):
        super(MainWindow, self).__init__()
        QCoreApplication.setApplicationName('IVK-NG Next')
        QCoreApplication.setOrganizationName('VNIIEM')
        QCoreApplication.setOrganizationDomain('mcc.vniiem.ru')
        
        self.EXIT_CODE = MainWindow.EXIT_CODE_NORMAL
        
        self.initUI()
        self.initGlobalLogAndExchangeDocks()

        config.get_exchange().init()

        self.initCommandsDocks()
        self.initMenu()
        self.restoreSettings()
        

    def initUI(self):
        self.setWindowTitle("IVK-NG Next [%s]" % getpass.getuser())
        self.setDockOptions(QMainWindow.AnimatedDocks)
        self.statusBar().show()
        
        self.save_dir = os.path.expanduser('~')
        self.open_dir = os.path.expanduser('~')

        self.setCentralWidget(QWidget(self))
        self.tabs_widget = TabsWidget(self.centralWidget(), self)
        self.tabs_frames = []
        self.frames_stack = [self]
        
        lb = QBoxLayoutBuilder(self.centralWidget(), QBoxLayout.TopToBottom, margins=(0, 0, 0, 0), spacing=5)
        lb.add(self.tabs_widget)
    
    def initMenu(self):
        #FILE MENU
        file_actions = MainWindow.createBasicActions(self,
            lambda: self.tabs_widget.newTab(), 
            lambda: self.tabs_widget.openTab(),
            lambda: self.tabs_widget.saveTab(),
            lambda: self.tabs_widget.saveTabAs(),
            lambda: self.tabs_widget.searchActionActivated(),
            lambda: self.tabs_widget.currentWidget().undo(),
            lambda: self.tabs_widget.currentWidget().redo(),
            lambda: config.openWidget(self),
            lambda: DbLogWidget.OpenWidget(self),
            self.close
        )
        file_menu = self.menuBar().addMenu('Файл')
        file_menu.addActions(file_actions)
        
        #WIDGETS MENU
        commands_console_widget_action = QAction(QIcon('res/console.png'), 'Окно вывода команд', self)
        commands_console_widget_action.setStatusTip('Открыть окно вывода команд')
        commands_console_widget_action.triggered.connect(lambda: self.openDock(self.commands_console_dock_widget, Qt.LeftDockWidgetArea))

        total_console_widget_action = QAction(QIcon('res/console.png'), 'Глобальный лог', self)
        total_console_widget_action.setStatusTip('Открыть глобальный лог')
        total_console_widget_action.triggered.connect(lambda: self.openDock(self.total_console_dock_widget, Qt.BottomDockWidgetArea))

        commands_widget_action = QAction(QIcon('res/commands.png'), 'Окно команд', self)
        commands_widget_action.setStatusTip('Открыть окно команд')
        commands_widget_action.triggered.connect(lambda: self.openDock(self.commands_dock_widget, Qt.LeftDockWidgetArea))
        
        widgets_menu = self.menuBar().addMenu('Панели')
        widgets_menu.addActions([total_console_widget_action, commands_console_widget_action, commands_widget_action])

        #Сторонние доки в зависимости от конфигурации
        for dock in self.exchange_docks:
            params = dock.getMenuParams()
            action = QAction(QIcon(params['icon']), params['text'], self)
            action.setStatusTip(params['status_tip'])
            action.triggered.connect(lambda qt_checked, dock=dock: self.openDock(dock, Qt.RightDockWidgetArea)) #нормальное запоминания контекста в lambda
            widgets_menu.addAction(action)
        


    
    @staticmethod
    def createBasicActions(parent, add_new_action_func, open_action_func, save_action_func, save_as_action_func, search_action_func, undo_action_func, redo_action_func, settings_action_func, log_db_action_func, exit_action_func):
        add_new_action = QAction(QIcon('res/new_tab.png'), 'Новая вкладка', parent)
        add_new_action.setShortcut('Ctrl+N')
        add_new_action.setStatusTip('Создать новую вкладку')
        add_new_action.triggered.connect(add_new_action_func)

        open_action = QAction(QIcon('res/open.png'), 'Открыть', parent)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Открыть программу испытаний')
        open_action.triggered.connect(open_action_func)
        
        save_action = QAction(QIcon('res/save.png'), 'Сохранить', parent)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Сохранить программу испытаний')
        save_action.triggered.connect(save_action_func)
        
        save_as_action = QAction(QIcon('res/save_as.png'), 'Сохранить как...', parent)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.setStatusTip('Сохранить программу испытаний как...')
        save_as_action.triggered.connect(save_as_action_func)

        search_action = QAction(QIcon('res/search.png'), 'Поиск', parent)
        search_action.setShortcut('Ctrl+F')
        search_action.setStatusTip('Найти в тексте')
        search_action.triggered.connect(search_action_func)

        undo_action = QAction(QIcon('res/undo.png'), 'Отменить', parent)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.setStatusTip('Отменить последнее изменение текста')
        undo_action.triggered.connect(undo_action_func)

        redo_action = QAction(QIcon('res/redo.png'), 'Вернуть', parent)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.setStatusTip('Вернуть отмененное изменение текста')
        redo_action.triggered.connect(redo_action_func)

        settings_action = QAction(QIcon('res/settings.png'), 'Настройки', parent)
        settings_action.setShortcut('Ctrl+I')
        settings_action.setStatusTip('Открыть окно настроек')
        settings_action.triggered.connect(settings_action_func)

        db_log_action = QAction(QIcon('res/log.png'), 'Выгрузка лога', parent)
        db_log_action.setShortcut('Ctrl+L')
        db_log_action.setStatusTip('Открыть окно базы данных лога')
        db_log_action.triggered.connect(log_db_action_func)

        exit_action = QAction(QIcon('res/exit.png'), 'Выход', parent)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Выйти из программы')
        exit_action.triggered.connect(exit_action_func)

        return [add_new_action, open_action, save_action, save_as_action, search_action, undo_action, redo_action, settings_action, db_log_action, exit_action]

    ###################################################################################################################
    ############################################### DOCK WIDGETS ######################################################
    ###################################################################################################################
    def initGlobalLogAndExchangeDocks(self):
        self.total_console_dock_widget = ConsoleWidget(self, 'Глобальный лог', 'TotalConsoleWidget')
        GlobalLog.init(self.total_console_dock_widget.widget())
        self.available_docks = [self.total_console_dock_widget]
        #Сторонние доки в зависимости от конфигурации
        self.exchange_docks = config.get_exchange().initDocks(self, self.tabs_widget)
        self.available_docks.extend(self.exchange_docks)

    def initCommandsDocks(self):
        self.commands_console_dock_widget = ConsoleWidget(self, 'Вывод команд', 'CommandsConsoleWidget')
        self.commands_dock_widget = CommandsWidget(self, self.commands_console_dock_widget.widget(), self.tabs_widget)
        self.available_docks.insert(1, self.commands_dock_widget)
        self.available_docks.insert(2, self.commands_console_dock_widget)
        
    def openDock(self, dock, area):
        if dock.isVisible():
            return
        if hasattr(dock, 'open_settings'):
            if dock.open_settings['floating']:
                dock.setFloating(True)
                dock.setGeometry(QRect(dock.open_settings['pos'], dock.open_settings['size']))
            else:
                dock.resize(dock.open_settings['size'])
                self.addDockWidget(dock.open_settings['area'], dock)
            if 'settings' in dock.open_settings and dock.open_settings['settings']:
                dock.restoreSettings(dock.open_settings['settings'])
                dock.open_settings['settings'] = None
        elif area:
            self.addDockWidget(area, dock)
        dock.show()

    def onDockClose(self, dock):
        if not hasattr(dock, 'open_settings'):
            dock.open_settings = {}
        dock.open_settings['area'] = self.dockWidgetArea(dock)
        dock.open_settings['floating'] = dock.isFloating()
        dock.open_settings['size'] = dock.size()
        dock.open_settings['pos'] = dock.mapToGlobal(QPoint(0, 0)) if dock.isFloating() else dock.pos()

    def getDockBySettingsKeyword(self, keyword):
        for dock in self.available_docks:
            if dock.settingsKeyword() == keyword:
                return dock
        return None

    def tabDragDrop(self, tab, from_tabs_widget, from_window, pos):
        is_main_tabs_widget = from_tabs_widget == self.tabs_widget
        from_tabs_widget.tabDraggedOut(tab, is_main_tabs_widget)
        
        if not is_main_tabs_widget and from_tabs_widget.count() == 0:
            frame = None
            for f in self.tabs_frames:
                if f.tabs_widget == from_tabs_widget:
                    frame = f
                    break
            frame.save_tabs_on_close = False
            frame.close()
            self.tabs_frames.remove(frame)
            self.frames_stack.remove(frame)

        frame = None
        for f in self.frames_stack:
            if QRect(f.pos(), f.size()).contains(pos) and f.isVisible():
                frame = f #no break cause looking for top level frame
        if not frame:
            frame = IvkTabsFrame(self, self.tabs_widget.search_widget)
            frame.resize(from_window.size())
            frame.move(pos.x()-35, pos.y()-44)
            frame.show()
            self.tabs_frames.append(frame)
            self.frames_stack.append(frame)
        
        frame.tabs_widget.tabDraggedIn(tab)
        frame.activateWindow()



    def saveSettings(self):
        s = QSettings('settings.ini', QSettings.IniFormat)
        
        s.setValue("size", self.size_.val)
        s.setValue("pos", self.pos_.val)
        s.setValue('maximized', self.isMaximized())
        s.setValue('save_dir', self.save_dir)
        s.setValue('open_dir', self.open_dir)
 
        #TABS
        s.setValue('tabs_widget/tab_index', self.tabs_widget.currentIndex())
        s.beginWriteArray('tabs_widget/tabs')
        for i in range(self.tabs_widget.count()):
            s.setArrayIndex(i)
            s.setValue('file', self.tabs_widget.widget(i).filepath())
            s.setValue('text', self.tabs_widget.widget(i).text())
            s.setValue('breakpoints', self.tabs_widget.widget(i).breakpoints())
            s.setValue('search_options', self.tabs_widget.widget(i).getSearchOptions())
            s.setValue('ui_settings', self.tabs_widget.widget(i).saveSettings())
        s.endArray()

        #FLOATING TABS
        s.beginWriteArray('tabs_frames')
        for i, frame in enumerate(self.tabs_frames):
            s.setArrayIndex(i)
            s.setValue("size", frame.size_.val)
            s.setValue("pos", frame.pos_.val)
            s.setValue('maximized', frame.isMaximized())
            s.setValue('tab_index', frame.tabs_widget.currentIndex())
            s.beginWriteArray('tabs')
            for j in range(frame.tabs_widget.count()):
                s.setArrayIndex(j)
                s.setValue('file', frame.tabs_widget.widget(j).filepath())
                s.setValue('text', frame.tabs_widget.widget(j).text())
                s.setValue('breakpoints', frame.tabs_widget.widget(j).breakpoints())
                s.setValue('search_options', frame.tabs_widget.widget(j).getSearchOptions())
                s.setValue('ui_settings', frame.tabs_widget.widget(j).saveSettings())
            s.endArray()
        s.endArray()

        #DOCKS
        s.beginWriteArray('docks')
        index = 0
        for dock in self.available_docks:
            if not dock.isVisible() and not hasattr(dock, 'open_settings'):
                continue
            s.setArrayIndex(index)
            index += 1
            s.setValue('visible', dock.isVisible())
            s.setValue('area', self.dockWidgetArea(dock) if dock.isVisible() else dock.open_settings['area'])
            s.setValue('floating', dock.isFloating() if dock.isVisible() else dock.open_settings['floating'])
            s.setValue('size', dock.size() if dock.isVisible() else dock.open_settings['size'])
            s.setValue('pos', dock.mapToGlobal(QPoint(0, 0)) if dock.isFloating() else dock.pos() if dock.isVisible() else dock.open_settings['pos'])
            s.setValue('keyword', dock.settingsKeyword())
            if hasattr(dock, 'saveSettings'):
                s.setValue('settings', dock.saveSettings())
            
        s.endArray()


    def restoreSettings(self): 
        s = QSettings('settings.ini', QSettings.IniFormat)
        self.restore_started = datetime.datetime.now()
        
        self.size_ = Revertable(s.value('size') if s.value('size') is not None else QSize(600, 500))   
        self.resize(self.size_.val) 
        
        self.pos_ = Revertable(s.value('pos') if s.value('pos') is not None else QPoint(100, 100))    
        self.move(self.pos_.val)

        if s.value('maximized') is not None and s.value('maximized', type=bool): #only after size_ and pos_ are set
            self.showMaximized()

        if s.value('open_dir') is not None:
            self.open_dir = s.value('open_dir', type=str)
        if s.value('save_dir') is not None:
            self.save_dir = s.value('save_dir', type=str)

        #TABS
        n = s.beginReadArray('tabs_widget/tabs')
        for i in range(n):
            s.setArrayIndex(i)
            tab = self.tabs_widget.newTab(s.value('file', type=str), s.value('text', type=str), s.value('breakpoints', type=set), s.value('search_options', type=dict))
            tab.restoreSettings(s.value('ui_settings', type=dict))
        s.endArray()
        
        if s.value('tabs_widget/tab_index') is not None:
            self.tabs_widget.setCurrentIndex(s.value('tabs_widget/tab_index', type=int))
        
        if self.tabs_widget.count() < 1:
            self.tabs_widget.newTab()

        #FLOATING TABS
        n = s.beginReadArray('tabs_frames')
        for i in range(n):
            s.setArrayIndex(i)
            frame = IvkTabsFrame(self, self.tabs_widget.search_widget)
            frame.restore_started = datetime.datetime.now()
        
            frame.size_ = Revertable(s.value('size') if s.value('size') is not None else QSize(600, 500))   
            frame.resize(frame.size_.val) 
        
            frame.pos_ = Revertable(s.value('pos') if s.value('pos') is not None else QPoint(100, 100))    
            frame.move(frame.pos_.val)

            if s.value('maximized') is not None and s.value('maximized', type=bool): #only after size_ and pos_ are set
                frame.showMaximized()
            else:
                frame.show()
            
            self.tabs_frames.append(frame)
            self.frames_stack.append(frame)

            m = s.beginReadArray('tabs')
            for j in range(m):
                s.setArrayIndex(j)
                tab = frame.tabs_widget.newTab(s.value('file', type=str), s.value('text', type=str), s.value('breakpoints', type=set), s.value('search_options', type=dict))
                tab.restoreSettings(s.value('ui_settings', type=dict))
            s.endArray()

            if s.value('tab_index') is not None:
                frame.tabs_widget.setCurrentIndex(s.value('tab_index', type=int))
        s.endArray()


        #DOCKS
        left = []
        right = []
        top = []
        bottom = []

        total_docks = []
        horizontal_sizes = []
        vertical_sizes = []

        dock_settings = []

        n = s.beginReadArray('docks')
        for i in range(n):
            s.setArrayIndex(i)
            dock = self.getDockBySettingsKeyword(s.value('keyword', type=str))
            if s.value('visible', type=bool):
                if s.value('floating', type=bool):
                    dock.setFloating(True)
                    dock.setGeometry(QRect(s.value('pos', type=QPoint), s.value('size', type=QSize)))
                    self.openDock(dock, None)
                else:
                    total_docks.append(dock)
                    horizontal_sizes.append(s.value('size', type=QSize).width())
                    vertical_sizes.append(s.value('size', type=QSize).height())
                    dock.move(s.value('pos', type=QPoint))
                    if s.value('area', type=Qt.DockWidgetArea) == Qt.LeftDockWidgetArea:
                        left.append(dock)
                    elif s.value('area', type=Qt.DockWidgetArea) == Qt.RightDockWidgetArea:
                        right.append(dock)
                    elif s.value('area', type=Qt.DockWidgetArea) == Qt.TopDockWidgetArea:
                        top.append(dock)
                    else:
                        bottom.append(dock)
                if s.contains('settings'):
                    dock_settings.append({'dock' : dock, 'settings' : s.value('settings', type=dict)})
            dock.open_settings = {         
                'area' : s.value('area', type=Qt.DockWidgetArea),
                'floating' : s.value('floating', type=bool),
                'size' : s.value('size', type=QSize),
                'pos' : s.value('pos', type=QPoint)    
            }
            if s.contains('settings'):
                dock.open_settings['settings'] = s.value('settings', type=dict)
                if not s.value('visible', type=bool):
                    dock.restoreSettings(dock.open_settings['settings']) #for case when we don't open that dock before closing app
                
        s.endArray()
        
        left.sort(key=lambda e: e.pos().y())
        right.sort(key=lambda e: e.pos().y())
        top.sort(key=lambda e: e.pos().x())
        bottom.sort(key=lambda e: e.pos().x())

        for dock in left:
            self.openDock(dock, Qt.LeftDockWidgetArea)
        for dock in right:
            self.openDock(dock, Qt.RightDockWidgetArea)
        for dock in top:
            self.openDock(dock, Qt.TopDockWidgetArea)
        for dock in bottom:
            self.openDock(dock, Qt.BottomDockWidgetArea)

        if total_docks:
            self.resizeDocks(total_docks, horizontal_sizes, Qt.Horizontal)
            self.resizeDocks(total_docks, vertical_sizes, Qt.Vertical)
        for entry in dock_settings:
            entry['dock'].restoreSettings(entry['settings'])

    def onFrameActivated(self, frame):
        if frame != self:
            self.tabs_widget.frameDeactivated()
        for f in self.tabs_frames:
            if f != frame:
                f.tabs_widget.frameDeactivated()
        #move on top of stack
        self.frames_stack.remove(frame)
        self.frames_stack.append(frame)
            
    def event(self, event):    
        if event.type() == QEvent.Resize:
            if (datetime.datetime.now() - self.restore_started).seconds > 1:
                self.size_.val = self.size()
            self.tabs_widget.refrershSearchPosition()
            self.tabs_widget.refreshAutocompletePosition()
        elif event.type() == QEvent.Move:
            if (datetime.datetime.now() - self.restore_started).seconds > 1:
                self.pos_.val = self.pos()
            self.tabs_widget.refrershSearchPosition()
            self.tabs_widget.refreshAutocompletePosition()
        elif event.type() == QEvent.WindowStateChange and self.isMaximized():
            self.size_.revert()
            self.pos_.revert()
        elif event.type() == QEvent.WindowActivate:
            self.tabs_widget.frameActivated()
            self.onFrameActivated(self)

        return super().event(event)
        
    def closeEvent(self, event):
        GlobalLog.onClose()
        config.get_exchange().onClose()
        self.saveSettings()
        for frame in self.tabs_frames:
            frame.save_tabs_on_close = False
            frame.close()

        super().closeEvent(event)

class IvkTabsFrame(QFrame):
    def __init__(self, main_window, search_widget):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.save_tabs_on_close = True
        self.main_window = main_window
        self.tabs_widget = TabsWidget(self, main_window, search_widget)
        
        file_actions = MainWindow.createBasicActions(self,
            lambda: self.tabs_widget.newTab(), 
            lambda: self.tabs_widget.openTab(),
            lambda: self.tabs_widget.saveTab(),
            lambda: self.tabs_widget.saveTabAs(),
            lambda: self.tabs_widget.searchActionActivated(),
            lambda: self.tabs_widget.currentWidget().undo(),
            lambda: self.tabs_widget.currentWidget().redo(),
            lambda: config.openWidget(main_window),
            lambda: DbLogWidget.OpenWidget(self),
            self.close
        )
        self.addActions(file_actions)

        self.restore_started = None
        self.size_ = Revertable(QSize(600, 500))   
        self.pos_ = Revertable(QPoint(100, 100))

        lb = QBoxLayoutBuilder(self, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        lb.add(self.tabs_widget)

    def closeEvent(self, event):
        if self.save_tabs_on_close:
            while self.tabs_widget.count() > 0:
                if not self.tabs_widget.closeTab(self.tabs_widget.count()-1, False, False, False):
                    event.ignore()
                    return
        super().closeEvent(event)
    
    def event(self, event):
        if event.type() == QEvent.Resize:
            if not self.restore_started or (datetime.datetime.now() - self.restore_started).seconds > 1:
                self.size_.val = self.size()
            self.tabs_widget.refrershSearchPosition()
            self.tabs_widget.refreshAutocompletePosition()
        elif event.type() == QEvent.Move:
            if not self.restore_started or (datetime.datetime.now() - self.restore_started).seconds > 1:
                self.pos_.val = self.pos()
            self.tabs_widget.refrershSearchPosition()
            self.tabs_widget.refreshAutocompletePosition()
        elif event.type() == QEvent.WindowStateChange and self.isMaximized():
            self.size_.revert()
            self.pos_.revert()
        elif event.type() == QEvent.WindowActivate:
            self.tabs_widget.frameActivated()
            self.main_window.onFrameActivated(self)
        return super().event(event)
