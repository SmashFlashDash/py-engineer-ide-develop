import os, ntpath, platform

from PyQt5.QtWidgets import QFrame, QLabel, QTabWidget, QPushButton, QFileDialog, QAbstractButton, QBoxLayout, QTabBar
from PyQt5.QtGui import QIcon, QFontMetrics
from PyQt5.QtCore import Qt, QEvent, QRect
if platform.system() == 'Windows':
    from PyQt5 import sip
else:
    import sip

from ui.components.commons import Commons, BoxResult
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.searchWidget import SearchWidget
from ui.tabWidget import TabWidget

class TabsWidget(QTabWidget):
    
    def __init__(self, parent, main_window, search_widget=None):
        super().__init__(parent)
        self.main_window = main_window
        
        add_tab_button = QPushButton(QIcon('res/plus.png'), '')
        add_tab_button.setObjectName('addTabButton')
        add_tab_button.setToolTip('Новая вкладка')
        add_tab_button.clicked.connect(self.newTab)
        self.setCornerWidget(add_tab_button)

        self.search_widget = search_widget or SearchWidget( 
                                                        lambda: self.currentWidget().searchNext(), 
                                                        lambda: self.currentWidget().searchPrev(),
                                                        lambda: self.currentWidget().replaceNext(),
                                                        lambda: self.currentWidget().replaceAll(),
                                                        lambda: self.currentWidget().getSearchOptions(), 
                                                        self.onSearchOptionChange, 
                                                        self.onSearchTextChange,
                                                        self.onSearchWidgetClose)
        
       
        self.setTabBar(IvkTabBar(self, self.main_window))
        self.tabBar().tabMoved.connect(self.__tabMoved)

        self.setMovable(True)
        self.setTabsClosable(True) 
        self.currentChanged.connect(self.__currentChanged)
        self.tabCloseRequested.connect(self.closeTab)
    


    def newTab(self, file='', text='', breakpoints=None, search_options=None):
        w = TabWidget(self, file, text, breakpoints, search_options, self.needToUpdateSearchIndicators, self.updateSearchIndicators)
        w.index = self.addTab(w, '')
        w.modifiedStateChanged.connect(self.__updateTabTitle)
        w.checkModified()
        
        self.tabBar().setTabButton(w.index, QTabBar.LeftSide, w.loading_widget)
        if text:
            w.lintText()
        else:
            w.loading_widget.setVisible(False)
        
        for x in self.findChildren(QAbstractButton):
            if 'Close' in x.toolTip():
                x.setToolTip('Закрыть')
        
        self.setCurrentIndex(w.index)
        return w

    def __updateTabTitle(self, index):
        w = self.widget(index)
        if not os.path.isfile(w.filepath()):
            self.setTabText(index, 'без имени*' if w.text() != '' else 'без имени')
            self.setTabToolTip(index, None)
        else:
            name = ntpath.basename(w.filepath())
            if len(name) > 15:
                name = name[:16] + '...'
            if w.modified():
                name += '*'
            self.setTabText(index, name)
            self.setTabToolTip(index, w.filepath())
    
    def closeTab(self, index, create_tab_if_empty=True, check_modified_on_save=True, lint_text_on_save=True):
        w = self.widget(index)
        if w.executing():
            return False

        save_tab = False
        if w.modified() and w.text() != '':
            name = ntpath.basename(w.filepath()) if os.path.isfile(w.filepath()) else 'без имени'
            box_result = Commons.YesNoCancelBox('Файл не сохранен', 'Закрываемый файл "%s" был изменен. Сохранить изменения?' % name, self)
            if box_result == BoxResult.CANCEL:
                return False
            save_tab = box_result == BoxResult.YES
        
        w.modifiedStateChanged.disconnect() 
        if save_tab and not self.saveTab(w, check_modified_on_save, lint_text_on_save):
            w.modifiedStateChanged.connect(self.__updateTabTitle)
            return False

        self.removeTab(index)
        w.closeHandler()
        sip.delete(w)

        if self.count() > 0:
            for i in range(index, self.count()):
                self.widget(i).index = i
        elif create_tab_if_empty:
            self.newTab()     
        return True

    def openTab(self):
        filename = QFileDialog.getOpenFileName(self, 'Открыть файл', self.main_window.open_dir, 'Файлы программ испытаний (*.ivkng)')[0]  # @UndefinedVariable
        if filename != '':
            self.newTab(filename, open(filename, mode='r', encoding='utf-8').read())
            self.main_window.open_dir = os.path.dirname(filename)

    def saveTab(self, w=None, check_modified=True, lint_text=True):
        if w is None:
            w = self.currentWidget()
        if os.path.isfile(w.filepath()):
            f = open(w.filepath(), mode='w', encoding='utf-8')
            f.write(w.text())
            f.close()
            if check_modified:
                w.checkModified()
            if lint_text:
                w.lintText()
            return True
        else:
            return self.saveTabAs(w)

    def saveTabAs(self, w=None, check_modified=True, lint_text=True):
        if w is None:
            w = self.currentWidget()
        filename = QFileDialog.getSaveFileName(self, 'Сохранить файл', self.main_window.save_dir, 'Файлы программ испытаний (*.ivkng)')[0]  # @UndefinedVariable
        if filename != '':
            if not filename.endswith('.ivkng'):
                filename += '.ivkng'
            f = open(filename, mode='w', encoding='utf-8')
            f.write(w.text())
            f.close()
            self.main_window.save_dir = os.path.dirname(filename)
            w.filepath(filename)
            if check_modified:
                w.checkModified()
            if lint_text:
                w.lintText()
            return True
        else:
            return False
    
    def insertTextToCurrentTab(self, text):
        self.currentWidget().insertText(text)

    def mouseDoubleClickEvent(self, event):
        self.newTab()
    
    def __currentChanged(self, index):
        self.search_widget.loadSearchOptions()
        if self.search_widget.isVisible():
            self.updateSearchIndicators()
    
    def __tabMoved(self, from_index, to_index):
        self.widget(from_index).index = from_index
        self.widget(to_index).index = to_index
    
    ###################################################################################################################
    ################################################# DRAG TAB OUT ####################################################
    ###################################################################################################################

    def tabDraggedOut(self, w, create_tab_if_empty):
        w.modifiedStateChanged.disconnect() 
        self.removeTab(w.index)
        if self.count() > 0:
            for i in range(w.index, self.count()):
                self.widget(i).index = i
        elif create_tab_if_empty:
            self.newTab()
    
    def tabDraggedIn(self, w):
        w.index = self.addTab(w, '')
        w.modifiedStateChanged.connect(self.__updateTabTitle)
        w.checkModified()
        for x in self.findChildren(QAbstractButton):
            if 'Close' in x.toolTip():
                x.setToolTip('Закрыть')
        self.setCurrentIndex(w.index)
        w.text_edit.needToUpdateSearchIndicators = self.needToUpdateSearchIndicators
        w.text_edit.doUpdateSearchIndicators = self.updateSearchIndicators
        self.refrershSearchPosition()

    def frameActivated(self):
        self.search_widget.loadFunctions(
                    lambda: self.currentWidget().searchNext() if self.currentWidget() else None, 
                    lambda: self.currentWidget().searchPrev() if self.currentWidget() else None,
                    lambda: self.currentWidget().replaceNext() if self.currentWidget() else None,
                    lambda: self.currentWidget().replaceAll() if self.currentWidget() else None,
                    lambda: self.currentWidget().getSearchOptions() if self.currentWidget() else None, 
                    self.onSearchOptionChange, 
                    self.onSearchTextChange,
                    self.onSearchWidgetClose)
        self.refrershSearchPosition()
        self.__currentChanged(self.currentIndex())
    
    def frameDeactivated(self):
        if self.search_widget.isVisible():
            self.onSearchWidgetClose()

    def refreshAutocompletePosition(self):
        if self.currentWidget():
            self.currentWidget().text_edit.refreshAutocompletePosition()
   
    ###################################################################################################################
    ############################################### SEARCH / REPLACE ##################################################
    ###################################################################################################################


    def needToUpdateSearchIndicators(self, text_edit):
        if self.currentWidget():
            return self.currentWidget().needToUpdateSearchIndicators(text_edit) and self.search_widget.isVisible() and not self.search_widget.refreshing
        
    def updateSearchIndicators(self):
        if self.currentWidget():
            count = self.currentWidget().updateSearchIndicators()
            self.search_widget.onSearchIndicatorsUpdate(count)

    def onSearchWidgetClose(self):
        for index in range(self.count()):
            self.widget(index).text_edit.updateSearchIndicators(just_wipe=True)
    
    def onSearchOptionChange(self, key, value):
        if key in ('re', 'cs', 'wo') and self.search_widget.isVisible():
            self.updateSearchIndicators()
    
    def onSearchTextChange(self):
        if self.search_widget.isVisible():
            self.updateSearchIndicators()

    def refrershSearchPosition(self):
        self.search_widget.refreshPosition(self, -8, self.tabBar().height() + 5)

    def searchActionActivated(self):
        self.search_widget.open()
        self.refrershSearchPosition()
        selected_text = self.currentWidget().selectedText()
        if selected_text:
            self.search_widget.setSearchText(selected_text) #Апдейт индикаторов пойдет из __searchTextChanged
        else:
            self.updateSearchIndicators()

class IvkTabBar(QTabBar):
    def __init__(self, tabs_widget, main_window):
        super().__init__(tabs_widget)
        self.setDrawBase(False)
        
        self.tabs_widget = tabs_widget
        self.main_window = main_window
        self.drag_tab = None
        
        self.drag_frame = QFrame()
        self.drag_frame.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.grag_frame_label = QLabel('')
        lb = QBoxLayoutBuilder(self.drag_frame, QBoxLayout.LeftToRight, margins=(2, 2, 2, 2), spacing=2, object_name='dragTabFrame')
        lb.stretch().add(self.grag_frame_label).stretch()
        self.drag_frame.hide()

    def mouseDoubleClickEvent(self, event):
        self.drag_tab = self.tabs_widget.currentWidget()
        pos = event.globalPos()
        fm = QFontMetrics(self.font())
        text = self.tabText(self.drag_tab.index)
        self.grag_frame_label.setText(text)
        self.drag_frame.setFixedSize(fm.width(text) + 20, 25)
        self.drag_frame.move(pos.x() - self.drag_frame.width()*0.5 - 10, pos.y() - 20)
        self.drag_frame.show()

    def mouseMoveEvent(self, event):
        if self.drag_tab:
            pos = event.globalPos()
            self.drag_frame.move(pos.x() - self.drag_frame.width()*0.5 - 5, pos.y() - 20)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.drag_tab:
            self.drag_frame.hide()
            my_window = self.tabs_widget.parent() if self.main_window.tabs_widget != self.tabs_widget else self.main_window
            if QRect(my_window.pos(), my_window.size()).contains(event.globalPos()):
                self.drag_tab = None
            else:
                self.main_window.tabDragDrop(self.drag_tab, self.tabs_widget, my_window, event.globalPos())
                self.drag_tab = None
        else:
            super().mouseReleaseEvent(event)
