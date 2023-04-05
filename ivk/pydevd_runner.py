import socket, threading, os, platform, subprocess, sys
from urllib.parse import unquote
import xmltodict


class PyDevDRunner:
    PAUSE_STDOUT_CODE = 'E39AB7CEBAC67D27CC7A6763C714CC93_PAUSE_STDOUT_A86F0E4FDB33991063CD08E63F8CBFFA'

    def __init__(self, outNormalFunc, outErrorFunc, outInputFunc, outPdbFunc, requsetInputFunc, onThreadCreateFunc,
                 onThreadKillFunc, getScriptDataFunc):
        self.outNormalFunc = outNormalFunc
        self.outErrorFunc = outErrorFunc
        self.outInputFunc = outInputFunc
        self.outPdbFunc = outPdbFunc
        self.requsetInputFunc = requsetInputFunc
        self.getScriptDataFunc = getScriptDataFunc
        self.onThreadCreateFunc = onThreadCreateFunc
        self.onThreadKillFunc = onThreadKillFunc

        self.stop_server = False
        self.subprocess = None
        self.connection = None

        self.std_code_page = None

        self.sequence = 1
        self.pydevd_main_thread = None
        self.pydevd_threads = []
        self.selected_pydevd_thread = None
        self.pydevd_input_lock = {'lock': threading.Lock(), 'thread': None}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', 0))
        self.sock.listen()

        self.server_thread = threading.Thread(target=self.__server, daemon=True)
        self.server_thread.start()

    def __del__(self):
        self.stop_server = True
        if self.connection:
            self.connection.close()
        self.sock.close()
        if self.onThreadKillFunc:
            self.onThreadKillFunc(None, True)

    def __server(self):
        self.connection, self.connection_address = self.sock.accept()
        self.sendTCP(PyDevDRequest.SetProtocol('quoted-line'))
        self.sendTCP(
            PyDevDRequest.SetVersion(1, 'WINDOWS' if platform.system().lower() == 'windows' else 'UNIX', 'LINE'))
        self.sendTCP(PyDevDRequest.SetPyException(False, False, False, True, True))
        if self.breakpoints:
            for line in self.breakpoints:
                self.sendTCP(PyDevDRequest.SetBreakLine(self.filename, line))
        if self.input_breakpoints:
            for line in self.input_breakpoints:
                if line not in self.breakpoints:
                    self.sendTCP(PyDevDRequest.SetBreakLine(self.filename, line))
        self.sendTCP(PyDevDRequest.Run())
        buf = ''
        while not self.stop_server:
            try:
                buf += self.connection.recv(1024).decode('utf-8')
            except ConnectionResetError:
                self.stop_server = True
                continue
            if buf.endswith('\n'):
                bufs = buf.strip().split('\n')
                for b in bufs:
                    self.__pydevdResponceAction(PyDevDResponse.parse(unquote(b)))
                buf = ''

    def updateBreakpoint(self, line, add):
        if add:
            self.sendTCP(PyDevDRequest.SetBreakLine(self.filename, line))
            if line not in self.breakpoints:
                self.breakpoints.append(line)
        else:
            self.sendTCP(PyDevDRequest.RemoveBreakLine(self.filename, line))
            if line in self.breakpoints:
                self.breakpoints.remove(line)

    def sendTCP(self, command):
        if self.connection:
            self.connection.send(command.toTCP(self.sequence))
            self.sequence += 2

    def onThreadChanged(self, thread):
        if thread:
            for t in self.pydevd_threads:
                if t['thread_id'] == thread['thread_id']:
                    self.selected_pydevd_thread = t
                    return
        self.selected_pydevd_thread = None

    def __getPydevdThread(self, thread_id):
        for t in self.pydevd_threads:
            if t['thread_id'] == thread_id:
                return t
        return None

    def __pydevdResponceAction(self, resp):
        # print(repr(resp))
        if resp.ident == 103:  # CMD_THREAD_CREATE
            payload = resp.payloadToDict()
            thread = {
                'thread_id': payload['xml']['thread']['@id'],
                'thread_name': unquote(payload['xml']['thread']['@name']),
                'suspend_frame': None,
                'suspend_line': None,
                'waiting_input': False,
                'waiting_pdb_input': False
            }
            if self.__getPydevdThread(thread['thread_id']) is None:
                self.pydevd_threads.append(thread)
            if self.onThreadCreateFunc:
                self.onThreadCreateFunc(thread)
            if self.pydevd_main_thread is None:
                self.pydevd_main_thread = thread

        elif resp.ident == 104:  # CMD_THREAD_KILL
            thread = self.__getPydevdThread(resp.payload)
            if self.onThreadKillFunc:
                self.onThreadKillFunc(thread, thread is self.pydevd_main_thread)
            self.pydevd_threads.remove(thread)
            if thread is self.pydevd_main_thread:
                self.stop_server = True

        elif resp.ident == 147:  # CMD_INPUT_REQUESTED
            if resp.payload == 'True':
                thread = self.pydevd_input_lock['thread']
                thread['waiting_input'] = True
                self.requsetInputFunc(thread['thread_id'], thread['suspend_line'], False,
                                      'Ввод (%s)' % thread['thread_name'])

        elif resp.ident == 105:  # CMD_THREAD_SUSPEND
            payload = resp.payloadToDict()
            thread = self.__getPydevdThread(payload['xml']['thread']['@id'])

            if isinstance(payload['xml']['thread']['frame'], list):
                thread['suspend_frame'] = payload['xml']['thread']['frame'][0]['@id']
                thread['suspend_line'] = int(payload['xml']['thread']['frame'][0]['@line'])
            else:
                thread['suspend_frame'] = payload['xml']['thread']['frame']['@id']
                thread['suspend_line'] = int(payload['xml']['thread']['frame']['@line'])

            if thread['suspend_line'] in self.input_breakpoints and thread['suspend_line'] not in self.breakpoints:
                self.pydevd_input_lock['lock'].acquire()
                self.pydevd_input_lock['thread'] = thread
                self.sendTCP(PyDevDRequest.Resume(thread['thread_id']))
                return

            if self.getScriptDataFunc:
                script_data = self.getScriptDataFunc(thread['suspend_line'])
                self.outPdbFunc('[ПАУЗА ПОТОКА %s "%s"] > %s (строка %d) -> %s\n' % (
                thread['thread_id'], thread['thread_name'], script_data[0], script_data[1], script_data[2]))

            thread['waiting_pdb_input'] = True
            self.requsetInputFunc(thread['thread_id'], thread['suspend_line'], True, 'DBG (%s)' % thread['thread_name'])

        elif resp.ident == 113:  # CMD_EVALUATE_EXPRESSION
            payload = resp.payloadToDict()
            thread = self.selected_pydevd_thread
            self.outPdbFunc('[ОТВЕТ ПОТОКА %s "%s"] > %s\n' % (
            thread['thread_id'], thread['thread_name'], unquote(payload['xml']['var']['@value'])))
            thread['waiting_pdb_input'] = True
            self.requsetInputFunc(thread['thread_id'], thread['suspend_line'], True, 'DBG (%s)' % thread['thread_name'])

    def sendInput(self, text):
        if self.subprocess and self.selected_pydevd_thread:
            thread = self.selected_pydevd_thread
            if thread['waiting_pdb_input']:
                text = text.strip()
                if thread['suspend_line'] in self.input_breakpoints and text.lower() in (
                '!c', '!continue', '!n', '!next'):
                    self.pydevd_input_lock['lock'].acquire()
                    self.pydevd_input_lock['thread'] = thread
                if text.lower() in ('!c', '!continue'):
                    self.sendTCP(PyDevDRequest.Resume(thread['thread_id']))
                elif text.lower() in ('!n', '!next'):
                    self.sendTCP(PyDevDRequest.StepOver(thread['thread_id']))
                else:
                    self.sendTCP(PyDevDRequest(113, [('thread_id', thread['thread_id']),
                                                     ('frame_id', thread['suspend_frame']), ('scope', 'LOCAL'),
                                                     ('expression', text), ('trim', 0)]))
                thread['waiting_pdb_input'] = False

            elif thread['waiting_input']:
                self.subprocess.stdin.write((text + '\n').encode(self.std_code_page))
                self.subprocess.stdin.flush()
                thread['waiting_input'] = False
                self.pydevd_input_lock['lock'].release()

            elif text.strip().lower() in ('!p', '!pause'):
                self.sendTCP(PyDevDRequest.Pause(thread['thread_id']))

    def runScript(self, filename, breakpoints, input_breakpoints):
        self.filename = filename
        self.breakpoints = breakpoints
        self.input_breakpoints = input_breakpoints

        executable = sys.executable if "python" in sys.executable else "python"
        pydevd_path = os.getcwd() + '/lib/pydevd/pydevd.py'
        cmd = '%s %s --vm_type python --client 127.0.0.1 --port %d --file %s' % (
        executable, pydevd_path, self.sock.getsockname()[1], filename)
        self.subprocess = subprocess.Popen(cmd.split(' '), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, shell=False)
        # cwd=os.getcwd()
        # platform.system().lower() != 'windows'

        while True:
            line = self.subprocess.stdout.readline()
            if self.std_code_page is None:
                try:
                    tmp = line.decode('cp1251').strip()
                    if tmp == 'я':
                        self.std_code_page = 'cp1251'
                except:
                    pass
                if self.std_code_page is None:
                    try:
                        tmp = line.decode('utf-8').strip()
                        if tmp == 'я':
                            self.std_code_page = 'utf-8'
                    except:
                        pass
                if self.std_code_page is not None:
                    self.outNormalFunc('Кодировка потока успешно определена: %s\n' % self.std_code_page)
                    continue
                else:
                    self.outErrorFunc(
                        'Не удалось определить кодировку потока при первом чтении, остановка выполнения скрипта\n')
                    self.terminate()
                    break
            else:
                line = line.decode(self.std_code_page)
            if line == '' and self.subprocess.poll() is not None:
                break
            # Пауза потока по спец ключу на следующей инструкции (сработает только для главной треды)
            # if PyDevDRunner.PAUSE_STDOUT_CODE in line:
            #     if self.pydevd_main_thread:
            #         self.sendTCP(PyDevDRequest.Pause(self.pydevd_main_thread['thread_id']))
            #     if line.strip() != PyDevDRunner.PAUSE_STDOUT_CODE:
            #         line = line[:line.indexOf(PyDevDRunner.PAUSE_STDOUT_CODE)] + line[line.indexOf(PyDevDRunner.PAUSE_STDOUT_CODE)+len(PyDevDRunner.PAUSE_STDOUT_CODE):]
            #         self.outNormalFunc(line)
            # else:
            #     self.outNormalFunc(line)
            self.outNormalFunc(line)

        traceback = ''
        output = self.subprocess.communicate()
        if output[1] and self.std_code_page is not None:  # self.subprocess.returncode != 0
            traceback = output[1].decode(self.std_code_page)

        return traceback.replace('\r\n', '\n')

    def terminate(self):
        if self.subprocess:
            self.subprocess.kill()
            if self.onThreadKillFunc is not None:
                self.onThreadKillFunc(None, True)
            else:
                print("onThreadKillFunc is None")

    @staticmethod
    def ParseTraceback(traceback, line_correction):
        first_line_captured = False
        error_line = None
        for line in reversed(traceback.splitlines()):
            if not first_line_captured and line.strip():
                exc = line.strip()
                first_line_captured = True
            line = line.lower().strip()
            if 'pdb_ivkng_script' in line and 'line' in line:
                begin_index = line.find('line') + 5
                end_index = line.find(',', begin_index)
                if end_index == -1:
                    end_index = len(line)
                error_line = int(line[begin_index:end_index]) - line_correction - 1
                break
        return error_line, exc


class PyDevDResponse:
    def __init__(self, ident, seq, payload):
        self.ident = ident
        self.meaning = PyDevDRequest.ID_TO_MEANING[str(ident)]
        self.seq = seq
        self.payload = payload

    @staticmethod
    def parse(data):
        splitted = data.strip().split('\t')
        return PyDevDResponse(int(splitted[0]), int(splitted[1]),
                              splitted[2] if len(splitted) == 3 else (splitted[2:] if len(splitted) > 3 else None))

    def __repr__(self):
        return 'command: %d (%s)\nsequence: %d\npayload: %s\n' % (self.ident, self.meaning, self.seq, str(self.payload))

    def payloadToDict(self):
        return xmltodict.parse(self.payload)


class PyDevDRequest:

    def __init__(self, ident, args=[]):
        self.ident = ident
        self.meaning = PyDevDRequest.ID_TO_MEANING[str(ident)]
        self.args = args

    def toTCP(self, seq):
        c = '%d\t%d' % (self.ident, seq)
        if self.args:
            c += '\t'
            c += '\t'.join([str(arg[1]) for arg in self.args])
        c += '\n'
        return c.encode('utf-8')

    def __repr__(self):
        info = 'command: %d (%s)' % (self.ident, self.meaning)
        if self.args:
            info += 'args:\n'
            info += '\n'.join(['    %s = %s' % (arg[0], arg[1]) for arg in self.args])
            info += '\n'
        return info

    @staticmethod
    def Run():
        return PyDevDRequest(101, [('empty_param', '')])

    @staticmethod
    def Pause(thread_id):
        return PyDevDRequest(105, [('thread_id', thread_id)])

    @staticmethod
    def Resume(thread_id):
        return PyDevDRequest(106, [('thread_id', thread_id)])

    @staticmethod
    def StepOver(thread_id):
        return PyDevDRequest(108, [('thread_id', thread_id)])

    @staticmethod
    def SetBreakLine(filename, line, func_name='None', suspend_policy='NONE', condition='None', expression='None'):
        return PyDevDRequest(111, [
            ('btype', 'python-line'),
            ('filename', filename),
            ('line', line),
            ('func_name', func_name),
            ('suspend_policy', suspend_policy),
            ('condition', condition),
            ('expression', expression),
        ])

    @staticmethod
    def RemoveBreakLine(filename, line):
        return PyDevDRequest(112, [
            ('btype', 'python-line'),
            ('filename', filename),
            ('line', line)
        ])

    @staticmethod
    def SetProtocol(protocol):
        '''
        protocol: 'quoted-line', 'http', 'json',  'http_json'
        '''
        return PyDevDRequest(503, [('protocol', protocol)])

    @staticmethod
    def SetVersion(local_version, os_type, breakpoints_by):
        '''
        local_version: any integer
        os_type: 'WINDOWS' or 'UNIX'
        breakpoints_by: 'ID' or 'LINE'
        '''
        return PyDevDRequest(501, [('local_version', local_version), ('os_type', os_type),
                                   ('breakpoints_by', breakpoints_by)])

    @staticmethod
    def SetPyException(break_on_uncaught,
                       break_on_caught,
                       skip_on_exceptions_thrown_in_same_context,
                       ignore_exceptions_thrown_in_lines_with_ignore_exception,
                       ignore_libraries):
        return PyDevDRequest(131, [('exceptions', ';'.join(
            [str(break_on_uncaught).lower(), str(break_on_caught).lower(),
             str(skip_on_exceptions_thrown_in_same_context).lower(),
             str(ignore_exceptions_thrown_in_lines_with_ignore_exception).lower(),
             str(ignore_libraries).lower()]) + ';')])

    @staticmethod
    def SetShowReturnValues(show_retrun_values):
        '''
        show_retrun_values: True/False
        '''
        return PyDevDRequest(146, [('name', 'CMD_SHOW_RETURN_VALUES'),
                                   ('show_retrun_values', 1 if show_retrun_values else 0)])

    ID_TO_MEANING = {
        '101': 'CMD_RUN',
        '102': 'CMD_LIST_THREADS',
        '103': 'CMD_THREAD_CREATE',
        '104': 'CMD_THREAD_KILL',
        '105': 'CMD_THREAD_SUSPEND',
        '106': 'CMD_THREAD_RUN',
        '107': 'CMD_STEP_INTO',
        '108': 'CMD_STEP_OVER',
        '109': 'CMD_STEP_RETURN',
        '110': 'CMD_GET_VARIABLE',
        '111': 'CMD_SET_BREAK',
        '112': 'CMD_REMOVE_BREAK',
        '113': 'CMD_EVALUATE_EXPRESSION',
        '114': 'CMD_GET_FRAME',
        '115': 'CMD_EXEC_EXPRESSION',
        '116': 'CMD_WRITE_TO_CONSOLE',
        '117': 'CMD_CHANGE_VARIABLE',
        '118': 'CMD_RUN_TO_LINE',
        '119': 'CMD_RELOAD_CODE',
        '120': 'CMD_GET_COMPLETIONS',
        '121': 'CMD_CONSOLE_EXEC',
        '122': 'CMD_ADD_EXCEPTION_BREAK',
        '123': 'CMD_REMOVE_EXCEPTION_BREAK',
        '124': 'CMD_LOAD_SOURCE',
        '125': 'CMD_ADD_DJANGO_EXCEPTION_BREAK',
        '126': 'CMD_REMOVE_DJANGO_EXCEPTION_BREAK',
        '127': 'CMD_SET_NEXT_STATEMENT',
        '128': 'CMD_SMART_STEP_INTO',
        '129': 'CMD_EXIT',
        '130': 'CMD_SIGNATURE_CALL_TRACE',

        '131': 'CMD_SET_PY_EXCEPTION',
        '132': 'CMD_GET_FILE_CONTENTS',
        '133': 'CMD_SET_PROPERTY_TRACE',
        '134': 'CMD_EVALUATE_CONSOLE_EXPRESSION',
        '135': 'CMD_RUN_CUSTOM_OPERATION',
        '136': 'CMD_GET_BREAKPOINT_EXCEPTION',
        '137': 'CMD_STEP_CAUGHT_EXCEPTION',
        '138': 'CMD_SEND_CURR_EXCEPTION_TRACE',
        '139': 'CMD_SEND_CURR_EXCEPTION_TRACE_PROCEEDED',
        '140': 'CMD_IGNORE_THROWN_EXCEPTION_AT',
        '141': 'CMD_ENABLE_DONT_TRACE',
        '142': 'CMD_SHOW_CONSOLE',
        '143': 'CMD_GET_ARRAY',
        '144': 'CMD_STEP_INTO_MY_CODE',
        '145': 'CMD_GET_CONCURRENCY_EVENT',
        '146': 'CMD_SHOW_RETURN_VALUES',
        '147': 'CMD_INPUT_REQUESTED',
        '148': 'CMD_GET_DESCRIPTION',

        '149': 'CMD_PROCESS_CREATED',  # Note: this is actually a notification of a sub-process created.
        '150': 'CMD_SHOW_CYTHON_WARNING',
        '151': 'CMD_LOAD_FULL_VALUE',
        '152': 'CMD_GET_THREAD_STACK',
        '153': 'CMD_THREAD_DUMP_TO_STDERR',
        '154': 'CMD_STOP_ON_START',
        '155': 'CMD_GET_EXCEPTION_DETAILS',
        '156': 'CMD_PYDEVD_JSON_CONFIG',
        '157': 'CMD_THREAD_SUSPEND_SINGLE_NOTIFICATION',
        '158': 'CMD_THREAD_RESUME_SINGLE_NOTIFICATION',

        '159': 'CMD_STEP_OVER_MY_CODE',
        '160': 'CMD_STEP_RETURN_MY_CODE',

        '200': 'CMD_REDIRECT_OUTPUT',
        '201': 'CMD_GET_NEXT_STATEMENT_TARGETS',
        '202': 'CMD_SET_PROJECT_ROOTS',
        '203': 'CMD_MODULE_EVENT',
        '204': 'CMD_PROCESS_EVENT',  # DAP process event.

        '205': 'CMD_AUTHENTICATE',

        '501': 'CMD_VERSION',
        '502': 'CMD_RETURN',
        '503': 'CMD_SET_PROTOCOL',
        '901': 'CMD_ERROR',
    }


'''
        #MAIN OUTPUT
        writer = lambda char: self.console.writeNormal(char)
        write_traceback = False
        traceback = ''
        write_pdb = False
        pdb_buf = ''
        total_buf = ''
        
            total_buf += out_char
            if out_char == cfc.STDOUT_SYM:
                writer = lambda char: self.console.writeNormal(char)
                write_traceback = False
                write_pdb = False
            elif out_char == cfc.STDERR_SYM:
                writer = lambda char: self.console.writeError(char)
                write_traceback = False
                write_pdb = False
            elif out_char == cfc.STDERR_TRACEBACK_SYM:
                writer = lambda char: self.console.writeError(char)
                write_traceback = True
                write_pdb = False
            elif out_char == cfc.STDIN_SYM:
                writer = lambda char: self.console.writeInput(char)
                write_traceback = False
                write_pdb = False
            elif out_char == cfc.PDB_STDIN_SYM:
                writer = lambda char: self.console.writePdb(char)
                write_traceback = False
                write_pdb = True
            elif out_char == cfc.CALL_INPUT_SYM:
                self.console.requestInput(from_pdb=False, pdb_mode=self.show_pdb_checkbox.checkState() == Qt.Checked, '')
                write_traceback = False
            elif out_char == cfc.CALL_PDB_INPUT_SYM:
                for line in reversed(pdb_buf.splitlines()):
                    if '>' in line and 'pdb_ivkng_script' in line:
                        pdb_line = self.__parsePdbLine(line)
                        if pdb_line:
                            self.text_edit.onPdbBreakpoint(pdb_line - self.__currentLineCorrection(pdb_line-1) - 1, True)
                        break
                self.console.requestInput(from_pdb=True, pdb_mode=self.show_pdb_checkbox.checkState() == Qt.Checked, '')
                write_traceback = False
            else:
                writer(out_char)
                if write_traceback:
                    traceback += out_char
                if write_pdb:
                    pdb_buf += out_char
'''
