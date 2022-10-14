import threading, time
from collections import deque
from datetime import datetime
from ui.consoleWidget import IvkConsole

class GlobalLog:
    
    @staticmethod
    def init(console_widget):
        GlobalLog.console_widget = console_widget
        GlobalLog.streams = deque([])
        GlobalLog.stop_dispatch = False
        GlobalLog.stream_dispatch_lock = threading.Lock()
        t = threading.Thread(target=GlobalLog.log_dispatch, daemon=True)
        t.start()

    @staticmethod
    def log(ident, source, stream, error):
        entryTime = datetime.now()
        GlobalLog.stream_dispatch_lock.acquire()
        appended = False
        for entry in reversed(GlobalLog.streams):
            if entry['ident'] == ident:
                if entry['error'] == error and entry['source'] == source:
                    entry['time'] = entryTime
                    entry['stream'] += stream
                    GlobalLog.streams.remove(entry)
                    GlobalLog.streams.append(entry)
                    appended = True
                break
        if not appended:
            GlobalLog.streams.append({
                'ident' : ident,
                'time' : entryTime,
                'source' : source,
                'stream' : stream,
                'error' : error
            })
        GlobalLog.stream_dispatch_lock.release()
        
    @staticmethod
    def do_log(dt, source, stream, error):
        prefix = '{#9ece94}[%s][%s] >{%s} ' % (dt.strftime(r'%d-%m-%Y %H:%M:%S.%f')[:-3], source, IvkConsole.ERROR_COLOR.name() if error else IvkConsole.MAIN_COLOR.name())
        if error:
            text = '%sОшибка -> %s' % (prefix, stream)
            GlobalLog.console_widget.writeError(text)
        else:
            GlobalLog.console_widget.writeNormal(prefix + stream)

    @staticmethod
    def log_dispatch():
        while not GlobalLog.stop_dispatch:
            GlobalLog.stream_dispatch_lock.acquire()

            while GlobalLog.streams:
                log = GlobalLog.streams[0]

                postfix = ''
                ident = log['ident']
                dt = log['time']
                source = log['source']
                stream = log['stream']
                error = log['error']
                do_log = stream.endswith('\n')

                if not do_log:
                    thread_exists = False
                    for t in threading.enumerate():
                        if t.ident == ident:
                            thread_exists = True
                            break
                    if not thread_exists:
                        do_log = True
                        stream += '\n'

                if do_log:
                    GlobalLog.streams.popleft()
                    GlobalLog.do_log(dt, source, stream, error)
                else:
                    break

            GlobalLog.stream_dispatch_lock.release()
            time.sleep(0.05)

    @staticmethod
    def onClose():
        GlobalLog.stop_dispatch = True
