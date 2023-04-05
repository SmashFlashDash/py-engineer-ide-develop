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


#executeWaitTMI("{04.01.beON1}@K == 'нет' and {05.01.beON2}@K == 'да' and {05.02.VSPU1} < 1 and {05.02.VSPU2} < 1",
#               20, period=1, downBCK=True)
res, dictRes = controlWaitEQ("{04.01.beON1}@K == 'нет' and {05.01.beON2}@K == 'да' and {05.02.VSPU1} < 1 and {05.02.VSPU2} < 1",
                             10, period=1, toPrint=True, downBCK=False)
print(res, dictRes)