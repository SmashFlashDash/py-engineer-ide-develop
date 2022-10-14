from PyQt5.QtWidgets import QBoxLayout, QGroupBox

class QBoxLayoutBuilder(QBoxLayout):
    '''
    Билдер бокс лэйаутов в linq стиле
    '''
    def __init__(self, target, direction, margins=(0, 0, 0, 0), spacing=0, object_name=None, style_sheet=None):
        super(QBoxLayoutBuilder, self).__init__(direction)
        self.setContentsMargins(*margins)
        self.setSpacing(spacing)
        if object_name:
            target.setObjectName(object_name)
        if style_sheet:
            target.setStyleSheet(style_sheet)
        
        self.stack = [self]
        self.current_widget = target
        target.setLayout(self)
    
    def removeWidgetRecursive(self, w, protected=False):
        self.__removeWidgetRecursive(self.stack[0], w, protected)
    
    def __removeWidgetRecursive(self, layout, w, protected=False):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item.widget():
                if item.widget() == w:
                    if not protected:
                        item.widget().deleteLater()
                    layout.removeWidget(item.widget())
                    return True
            else:
                if hasattr(item, 'count') and self.__removeWidgetRecursive(item, w) and item.count() == 0:
                    layout.removeItem(item)
        return False

    def clearAll(self, protected_widgets=None):
        self.__clearAll(self.stack[0], protected_widgets)

    def __clearAll(self, layout, protected_widgets=None):
        for i in reversed(range(layout.count())): 
            item = layout.itemAt(i)
            if item.widget():
                if protected_widgets is None or item.widget() not in protected_widgets:
                    item.widget().deleteLater()
                layout.removeWidget(item.widget())
            else:
                if hasattr(item, 'count'):
                    self.__clearAll(item, protected_widgets)
                layout.removeItem(item)
    
    def curLayout(self):
        return self.stack[-1]
    
    def add(self, widget, fix_w=None, fix_h=None, space_after=None, object_name=None, style_sheet=None):
        if object_name:
            widget.setObjectName(object_name)
        if style_sheet:
            widget.setStyleSheet(style_sheet)
        self.curLayout().addWidget(widget)
        self.current_widget = widget
        if space_after:
            self.curLayout().addSpacing(space_after)
        
        if fix_w and fix_h:
            self.fix(fix_w, fix_h)
        elif fix_w:
            self.fixW(fix_w)
        elif fix_h:
            self.fixH(fix_h)

        return self
    
    def up(self, fix_w=None, fix_h=None):
        if fix_w or fix_h:
            for i in range(self.curLayout().count()):
                w = self.curLayout().itemAt(i).widget()
                if w:
                    if fix_w and fix_h:
                        self.fix(fix_w, fix_h, w)
                    elif fix_w:
                        self.fixW(fix_w, w)
                    elif fix_h:
                        self.fixH(fix_h, w) 

        if len(self.stack) > 1:
            self.stack.pop()
        return self
    
    def hbox(self, margins=(0, 0, 0, 0), spacing=0, aligment=None, title=None):
        return self.__box(QBoxLayout.LeftToRight, margins, spacing, aligment, title)
    
    def vbox(self, margins=(0, 0, 0, 0), spacing=0, aligment=None, title=None):
        return self.__box(QBoxLayout.TopToBottom, margins, spacing, aligment, title)

    def __box(self, diretion, margins, spacing, aligment, title):
        box = QBoxLayout(diretion)
        box.setContentsMargins(*margins)
        box.setSpacing(spacing)
        if aligment:
            box.setAlignment(aligment)
        if title is not None:
            gb = QGroupBox(title)
            gb.setLayout(box)
            self.add(gb)
        else:
            self.curLayout().addLayout(box)
        self.stack.append(box)
        return self
    
    def stretch(self):
        self.curLayout().addStretch()
        return self
    
    def space(self, size):
        self.curLayout().addSpacing(size)
        return self

    def fix(self, width=None, height=None, widget=None):
        wdgt = widget if widget else self.current_widget
        w = wdgt.sizeHint().width() if width is None else wdgt.sizeHint().width() + int(width[1:]) if isinstance(width, str) and '+' in width else wdgt.sizeHint().width() - int(width[1:]) if isinstance(width, str) and '-' in width else width
        h = wdgt.sizeHint().height() if height is None else wdgt.sizeHint().height() + int(height[1:]) if isinstance(height, str) and '+' in height else wdgt.sizeHint().height() - int(height[1:]) if isinstance(height, str) and '-' in height else height
        wdgt.setFixedSize(w, h)
        return self
    def fixW(self, width=None, widget=None):
        wdgt = widget if widget else self.current_widget
        wdgt.setFixedWidth(wdgt.sizeHint().width() if width is None else wdgt.sizeHint().width() + int(width[1:]) if isinstance(width, str) and '+' in width else wdgt.sizeHint().width() - int(width[1:]) if isinstance(width, str) and '-' in width else width)
        return self
    def fixH(self, height=None, widget=None):
        wdgt = widget if widget else self.current_widget
        wdgt.setFixedHeight(wdgt.sizeHint().height() if height is None else wdgt.sizeHint().height() + int(height[1:]) if isinstance(height, str) and '+' in height else wdgt.sizeHint().height() - int(height[1:]) if isinstance(height, str) and '-' in height else height)
        return self
