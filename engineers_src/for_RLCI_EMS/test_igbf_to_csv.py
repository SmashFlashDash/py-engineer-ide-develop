import csv
import os
from datetime import datetime


filename = 'temp_AB_%s.csv' % datetime.now().strftime("%Y.%m.%d %H.%M.%S")
if filename.count('/') > 0:
    os.makedirs(os.path.dirname(filename), 0o775, exist_ok=True)
with open(filename, 'w+') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(('time', 'ab_1', 'ab_2', 'ab_3', 'ab_4', 'ab_5', 'ab_6',
                     'ab_7', 'ab_8', 'ab_9', 'ab_10', 'ab_11', 'ab_12'))
with open(filename, 'a+') as f:
    writer = csv.writer(f, delimiter=';')
    while True:
        row = [str(datetime.now().strftime("%Y:%m:%d %H:%M:%S"))]
        for x in range(1, 13):
            try:
                row.append(Ex.get('Ячейка ПИ', 'ЗапрТемпАБ', 'темп_канал_%s' % x))
            except Exception as ex:
                row.append('None')
                rprint('От ячекйи ПИ приходит None')
        writer.writerow(row)
        f.flush()
        print('Записано: %s' % row)
        sleep(100)
