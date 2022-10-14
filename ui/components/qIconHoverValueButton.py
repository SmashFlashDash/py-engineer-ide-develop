from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

class QIconHoverValueButton(QPushButton):
    def __init__(self, icon, hover_icon, value=None, press_icon=None, tooltip=None, stylesheet=None, cursor=None):
        super().__init__()
        self.setCursor(cursor if cursor else Qt.PointingHandCursor)
        self.setStyleSheet(stylesheet if stylesheet else 'padding: 0px; margin: 0px; border: 0px;')
        self.setToolTip(tooltip)
        
        self.value = value

        self.normal_icon = icon
        self.hover_icon = hover_icon
        self.press_icon = press_icon
        self.setIcon(self.normal_icon)

    def setClickedValueConsumer(self, consumer):
        def consume():
            self.clearFocus()
            consumer(self.value)
        self.clicked.connect(consume)
    
    def enterEvent(self, event):
        self.setIcon(self.hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self.normal_icon)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if self.press_icon:
            self.setIcon(self.press_icon)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.press_icon:
            self.setIcon(self.normal_icon)
        super().mouseReleaseEvent(event)
