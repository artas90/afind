from __future__ import unicode_literals, print_function
import sys
from subprocess import Popen, PIPE
from collections import OrderedDict


class ParseResult(object):

    def __init__(
        self, filename=None, line_text=None, line_num=None, line_cols=None,
        is_title=False, is_group_delimiter=False, is_file_finished=False
    ):
        self.filename = filename
        self.line_text = line_text
        self.line_num = line_num
        self.line_cols = line_cols
        self.is_title = is_title
        self.is_group_delimiter = is_group_delimiter
        self.is_file_finished = is_file_finished


class AdapterBase(object):
    cmd_search = ''
    cmd_usage  = ''

    # params with amount of following arguments
    CUSTOM_PARAMS = OrderedDict()

    def get_results(self, adapter_params, afind_params):
        pass

    def actions_pre(self, afind_params):
        pass

    def actions_post(self, afind_params):
        pass

    def print_usage(self):
        out, err = Popen(self.cmd_usage, stdout=PIPE, stderr=PIPE, shell=True).communicate()
        sys.stdout.write(out)
        if err:
            sys.stderr.write(err)
            return False
        return True

    def _get_cmd_output(self, command):
        proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = proc.communicate()

        if err:
            sys.stderr.write(err)
            raise StopIteration

        for line in out.splitlines():
            try:
                yield line.decode('utf-8')
            except UnicodeDecodeError as e:
                sys.stderr.write(b'@afind decode-error: ' + line + b'\n')
                continue

    def _join_args(self, arguments):
        cmd = ''
        for arg in arguments:
            if ' ' in arg:
                arg = "'{}'".format(arg)
            cmd += ' ' + arg
        return cmd
