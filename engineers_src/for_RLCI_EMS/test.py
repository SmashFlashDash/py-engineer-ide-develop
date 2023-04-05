# DEBUG
# from time import sleep as sleep2
# import time
# time.sleep = lambda *args: sleep2(0)
# sleep = lambda *args: sleep2(0)
# # Импорт зависимостей на винде
import sys

sys.path.insert(0, 'lib/')
from engineers_src.tools.tools import *

Ex.ivk_file_name = "script.ivkng"
Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"


def executeWaitTMI(*args, pause=None, stopFalse=True, **kwargs):
    """Вычислить выражние ТМИ с паузой перед опросом"""
    # пауза чтобы в бд изменились зачения
    if pause is not None:
        sleep(pause)
    result, dict_cpyphers = controlWaitEQ(*args, **kwargs)
    if stopFalse and not result:
        rprint('НЕ НОРМА: проверь ДИ')
        inputG('Проверь ТМИ')
    return result, dict_cpyphers


# executeWaitTMI("{04.01.beON1}@K == 'нет' and {05.01.beON2}@K == 'да' and {05.02.VSPU1} < 1 and {05.02.VSPU2} < 1",
#                20, period=1, downBCK=True)
res, dictRes = controlWaitEQ("{04.01.beON1}@K == 'нет'@any and {05.01.beON2}@K == 'да'@any and {05.02.VSPU1} < 1@any and {05.02.VSPU2} < 1@any",
                             20, period=0, toPrint=True, downBCK=False)
