import sys, os, platform, ctypes, psutil, logging
sys.path.insert(0, os.getcwd() + '/lib')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFontDatabase
from ui.mainWindow import MainWindow


if __name__ == '__main__':
    if 'windows' in platform.system().lower():
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('VNIIEM.IVKNG.NEXT.1')

    app = QApplication(sys.argv)
    QFontDatabase.addApplicationFont("./res/DejaVuSansMono.ttf")   # подключить шрфит
    '''
    # захардкодить стиль приложения
    import PyQt5.QtWidgets
    print(PyQt5.QtWidgets.QStyleFactory.keys())
    app.setStyle('FlyPlastique')  # под sudo стиль 'Breeze'
    '''
    app.setStyle('FlyPlastique')  # под sudo стиль 'Breeze'
    app.setStyleSheet(open('styles.css', mode='r', encoding='utf-8').read())
    app.setWindowIcon(QIcon("res/mainicon.png"))

    window = MainWindow()
    window.show()
    app.exec_()
    exit_code = window.EXIT_CODE

    if 'windows' not in platform.system().lower():
        if exit_code == MainWindow.EXIT_CODE_REBOOT:
            try:
                p = psutil.Process(os.getpid())
                for handler in p.open_files() + p.connections():
                    os.close(handler.fd)
            except Exception as exc:
                logging.error(exc)
            
            python = sys.executable
            os.execl(python, python, *sys.argv)
