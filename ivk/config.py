import sqlite3, struct, json, collections
import redis

from PyQt5.QtWidgets import QDialog, QBoxLayout, QPushButton, QScrollArea, QWidget
from PyQt5.QtGui import QColor, QFontMetrics, QFont
from PyQt5.QtCore import Qt
from PyQt5.Qsci import QsciScintilla, QsciLexerJavaScript

from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.labels import AlignLabel

class odict(collections.OrderedDict):
    def __init__(self, *args):
        if len(args) == 0:
            super().__init__()
        elif len(args) == 1 and isinstance(args[0], dict):
            super().__init__(sorted(args[0].items()))
        else:
            super().__init__()
            for item in args:
                self[item[0]] = item[1]

exchage_module = 'omka'
if exchage_module == '505':
    from ivk.sc505 import exchange_505
elif exchage_module == 'omka':
    from ivk.scOMKA import exchange_kpa
elif exchage_module == 'brk':
    from ivk.scBRK import exchange_brk

def get_exchange():
    if exchage_module == '505':
        return exchange_505.Exchange
    elif exchage_module == 'omka':
        return exchange_kpa.Exchange
    elif exchage_module == 'brk':
        return exchange_brk.Exchange

#====================== REDIS ========================
config_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
data_pool = redis.ConnectionPool(host='localhost', port=6379, db=1)

def getConf(name):
    return _redis_get(config_pool, name)

def updConf(name, val):
    return _redis_upd(config_pool, name, val)

def incConf(name, mod=None):
    res = _redis_inc(config_pool, name)
    if mod and res % mod != res:
        updConf(name, res % mod)
        return res % mod
    return res
    
def getData(name):
    return _redis_get(data_pool, name)

def updData(name, val):
    return _redis_upd(data_pool, name, val)

def incData(name, mod=None):
    res = _redis_inc(data_pool, name)
    if mod and res % mod != res:
        updData(name, res % mod)
        return res % mod
    return res

def cleanData():
    _redis_flushdb(data_pool)

def _redis_get(pool, name):
    r = redis.Redis(connection_pool=pool)
    b = r.get(name)
    return json.loads(b.decode('utf-8')) if b else None

def _redis_upd(pool, name, val):
    r = redis.Redis(connection_pool=pool)
    r.set(name, json.dumps(val).encode('utf-8'))

def _redis_flushdb(pool):
    r = redis.Redis(connection_pool=pool)
    r.flushdb()

def _redis_inc(pool, name):
    r = redis.Redis(connection_pool=pool)
    return r.incr(name)

def _redis_exists(pool, name):
    r = redis.Redis(connection_pool=pool)
    return r.exists(name)
    
#Заполняем redis-таблицу конфига, если там отсутствуют какие-либо параметры
for k, v in get_exchange().config.items():
    if not _redis_exists(config_pool, k):
        _redis_upd(config_pool, k, v)


#====================== ВИДЖЕТ НАСТРОЕК ========================
def openWidget(main_win):
    w = ConfigWidget(main_win)
    code = w.exec()
    if code == 1:
        main_win.setRebootExitCode()
        main_win.close()

class ConfigWidget(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Настройки')
        self.setModal(True)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.editors = {}
        
        fm = QFontMetrics(QFont("Consolas", 10, QFont.Normal))
        label_w = max(fm.width(key) for key in get_exchange().config.keys())
        fm = QFontMetrics(QFont("Consolas", 10, QFont.Bold))

        btn_cancel = QPushButton('Отмена')
        btn_cancel.clicked.connect(lambda: self.done(0))
        btn_apply = QPushButton('Сохранить и перезапустить')
        btn_apply.clicked.connect(self.saveAndClose)

        max_editor_w = None
        w = QWidget(self)
        lb = QBoxLayoutBuilder(w, QBoxLayout.TopToBottom, margins=(10, 10, 10, 10), spacing=10)
        for key in get_exchange().config.keys():
            val = getConf(key)
            val_text = json.dumps(val, ensure_ascii=False)
            val_text_width = fm.width(val_text)
            if max_editor_w is None or val_text_width > max_editor_w:
                max_editor_w = val_text_width

            editor = StyledLineEdit(self, val_text)
            self.editors[key] = editor

            lb.hbox(spacing=5).add(AlignLabel(key, Qt.AlignRight | Qt.AlignVCenter, object_name='consolasFont'), fix_w=label_w).add(editor).up()
        
        lb.stretch().hbox(spacing=5).stretch().add(btn_apply).add(btn_cancel).up()
        
        #скроллинг
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(w)
        lb = QBoxLayoutBuilder(self, QBoxLayout.TopToBottom, margins=(0, 0, 0, 0), spacing=0)
        lb.add(scroll_area)

        if max_editor_w:
            self.resize(label_w + max_editor_w + 200, 600)
    
    def saveAndClose(self):
        for key, editor in self.editors.items():
            updConf(key, json.loads(editor.text()))
        self.done(1)


class StyledLineEdit(QsciScintilla):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMaximumHeight(27)

        self.setMarginType(1, QsciScintilla.NumberMargin)
        self.setMarginWidth(1, 0)

        self.setUtf8(True)
        self.setWrapMode(QsciScintilla.WrapWord)
        self.setEolVisibility(False)
        self.setEolMode(QsciScintilla.EolUnix) # только \n в конце строки

        self.setLexer(CustomJsonLexer())
        self.setText(text)


class CustomJsonLexer(QsciLexerJavaScript):
    def __init__(self):
        super().__init__()
        #self.setStringsOverNewlineAllowed(True)
        #normalFont = QFont('Consolas', 10, QFont.Normal, False)
        #italicFont = QFont('Consolas', 10, QFont.Normal, True)
        demiBoldFont = QFont('Consolas', 10, QFont.DemiBold, False)
        self.setFont(demiBoldFont)
        self.setColor(QColor('#a1330e'), QsciLexerJavaScript.SingleQuotedString)
        self.setColor(QColor('#a1330e'), QsciLexerJavaScript.DoubleQuotedString)
        self.setColor(QColor('#5f3a78'), QsciLexerJavaScript.Keyword)
        self.setColor(QColor('#5f3a78'), QsciLexerJavaScript.KeywordSet2)
        self.setColor(QColor('#5f3a78'), QsciLexerJavaScript.Default)
        self.setColor(QColor('#5f3a78'), QsciLexerJavaScript.Identifier)
        #self.setFont(demiBoldFont, QsciLexerJSON.Number)
        #self.setColor(QColor('#A64800'), QsciLexerJSON.Number)
