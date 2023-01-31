from engineers_src.tools.tools import SCPICMD, AsciiHex, sleep, OBTS, Ex, CPIMD, inputG


def bck_rlci_off():
    # Откючение КППИ осн (-450 мА)
    SCPICMD(0x43FF, OBTS('2000:1:1:0:0:0'), AsciiHex('0x 0000 0000'))  # Снять питанние с Ku
    sleep(1)
    SCPICMD(0x5321, AsciiHex('0x 0500 0000 0000 0000'))  # Выдать потенциальную команду на откл. Ku осн
    sleep(1)
    SCPICMD(0x43F7, OBTS('2000:1:1:0:0:0'), AsciiHex('0x 0000 0000'))  # Снять питанние с НРЛ-Р
    sleep(1)
    SCPICMD(0x5321, AsciiHex('0x 0700 0000 0000 0000'))  # Выдать потенциальную команду  на откл. P осн

    # Откючение КППИ рез
    SCPICMD(0x43FF, OBTS('2000:1:1:0:0:0'), AsciiHex('0x 0000 0000'))  # Снять питанние с Ku
    sleep(1)
    SCPICMD(0x5321, AsciiHex('0x 0600 0000 0000 0000'))  # Выдать потенциальную команду на откл. Ku рез
    sleep(1)
    SCPICMD(0x43F7, OBTS('2000:1:1:0:0:0'), AsciiHex('0x 0000 0000'))  # Снять питанние с НРЛ-Р
    sleep(1)
    SCPICMD(0x5321, AsciiHex('0x 0800 0000 0000 0000'))  # Выдать потенциальную команду на откл. P рез

    # М-778Б снять питание (-500 мА)
    SCPICMD(0x43EB, OBTS('2000:1:1:0:0:0'), AsciiHex('0x 0000 0000'))  # отключение М-778Б

    # БСпА снять питание (-300 мА)
    SCPICMD(0x43FD)  # Разомкнуть ключ КПТ на БСпА 2
    sleep(1.5)
    SCPICMD(0x5321, AsciiHex('0x 0100 0000 0000 0000'))  # Снять потенциальную команду с БСпАосн
    sleep(1.5)
    SCPICMD(0x5321, AsciiHex('0x 0200 0000 0000 0000'))  # Снять потенциальную команду с БСпАрез
    sleep(1.5)
    SCPICMD(0xe06f, AsciiHex('0x 0600 0000 0000 0000'))  # отключение обмена БСпА1
    sleep(1.5)
    SCPICMD(0xe06f, AsciiHex('0x 0700 0000 0000 0000'))  # отключение обмена БСпА2

    # ОТКЛЮЧЕНИЕ
    SCPICMD(0xA00B)  # УМ
    sleep(1)
    SCPICMD(0xA008)  # МОД
    sleep(1)
    SCPICMD(0xA005)  # ФИП
    sleep(1)
    SCPICMD(0xA002)  # ПЧ
    sleep(1)
    SCPICMD(0xE005, AsciiHex('0111000000000000'))  # Снять питание ЭА331
    sleep(1)
    SCPICMD(0xE005, AsciiHex('0113000000000000'))  # Снять питание ЭА332
