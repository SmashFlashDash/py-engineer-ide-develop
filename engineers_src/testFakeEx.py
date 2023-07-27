# дял запуска из ide, и установить в run configurations ide
# working directory папку проекта
import sys
sys.path.insert(0, 'lib/')

from engineers_src.tools.fakeEx import Ex

print(Ex.get("ТМИ","Shiphr","КАЛИБР ТЕКУЩ"))
print(Ex.get("ТМИ","Shiphr","КАЛИБР ИНТЕРВАЛ"))
print(Ex.get("ТМИ","Shiphr","НЕКАЛИБР ТЕКУЩ"))
print(Ex.get("ТМИ","Shiphr","НЕКАЛИБР ИНТЕРВАЛ"))
print(Ex.wait("shiphr","kalibr",""))
print(Ex.wait("shiphr","kalibr",""))