from PyQt5.QtWidgets import QBoxLayout, QPushButton, QWidget, QLineEdit
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon

from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder

class QButtonLineEdit(QLineEdit):
    '''
    Текстовое поле с опциональными кнопками в правой части
    buttons_info - лист словарей, в которых указываются опции кнопок:
        Обязательные:
            checkable - кнопка становится зажимаемой, bool
            no_border - без границ, bool
        Необязательные:
            text - текст на кнопке, str
            icon - иконка кнопки, QIcon
            checked_text - текст, когда кнопка зажата
            checked_icon - иконка, когда кнопка зажата
            tooltip - подсказка
            clicked - обработчик нажатия, без агрументов
            toggled - обработчик изменения состояния зажатия, аргумент bool: зажата ли кнопка
    '''
    def __init__(self, parent, buttons_info=None, overlay_object_name=None, overlay_style_sheet=None):
        super().__init__(parent)
        self.overlay = QWidget(self)
        self.overlay.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.buttons = []   
        lb = QBoxLayoutBuilder(self.overlay, QBoxLayout.LeftToRight, spacing=1, object_name=overlay_object_name, style_sheet=overlay_style_sheet)
        if buttons_info:
            for button_info in buttons_info:
                b = QCheckButton(button_info)
                lb.add(b)
                self.buttons.append(b)
        self.setStyleSheet('padding-right: %dpx;' % (self.overlay.sizeHint().width() + 1))
        
    def refreshOverlayPosition(self):
        pos = self.mapToGlobal(QPoint(0, 0)) #gives global coors of top left point of self
        self.overlay.setFixedHeight(self.height()-4)
        self.overlay.move(pos.x() + self.width() - self.overlay.width() - 2, pos.y()+2)

    def hideEvent(self, *args, **kwargs):
        self.overlay.hide()
    
    def showEvent(self, *args, **kwargs):
        self.overlay.show()

class QCheckButton(QPushButton):
    def __init__(self, button_info):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet('padding: 0px; margin: 0px; border: 0px;' if button_info['no_border'] else 'padding: 0px; margin: 0px;')
        if 'text' in button_info:
            self.setText(button_info['text'])
            self.unchecked_text = button_info['text']
        else:
            self.unchecked_text = ''

        if 'icon' in button_info:
            self.setIcon(button_info['icon'])
            self.unchecked_icon = button_info['icon']
        else:
            self.unchecked_icon = QIcon()

        if 'tooltip' in button_info:
            self.setToolTip(button_info['tooltip'])

        if button_info['checkable']:
            self.setCheckable(True)
            self.checked_text = button_info['checked_text'] if 'checked_text' in button_info else None
            self.checked_icon = button_info['checked_icon'] if 'checked_icon' in button_info else None
            if self.checked_text or self.checked_icon:
                self.toggled.connect(self.toggled_handler)

        if 'clicked' in button_info:
            self.clicked.connect(button_info['clicked'])

        if 'toggled' in button_info:
            self.toggled.connect(button_info['toggled'])
    
    def toggled_handler(self, checked):
        if self.checked_text:
            self.setText(self.checked_text if checked else self.unchecked_text)
        if self.checked_icon:
            self.setIcon(self.checked_icon if checked else self.unchecked_icon)
