import sys
sys.path.insert(0, 'lib/')
from engineers_src.tools.tools import *
# Ex.ivk_file_name = "script.ivkng"
# Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"

from ivk import config
Ex = config.get_exchange()
Ex.ivk_file_name = "script.ivkng"
Ex.ivk_file_path = "D:/VMShared/ivk-ng-myremote/engineers_src/script.ivkng"
config.getData('rokot_current_tmsid')
config.updData('rokot_current_tmsid', 6236)
vals = Ex.get('ТМИ', '14.00.writepointerAllways', 'КАЛИБР ФУЛ')
# print(vals)
vals = Ex.get('ТМИ', {'14.00.writepointerAllways': "КАЛИБР", '14.00.readpointerSession': "НЕКАЛИБР"}, 'ФУЛ')
# print(vals)


# TODO: вручную фомратирвоать файл потом
import csv
from _collections import OrderedDict
with open('excel.csv', 'w', newline='') as f:
    # в orderedDict
    # to_odict_keys = vals.keys()
    # to_odict_vals = [(key, vals[key]) for key in to_odict_keys]
    # newdict = OrderedDict(to_odict_vals)
    # все массивы сделаь равной длинны
    maxlen = 0
    for item in vals.values():
        for x in item.values():
            if len(x) > maxlen:
                maxlen = len(x)
    for item in vals.values():
        for x in item.values():
            if len(x) < maxlen:
                x.extend([None] * (maxlen - len(x)))
    # сплитануть в массив построчно
    fieldnames = []
    keys = vals.keys()
    for x in keys:
        fieldnames.append('time_' + x)
        fieldnames.append(x)
    towrite_columns = [fieldnames]
    for idx in range(0, maxlen):
        towrite_columns.append([])
        for x in keys:
            towrite_columns[-1].append(vals[x]['time'][idx])
            towrite_columns[-1].append(vals[x]['values'][idx])
    # записать в csv
    writer = csv.writer(f, delimiter=';')
    for row in towrite_columns:
        writer.writerow(row)



