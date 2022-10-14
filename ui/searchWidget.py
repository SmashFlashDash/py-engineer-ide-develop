from PyQt5.QtWidgets import QLabel, QStyle, QTabWidget, QPushButton, QLineEdit, QMessageBox, QFileDialog, QAbstractButton, QVBoxLayout, QHBoxLayout, QBoxLayout, QFrame
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QEvent, QSize, QPoint, QObject, pyqtSignal 

from ui.components.commons import Commons, BoxResult
from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.qButtonLineEdit import QButtonLineEdit

class SearchWidget(QFrame):
    def __init__(self, search_next_func, search_prev_func, replace_next_func, replace_all_func, get_options_func, on_options_change_func, on_serach_text_change_func, on_close_func):
        super().__init__()
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.refreshing = False
        self.loadFunctions(search_next_func, search_prev_func, replace_next_func, replace_all_func, get_options_func, on_options_change_func, on_serach_text_change_func, on_close_func)

        exit_btn = QPushButton(QIcon('res/close.png'), '')
        exit_btn.setStyleSheet('padding: 1px; margin: 0px;')
        exit_btn.setToolTip('Закрыть')   
        exit_btn.clicked.connect(self.__close)

        find_next_btn = QPushButton(QIcon('res/right_arrow.png'), '')
        find_next_btn.setStyleSheet('padding: 0px; margin: 0px;')
        find_next_btn.setToolTip('Следующее совпадение')
        find_next_btn.clicked.connect(lambda: self.searchNext())
    
        find_prev_btn = QPushButton(QIcon('res/left_arrow.png'), '')
        find_prev_btn.setStyleSheet('padding: 0px; margin: 0px;')
        find_prev_btn.setToolTip('Предыдущее совпадение') 
        find_prev_btn.clicked.connect(lambda: self.searchPrev())

        self.matches_label = QLabel()

        self.search_field = QButtonLineEdit(self, [
                {'checkable' : True, 
                 'no_border' : True, 
                 'tooltip' : "Учитывать регистр", 
                 'icon' : QIcon('res/match_case.png'), 
                 'checked_icon' : QIcon('res/match_case_selected.png'), 
                 'toggled' : lambda checked: self.__setSearchOption('cs', checked)
                },                 
                {'checkable' : True, 
                 'no_border' : True, 
                 'tooltip' : "Только слова целиком", 
                 'icon' : QIcon('res/whole_word.png'), 
                 'checked_icon' : QIcon('res/whole_word_selected.png'), 
                 'toggled' : lambda checked: self.__setSearchOption('wo', checked)
                },
                {'checkable' : True, 
                 'no_border' : True, 
                 'tooltip' : "Регулярные выражения", 
                 'icon' : QIcon('res/regex.png'), 
                 'checked_icon' : QIcon('res/regex_selected.png'), 
                 'toggled' : lambda checked: self.__setSearchOption('re', checked)
                },
                {'checkable' : True, 
                 'no_border' : True, 
                 'tooltip' : "Зациклить поиск", 
                 'icon' : QIcon('res/wrap.png'), 
                 'checked_icon' : QIcon('res/wrap_selected.png'), 
                 'toggled' : lambda checked: self.__setSearchOption('wrap', checked)
                }
            ], 
            overlay_object_name='searchFieldOverlay'
        )
        self.search_field.setPlaceholderText("Поиск")
        self.search_field.textChanged.connect(self.__searchTextChanged)
        self.search_btn_cs, self.search_btn_wo, self.search_btn_re, self.search_btn_wrp = self.search_field.buttons

        self.show_replace_btn = QPushButton('')
        self.show_replace_btn.setStyleSheet('padding: 0px; margin: 0px; border: 0px;')
        self.show_replace_btn.setCursor(Qt.PointingHandCursor)
        self.show_replace_btn.clicked.connect(lambda: self.__setReplaceBlockVisible(not self.replace_field.isVisible()))

        self.replace_field = QLineEdit()
        self.replace_field.setPlaceholderText("Замена")
        self.replace_field.textChanged.connect(self.__replaceTextChanged)

        self.replace_next_btn = QPushButton(QIcon('res/replace_next.png'), '')
        self.replace_next_btn.setStyleSheet('padding: 0px; margin: 0px;')
        self.replace_next_btn.setToolTip('Заменить далее')
        self.replace_next_btn.clicked.connect(lambda: self.replaceNext())

        self.replace_all_btn = QPushButton(QIcon('res/replace_all.png'), '')
        self.replace_all_btn.setStyleSheet('padding: 0px; margin: 0px;')
        self.replace_all_btn.setToolTip('Заменить все')
        self.replace_all_btn.clicked.connect(lambda: self.replaceAll())   

        lb = QBoxLayoutBuilder(self, QBoxLayout.LeftToRight, margins=(5, 5, 5, 5), spacing=5, object_name='searchWidget')
        lb.vbox() \
            .stretch().add(self.show_replace_btn).fix(15, 15).stretch().up() \
          .vbox(spacing=5) \
            .hbox(spacing=5).add(self.search_field, object_name='searchField').fix(250, 25).add(find_prev_btn).fix(25, 25).add(find_next_btn).fix(25, 25).add(self.matches_label).stretch().add(exit_btn).fix(25, 25) \
            .up().hbox(spacing=5).add(self.replace_field, object_name='replaceField').fix(250, 25).add(self.replace_next_btn).fix(25, 25).add(self.replace_all_btn).fix(25, 25).stretch() \
            .up().stretch()
        self.__setReplaceBlockVisible(False)

    def loadFunctions(self, search_next_func, search_prev_func, replace_next_func, replace_all_func, get_options_func, on_options_change_func, on_serach_text_change_func, on_close_func):
        self.searchNext = search_next_func
        self.searchPrev = search_prev_func
        self.replaceNext = replace_next_func
        self.replaceAll = replace_all_func
        self.getOptions = get_options_func
        self.onOptionsChange = on_options_change_func
        self.onSearchTextChange = on_serach_text_change_func
        self.onClose = on_close_func

    def loadSearchOptions(self):
        options = self.getOptions()
        if options:
            self.refreshing = True
            self.search_field.setText(options['text'])
            self.search_btn_re.setChecked(options['re'])
            self.search_btn_cs.setChecked(options['cs'])
            self.search_btn_wo.setChecked(options['wo'])
            self.search_btn_wrp.setChecked(options['wrap'])
            self.replace_field.setText(options['replace'])
            self.refreshing = False
    
    def onSearchIndicatorsUpdate(self, count):
        self.matches_label.setText('Найдено: %d' % (count, ))
        self.matches_label.setStyleSheet('color: #136014' if count else 'color: #870c0c')
    
    def refreshPosition(self, parent, offset_x, offset_y):
        pos = parent.mapToGlobal(QPoint(0, 0))
        self.move(pos.x() + parent.width() - self.width() + offset_x, pos.y() + offset_y)
        self.search_field.refreshOverlayPosition()
        self.raise_()

    def setSearchText(self, text):
        self.search_field.setText(text)
    
    def open(self):
        if not self.isVisible():
            self.__setReplaceBlockVisible(False)
        self.show()

    def __setSearchOption(self, key, value):
        if not self.refreshing and self.getOptions():
            self.getOptions()[key] = value
            self.onOptionsChange(key, value)

    def __searchTextChanged(self, text):
        if not self.refreshing and self.getOptions():
            self.getOptions()['text'] = text
            self.onSearchTextChange()
    
    def __replaceTextChanged(self, text):
        if self.getOptions():
            self.getOptions()['replace'] = text
    
    def __setReplaceBlockVisible(self, visible):
        self.show_replace_btn.setIcon(QIcon('res/rightdown_triangle.png' if visible else 'res/right_triangle.png'))
        self.replace_field.setVisible(visible)
        self.replace_next_btn.setVisible(visible)
        self.replace_all_btn.setVisible(visible)
        self.setMinimumHeight(67 if visible else 37)
        self.resize(450, 67 if visible else 37)
            
    def __close(self):
        self.hide()
        self.onClose()

    