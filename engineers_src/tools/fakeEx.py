from ivk import config

Ex = config.get_exchange()
from engineers_src.tools.tools import inputGGG, inputGG


class ExchangeFake:
    ivk_file_name = "script.ivkng"
    ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"
    db = {}

    def __init__(self):
        pass

    @staticmethod
    def send(queue_label, data):
        print("Отпрвлено в " + queue_label, " ", data)

    @staticmethod
    def get(queue_label, msg_name, field_name):
        # Массив значений, параметры разделять ","
        # Float разделять "."
        if "ТЕКУЩ" in field_name:
            title_input = "Значение"
        elif "ИНТЕРВАЛ" in field_name or "ФУЛ" in field_name:
            title_input = "Массив значений"
        else:
            raise Exception("Неверный параметр " + field_name)
        title_message = " ".join(["Получить из", queue_label, msg_name, field_name])
        title_message_tmp = title_message
        while True:
            inp: str = inputGGG(title_input, title_message_tmp)
            if inp.strip() == "":
                title_message_tmp = title_message + "\nВы ничего не ввели"
                continue
            if "НЕКАЛИБР" in field_name:
                if title_input == "Значение":
                    if "," in inp:
                        title_message_tmp = title_message + "\nНедопустимы ',' для %s" % field_name
                        continue
                    return float(inp) if "." in inp else int(inp)
                return [float(x.strip()) if "." in inp else int(x.strip()) for x in inp.split(",")]
            else:
                if title_input == "Значение":
                    return inp
                return [x.strip() for x in inp.split(",")]


    @staticmethod
    def wait(queue_label, expression, timeout, print_interval=None):
        btn_name = inputGG([('True', 'False')],
                           "Ожидать выполнения выражения:\n%s\nВ течении%s" % (expression, timeout))
        return True if btn_name == 'True' else False


ExFake = ExchangeFake()
Ex.ivk_file_name = ExFake.ivk_file_name
Ex.ivk_file_path = ExFake.ivk_file_path
Ex.get = ExFake.get
Ex.send = ExFake.send
Ex.wait = ExFake.wait
