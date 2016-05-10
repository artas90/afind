from __future__ import unicode_literals, print_function
import os
import sys
from collections import OrderedDict
from afind.utils.filenames_collector import FilenamesCollector
from afind.utils.result_formatters import TtyFormatter, PipeFormatter, PatchFormatter
from afind.backends.ag import BackendParser


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
        self.parser = BackendParser()
        self.custom_params = OrderedDict()
        self.custom_params.update(self.parser.CUSTOM_PARAMS)
        self.custom_params.update(self.CUSTOM_PARAMS)

    def run(self):
        self.parser_params, self.afind_params = self.split_argv()

        show_usage = False

        if  ('-h' in self.parser_params) or ('--help' in self.parser_params):
            show_usage = True
        elif '--apply-patch' in self.afind_params:
            show_usage = False
        elif not self.parser_params:
            show_usage = True

        if show_usage:
            success = self.parser.print_usage()
            if success:
                self.add_afind_usage()
            return

        if '--apply-patch' in self.afind_params:
            self._run_patch_apply()
        else:
            self._run_search()

    def _run_search(self):
        self.actions_pre()

        results_stream = self.parser.get_results(self.parser_params, self.afind_params)
        formatter = self._get_output_formatter(results_stream)
        self.filenames_collector = FilenamesCollector(formatter)

        # Run stream
        for _ in self.filenames_collector: pass

        if '--afind-dbg' in self.afind_params:
            sys.stdout.write('\n@afind cmd: ' + self.parser.cmd_search + '\n')

        self.actions_post()

    def _run_patch_apply(self):
        cmd = 'patch --unified --strip=1 --force --input ' + self.afind_params['--apply-patch'][0]
        os.system(cmd)

    def _get_output_formatter(self, results_stream):
        if '--make-patch' in self.afind_params:
            return PatchFormatter(results_stream)
        elif sys.stdout.isatty() or ('--force-colors' in self.afind_params):
            return TtyFormatter(results_stream)
        else:
            return PipeFormatter(results_stream)

    def split_argv(self):
        all_args = sys.argv[1:]
        ag_args = []

        # Means that next N params will be used by afind
        afind_curr_param = ''
        afind_args_count = 0

        parser_params = []
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
                parser_params.append(param_name)

        for param_name in afind_params:
            args_count = self.custom_params[param_name]['args_count']

            if len(afind_params[param_name]) < args_count:
                err = b"Error: Parameter {} requires {} following arguments\n".format(param_name, args_count)
                sys.stderr.write(err)
                sys.exit(1)

        return parser_params, afind_params

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
        editor_title = ''
        editor_cmd = ''

        if '--subl' in self.afind_params:
            editor_title = 'SublimeText'
            editor_cmd = 'subl'

        elif '--atom' in self.afind_params:
            editor_title = 'Atom.io'
            editor_cmd = 'atom'

        if editor_title and editor_cmd:
            self.filenames_collector.onen_in_editor(editor_title, editor_cmd)
