from __future__ import unicode_literals, print_function
import os
import sys
from collections import OrderedDict
from afind.utils.term_colors import TermColors
from afind.utils.search_results import SearchResults
from afind.adapters.ag import Adapter


class c(object):
    RESET    = TermColors.RESET
    FILENAME = TermColors.make_flags(TermColors.green,  bold=True)
    LINENUM  = TermColors.make_flags(TermColors.yellow, bold=True)
    MATCH    = TermColors.make_flags(TermColors.black,  bg=TermColors.yellow)


def onen_in_editor(editor_title, editor_cmd, filenames):
    """
    :param: editor_title - string
    :param: editor_cmd   - string
    :param: filenames    - SearchResults instance
    """
    if len(filenames) > 15:
        msg = '\nDo you want to open {} files? [y/n]: '.format(len(filenames))
        if raw_input(msg).strip().lower() != 'y':
            return

    files = filenames.get_filenames(only_first_line=True)

    sys.stdout.write('@afind open: {}...\n'.format(editor_title))
    cmd = "echo {} | xargs {}".format(files, editor_cmd)
    os.system(cmd)


class Application(object):

    # afind params with amount of following arguments
    CUSTOM_PARAMS = OrderedDict([
        ('--subl',         {'args_count': 0, 'description': 'Open files in SublimeText'}),
        ('--atom',         {'args_count': 0, 'description': 'Open files in Atom'}),
        ('--force-colors', {'args_count': 0, 'description': 'Preserve colors while piping'}),
        ('--afind-dbg',    {'args_count': 0, 'is_hidden': True}),
    ])

    PARAMS_FIELD_LENGTH = 24

    def __init__(self):
        self.adapter = Adapter()
        self.custom_params = OrderedDict()
        self.custom_params.update(self.adapter.CUSTOM_PARAMS)
        self.custom_params.update(self.CUSTOM_PARAMS)

    def run(self):
        self.adapter_params, self.afind_params = self.split_argv()

        if not self.adapter_params or ('-h' in self.adapter_params) or ('--help' in self.adapter_params):
            success = self.adapter.print_usage()
            if success:
                self.add_afind_usage()
            return

        self.actions_pre()
        self.all_filenames = self.parse_and_print()
        if '--afind-dbg' in self.afind_params:
            sys.stdout.write('\n@afind cmd: ' + self.adapter.cmd_search + '\n')
        self.actions_post()

    def split_argv(self):
        all_args = sys.argv[1:]
        ag_args = []

        # Means that next N params will be used by afind
        afind_curr_param = ''
        afind_args_count = 0

        adapter_params  = []
        afind_params = {}

        while all_args:
            arg = all_args.pop(0).decode('utf-8')

            if arg in self.custom_params:
                afind_curr_param = arg
                afind_args_count = self.custom_params[arg]['args_count']
                afind_params[afind_curr_param] = []

            elif afind_args_count:
                afind_params[afind_curr_param].append(arg)
                afind_args_count -= 1

            else:
                adapter_params.append(arg)

        return adapter_params, afind_params

    def parse_and_print(self):
        """
        :params: orig_out - string
            output from ag in ackmate format. Example:
            :path/to/file.py
            89;7 8:         a = {}
        :return: SearchResults instance
        """

        if sys.stdout.isatty() or ('--force-colors' in self.afind_params):
            printer = self._print_to_tty()
        else:
            printer = self._print_to_pipe()

        all_filenames = SearchResults()

        for res in printer:
            all_filenames.add_result(res.filename, res.line_num)

        return all_filenames

    def _print_to_tty(self):

        for res in self.adapter.get_results(self.adapter_params, self.afind_params):
            if res.is_file_finished:
                sys.stdout.write('\n')

            elif res.is_title:
                sys.stdout.write(c.FILENAME + res.filename.encode('utf-8') + c.RESET + b'\n')
                yield res

            else:
                sys.stdout.write(c.LINENUM + res.line_num.encode('utf-8') + b':' + c.RESET)

                line_text = res.line_text.encode('utf-8')
                cursor = 0
                for start, length in res.line_cols:
                    end = start + length
                    sys.stdout.write(line_text[cursor:start])
                    sys.stdout.write(c.MATCH + line_text[start:end] + c.RESET)
                    cursor = end
                sys.stdout.write(line_text[cursor:] + b'\n')

                yield res

    def _print_to_pipe(self):
        current_filename = ''

        for res in self.adapter.get_results(self.adapter_params, self.afind_params):
            if res.is_file_finished:
                pass

            elif res.is_title:
                current_filename = res.filename.encode('utf-8')
                yield res

            else:
                sys.stdout.write(current_filename + b':')
                sys.stdout.write(res.line_num.encode('utf-8') + b':' + res.line_text.encode('utf-8'))
                sys.stdout.write(b'\n')
                yield res

    def add_afind_usage(self):
        usage = ''
        for param in self.custom_params:
            if self.custom_params[param].get('is_hidden'):
                continue
            usage += '  ' + param.ljust(self.PARAMS_FIELD_LENGTH)
            usage += self.custom_params[param]['description'] + '\n'
        sys.stdout.write('afind Options:\n' + usage)

    def actions_pre(self):
        pass

    def actions_post(self):
        if '--subl' in self.afind_params and self.all_filenames:
            onen_in_editor('SublimeText', 'subl', self.all_filenames)

        if '--atom' in self.afind_params and self.all_filenames:
            onen_in_editor('Atom.io', 'atom', self.all_filenames)
