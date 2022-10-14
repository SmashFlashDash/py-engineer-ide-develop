from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt

class TrueFalseIconLabel(QLabel):

    def __init__(self, true_icon_path, false_icon_path, true_tooltip, false_tooltip, initial_state, scale_w=None, scale_h=None, align=None):
        super().__init__()
        self.true_pixmap = TrueFalseIconLabel.GetScaledPixmap(true_icon_path, scale_w, scale_h)
        self.false_pixmap = TrueFalseIconLabel.GetScaledPixmap(false_icon_path, scale_w, scale_h)
        self.true_tooltip = true_tooltip
        self.false_tooltip = false_tooltip
        self.setState(initial_state)
        if align:
            self.setAlignment(align)

    def setState(self, state):
        self.setPixmap(self.true_pixmap if state else self.false_pixmap)
        self.setToolTip(self.true_tooltip if state else self.false_tooltip)
        self.update()

    @staticmethod
    def GetScaledPixmap(img_path, scale_w, scale_h):
        pix = QPixmap(img_path)
        if scale_w and scale_h:
            return pix.scaled(scale_w, scale_h) 
        elif scale_w:
            return pix.scaledToWidth(scale_w)
        elif scale_h:
            return pix.scaledToWidth(scale_h)
        else:
            return pix

class TrueFalseNoneIconLabel(QLabel):
    def __init__(self, true_icon_path, false_icon_path, none_icon_path, true_tooltip, false_tooltip, none_tooltip, initial_state, scale_w=None, scale_h=None, align=None):
        super().__init__()
        self.true_pixmap = TrueFalseIconLabel.GetScaledPixmap(true_icon_path, scale_w, scale_h)
        self.false_pixmap = TrueFalseIconLabel.GetScaledPixmap(false_icon_path, scale_w, scale_h)
        self.none_pixmap = TrueFalseIconLabel.GetScaledPixmap(none_icon_path, scale_w, scale_h)
        self.true_tooltip = true_tooltip
        self.false_tooltip = false_tooltip
        self.none_tooltip = none_tooltip
        self.setState(initial_state)
        if align:
            self.setAlignment(align)

    def setState(self, state):
        if state is None:
            self.setPixmap(self.none_pixmap)
            self.setToolTip(self.none_tooltip)
        else:
            self.setPixmap(self.true_pixmap if state else self.false_pixmap)
            self.setToolTip(self.true_tooltip if state else self.false_tooltip)
        self.update()

class StyledLabel(QLabel):
    def __init__(self, text, object_name=None, style_sheet=None):
        super().__init__(text)
        if object_name:
            self.setObjectName(object_name)
        if style_sheet:
            self.setStyleSheet(style_sheet)

class AlignLabel(StyledLabel):
    def __init__(self, text, align, object_name=None, style_sheet=None):
        super().__init__(text, object_name, style_sheet)
        self.setAlignment(align)

class GifLabelSaveSpace(QLabel):
    def __init__(self, gif_path, parent=None, visible=True, fix_w=None, fix_h=None):
        super().__init__(parent)
        
        movie = QMovie(gif_path)
        self.setMovie(movie)
        movie.start()

        sp = self.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.setSizePolicy(sp)

        self.setVisible(visible)

        if fix_w:
            self.setFixedWidth(fix_w)
        if fix_h:
            self.setFixedHeight(fix_h)

