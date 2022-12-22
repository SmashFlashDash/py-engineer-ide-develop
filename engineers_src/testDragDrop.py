
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


import csv
import os
from datetime import datetime

vals = Ex.get('ТМИ', '14.00.writepointerAllways', 'КАЛИБР ФУЛ')
# print(vals)
vals = Ex.get('ТМИ', {'14.00.writepointerAllways': "КАЛИБР", '14.00.readpointerSession': "НЕКАЛИБР"}, 'ФУЛ')
# print(vals)


def writeFullToCsv(filename, vals_from_ExGet_Full):
    # в orderedDict
    # to_odict_keys = vals.keys()
    # to_odict_vals = [(key, vals[key]) for key in to_odict_keys]
    # newdict = OrderedDict(to_odict_vals)
    filename += '_' + datetime.now().strftime("%Y.%m.%d %H.%M.%S")
    if filename.count('/') > 0:
        os.makedirs(os.path.dirname(filename), 0o775, exist_ok=True)
    with open(filename, 'w', newline='') as f:
        # все массивы равной длинны
        maxlen = 0
        for item in vals_from_ExGet_Full.values():
            for x in item.values():
                if len(x) > maxlen:
                    maxlen = len(x)
        for item in vals_from_ExGet_Full.values():
            for x in item.values():
                if len(x) < maxlen:
                    x.extend([None] * (maxlen - len(x)))
        # сплитануть в массивы построчно
        fieldnames = []
        keys = vals_from_ExGet_Full.keys()
        for x in keys:
            fieldnames.append('time_' + x)
            fieldnames.append(x)
        towrite_columns = [fieldnames]
        for idx in range(0, maxlen):
            towrite_columns.append([])
            for x in keys:
                val = vals_from_ExGet_Full[x]['values'][idx]
                if isinstance(val, float):
                    val = str(val).replace('.', ',')
                elif isinstance(val, str) and val.endswith('.000'):
                    val = val[:-4]
                time = vals_from_ExGet_Full[x]['time'][idx]
                try:
                    time = datetime.fromtimestamp(int(time)).strftime("%Y:%m:%d %H:%M:%S")
                except Exception as ex:
                    time = str(vals_from_ExGet_Full[x]['time'][idx]).replace('.', ',')
                towrite_columns[-1].append(time)
                towrite_columns[-1].append(val)
        # записать в csv
        writer = csv.writer(f, delimiter=';')
        for row in towrite_columns:
            writer.writerow(row)


writeFullToCsv('excel.csv', vals)



