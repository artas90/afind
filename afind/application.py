from __future__ import unicode_literals, print_function
import os
import sys
from collections import OrderedDict
from afind.utils.search_results import SearchResults
from afind.utils.result_formatters import tty_formatter, pipe_formatter, patch_formatter
from afind.utils.editors import onen_in_editor
from afind.adapters.ag import Adapter


class Application(object):

    # afind params with amount of following arguments
    CUSTOM_PARAMS = OrderedDict([
        ('--subl',         {'args_count': 0, 'description': 'Open files in SublimeText'}),
        ('--atom',         {'args_count': 0, 'description': 'Open files in Atom'}),
        ('--make-patch',   {'args_count': 0, 'description': 'Generate patch for bulk file editing'}),
        ('--apply-patch',  {'args_count': 1, 'description': 'Apply previously generated patch'}),
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

        show_usage = False

        if  ('-h' in self.adapter_params) or ('--help' in self.adapter_params):
            show_usage = True
        elif '--apply-patch' in self.afind_params:
            show_usage = False
        elif not self.adapter_params:
            show_usage = True

        if show_usage:
            success = self.adapter.print_usage()
            if success:
                self.add_afind_usage()
            return

        if '--apply-patch' in self.afind_params:
            self._run_patch_apply()
        else:
            self._run_search()

    def _run_search(self):
        self.actions_pre()
        self.all_filenames = self.parse_and_print()
        if '--afind-dbg' in self.afind_params:
            sys.stdout.write('\n@afind cmd: ' + self.adapter.cmd_search + '\n')
        self.actions_post()

    def _run_patch_apply(self):
        cmd = 'patch --unified --strip=1 --force --input ' + self.afind_params['--apply-patch'][0]
        os.system(cmd)

    def split_argv(self):
        all_args = sys.argv[1:]
        ag_args = []

        # Means that next N params will be used by afind
        afind_curr_param = ''
        afind_args_count = 0

        adapter_params  = []
        afind_params = {}

        while all_args:
            param_name = all_args.pop(0).decode('utf-8')

            if param_name in self.custom_params:
                afind_curr_param = param_name
                afind_args_count = self.custom_params[param_name]['args_count']
                afind_params[afind_curr_param] = []

            elif afind_args_count:
                afind_params[afind_curr_param].append(param_name)
                afind_args_count -= 1

            else:
                adapter_params.append(param_name)

        for param_name in afind_params:
            args_count = self.custom_params[param_name]['args_count']

            if len(afind_params[param_name]) < args_count:
                err = b"Error: Parameter {} requires {} following arguments\n".format(param_name, args_count)
                sys.stderr.write(err)
                sys.exit(1)

        return adapter_params, afind_params

    def parse_and_print(self):
        """
        :params: orig_out - string
            output from ag in ackmate format. Example:
            :path/to/file.py
            89;7 8:         a = {}
        :return: SearchResults instance
        """

        results = self.adapter.get_results(self.adapter_params, self.afind_params)

        if '--make-patch' in self.afind_params:
            results = patch_formatter(results)
        elif sys.stdout.isatty() or ('--force-colors' in self.afind_params):
            results = tty_formatter(results)
        else:
            results = pipe_formatter(results)

        all_filenames = SearchResults()

        for res in results:
            if res.filename:
                all_filenames.add_result(res.filename, res.line_num)

        return all_filenames

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
