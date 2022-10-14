import threading, platform, getpass
from datetime import datetime
import psycopg2, psycopg2.extras

from PyQt5.QtWidgets import QDialog, QBoxLayout, QPushButton, QDateTimeEdit, QFileDialog, QLineEdit
from PyQt5.QtGui import QFontMetrics, QFont
from PyQt5.QtCore import Qt

from ui.components.qBoxLayoutBuilder import QBoxLayoutBuilder
from ui.components.labels import AlignLabel
from ui.components.commons import Commons

from ivk.global_log import GlobalLog
from ivk import config

class DbLog:
    db_connection = None  

    #Выполняется из pydev процесса, не использовать переменные ui-процесса, выбрасывать исключения
    @staticmethod
    def connectDb(raise_exceptions=False):
        if config.getConf("log_to_database"):
            if DbLog.db_connection is not None:
                return True
            host = config.getConf("log_db_ip")
            port = config.getConf("log_db_port")
            db = config.getConf("log_db_name")
            user = config.getConf("log_db_user")
            password = config.getConf("log_db_password")
            try:
                if host is None or port is None or db is None or user is None or password is None:
                    raise Exception("Не удалость получить параметры подключения к БД логов из конфигурации")
                DbLog.db_connection = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
                cur = DbLog.db_connection.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS log (dt timestamp NOT NULL, username varchar(250), thread_id int8 NOT NULL, source_name varchar(250) NOT NULL, source_path text, log text NOT NULL, error bool NOT NULL, additional text)")
                DbLog.db_connection.commit()
                cur.close()
                return True
            except Exception as exc:
                if raise_exceptions:
                    raise exc
        return False

    #Выполняется из pydev процесса, не использовать переменные ui-процесса, выбрасывать исключения
    @staticmethod
    def log(source_name, log, error, source_path=None, additional=None):
        connected = DbLog.connectDb()
        if not connected:
            return
        cur = DbLog.db_connection.cursor()
        cur.execute("INSERT INTO log (dt, username, thread_id, source_name, source_path, log, error, additional) VALUES (LOCALTIMESTAMP(6), %s, %s, %s, %s, %s, %s, %s)", (getpass.getuser(), threading.get_ident(), source_name, source_path, log, error, additional))
        DbLog.db_connection.commit()
        cur.close()
    
    @staticmethod
    def logGlobalAndDb(source_name, log, error):
        GlobalLog.log(threading.get_ident(), source_name, log, error)
        DbLog.log(source_name, log, error)
    
    @staticmethod
    def downloadStat(_from, _to):
        connected = DbLog.connectDb()
        if not connected:
            return None
        cur = DbLog.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM log WHERE dt >= %s AND dt <= %s ORDER BY dt ASC", (_from, _to))
        res = cur.fetchall() 
        cur.close()
        return res


#====================== ВИДЖЕТ ВЫГРУЗКИ ЛОГА ========================

class DbLogWidget(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('База данных лога')
        self.setModal(True)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.log_from = QDateTimeEdit(datetime.now(), self)
        self.log_from.setDisplayFormat("dd.MM.yyyy HH:mm:ss")
        self.log_to = QDateTimeEdit(datetime.now(), self)
        self.log_to.setDisplayFormat("dd.MM.yyyy HH:mm:ss")
        
        self.file_line_edit = QLineEdit(self)
        self.file_line_edit.setReadOnly(True)

        browse_button = QPushButton('...', self)
        browse_button.clicked.connect(self.selectFile)

        btn_cancel = QPushButton('Отмена')
        btn_cancel.clicked.connect(lambda: self.done(0))
        btn_apply = QPushButton('Выгрузить')
        btn_apply.clicked.connect(self.saveToExcel)

        fm = QFontMetrics(QFont("Consolas", 10, QFont.Normal))
        label_w = fm.width("Начало периода:")

        lb = QBoxLayoutBuilder(self, QBoxLayout.TopToBottom, margins=(5, 5, 5, 5), spacing=5)
        lb.hbox(spacing=5).add(AlignLabel("Начало периода:", Qt.AlignRight | Qt.AlignVCenter, object_name='consolasFont'), fix_w=label_w).add(self.log_from, object_name='consolasFont').stretch().up() \
          .hbox(spacing=5).add(AlignLabel("Конец периода:", Qt.AlignRight | Qt.AlignVCenter, object_name='consolasFont'), fix_w=label_w).add(self.log_to, object_name='consolasFont').stretch().up() \
          .hbox(spacing=5).add(AlignLabel("Сохранить в:", Qt.AlignRight | Qt.AlignVCenter, object_name='consolasFont'), fix_w=label_w).add(self.file_line_edit, object_name='consolasFont').add(browse_button).fix(30, self.file_line_edit.sizeHint().height()).up() \
          .stretch() \
          .hbox(spacing=5).stretch().add(btn_apply).add(btn_cancel).up() \
          
        self.resize(500, 150)
    
    def selectFile(self):
        filename = QFileDialog.getSaveFileName(self, 'Сохранить файл', self.parent().save_dir, 'Файлы статистики (*.csv)')[0]  # @UndefinedVariable
        if filename != '':
            if not filename.endswith('.csv'):
                filename += '.csv'
            self.file_line_edit.setText(filename)

    def saveToExcel(self):
        if self.file_line_edit.text() == '':
            Commons.WarningBox('Ошибка', 'Необходимо выбрать корректный файл для выгрузки статистики', self)
            return

        _from = self.log_from.dateTime().addMSecs(-self.log_from.dateTime().time().msec()).toPyDateTime()
        _to = self.log_to.dateTime().addMSecs(-self.log_to.dateTime().time().msec()).toPyDateTime()
        if _from > _to:
            Commons.WarningBox('Ошибка', 'Время начала интервала позже времени конца интервала', self)
            return

        try:
            stat = DbLog.downloadStat(_from, _to)
        except Exception as exc:
            Commons.WarningBox('Ошибка', 'При загрузке статистики из БД произошла ошибка: %s' % repr(exc), self)
            return
        
        total_text = '"Время события";"Имя пользователя";"ИД источника";"Название источника";"Путь к источнику";"Событие";"Ошибка";"Дополнителная информация"\r\n'
        for row in stat:
            log = row['log'].replace('"', '""').replace('\r\n', '\n').replace('\r', '\n').strip()
            additional = row['additional'].replace('"', '""').replace('\r\n', '\n').replace('\r', '\n').strip() if row['additional'] is not None else ''
            total_text += '"%s";"%s";"%d";"%s";"%s";"%s";"%s";"%s"\r\n' % (
                row['dt'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                row['username'] if row['username'] is not None else '',
                row['thread_id'],
                row['source_name'],
                row['source_path'] if row['source_path'] is not None else '',
                log,
                'Да' if row['error'] else 'Нет',
                additional
            )

        try:
            f = open(self.file_line_edit.text(), mode='w', encoding='utf-8', newline='') # newline='' NO NEWLINE TRANSLATION TO SYSTEM DEFAULT
            if 'windows' in platform.system().lower():
                f.write('\ufeff') #BOM для Excel
            f.write(total_text)
            f.close()
        except Exception as exc:
            Commons.WarningBox('Ошибка', 'При записи статистики в файл произошла ошибка: %s' % repr(exc), self)
            return
        
        Commons.InfoBox('Запись статистики', 'Статистика за период c %s по %s успешно записана в файл "%s"' % (_from.strftime('%Y-%m-%d %H:%M:%S'), _to.strftime('%Y-%m-%d %H:%M:%S'), self.file_line_edit.text()))

    @staticmethod
    def CSVPrepareText(text):
        text = text.replace('"', '""').replace('\r\n', '\n').replace('\r', '\n')
        

    @staticmethod
    def OpenWidget(main_win):
        if DbLog.db_connection is None:
            Commons.WarningBox('Ошибка', 'Нет подключения к БД лога, выгрузка невозможна', main_win)
            return
        w = DbLogWidget(main_win)
        code = w.exec()