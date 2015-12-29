from __future__ import unicode_literals, print_function
import re
import sys
from collections import OrderedDict
from afind.adapters._base import AdapterBase, ParseResult


class AdapterAg(AdapterBase):
    cmd_usage = 'ag --help'

    # params specefic for ag utility
    CUSTOM_PARAMS = OrderedDict([
        ('-nG',    {'args_count': 1, 'description': 'PATTERN Limit search to filenames NOT matching PATTERN'}),
    ])

    # 160:                 line_data - before/after lines
    # 160;17 7:            line_data - with one match in line
    # 175;10 8,23 8:       line_data - with several matches in one line
    MATCH_STR_RE = re.compile(r'^(\d+)(?:;(\d+[ ]\d+(?:,\d+[ ]\d+)*))?:(.*)$')

    def get_results(self, adapter_params, afind_params):
        self.run_params = ['ag', '--ackmate'] + adapter_params
        self.actions_pre(afind_params)
        self.cmd_search = self._join_args(self.run_params)

        current_filename = ''

        for line in self._get_cmd_output(self.cmd_search):
            # file content finished
            if not line:
                current_filename = ''
                yield ParseResult(is_file_finished=True)

            # is filename
            elif line.startswith(':'):
                current_filename = line[1:]
                yield ParseResult(filename=current_filename, is_title=True)

            # is group delimiter
            elif line.strip() == '--':
                yield ParseResult(is_group_delimiter=True)

            # file content
            else:
                parsed = self.MATCH_STR_RE.match(line)

                if not parsed:
                    sys.stderr.write('@afind parse-error: ' + line + '\n')
                    continue

                line_num, line_cols, line_text = parsed.groups()
                if line_cols:
                    line_cols = [map(int, c.split(' ')) for c in line_cols.split(',')]
                else:
                    line_cols = []

                yield ParseResult(
                    filename=current_filename,
                    line_text=line_text,
                    line_num=line_num,
                    line_cols=line_cols,
                )

        self.actions_post(afind_params)

    def actions_pre(self, afind_params):
        nG = afind_params.get('-nG', None)
        if nG:
            self.run_params += ['-G', self._rxno(nG[0])]

    def actions_post(self, afind_params):
        pass

    def _rxno(self, *patterns):
        """
        Return regexp means that line does't containt patterns
        """
        patterns = r'|'.join(patterns)
        patterns = r"'^((?!" + patterns + r").)*$'"
        return patterns

Adapter = AdapterAg
