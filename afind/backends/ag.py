from __future__ import unicode_literals, print_function
import re
import sys
from collections import OrderedDict
from afind.backends._base import ParserBase, ParseResult 
from afind.utils.term_colors import TermColors
from afind.utils.result_formatters import FormatterBase


class AgParser(ParserBase):
    cmd_usage = 'ag --help'

    # params specefic for ag utility
    CUSTOM_PARAMS = OrderedDict([
        ('-nG',    {'args_count': 1, 'description': 'PATTERN Limit search to filenames NOT matching PATTERN'}),
    ])

    # 160:                 line_data - before/after lines
    # 160;17 7:            line_data - with one match in line
    # 175;10 8,23 8:       line_data - with several matches in one line
    MATCH_STR_RE = re.compile(r'^(\d+)(?:;(\d+[ ]\d+(?:,\d+[ ]\d+)*))?:(.*)$')

    def get_results(self, parser_params, afind_params):
        self.run_params = ['ag', '--ackmate'] + parser_params
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

        yield ParseResult(is_results_finished=True)

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

BackendParser = AgParser


class AgDefaultColors(object):
    RESET    = TermColors.RESET
    FILENAME = TermColors.make_flags(TermColors.green,  bold=True)
    LINENUM  = TermColors.make_flags(TermColors.yellow, bold=True)
    MATCH    = TermColors.make_flags(TermColors.black,  bg=TermColors.yellow)


class AgFormatter(FormatterBase):
    DefaultColors = AgDefaultColors

    def __iter__(self):
        c = self._colors

        for res in self._results_stream:
            if res.is_file_finished:
                sys.stdout.write(b'\n')

            elif res.is_title:
                sys.stdout.write(c.FILENAME + res.filename.encode('utf-8') + c.RESET + b'\n')

            elif res.is_group_delimiter:
                sys.stdout.write(b'--\n')

            elif res.line_text is not None:
                suffix = b':' if res.line_cols else b'-'
                sys.stdout.write(c.LINENUM + res.line_num.encode('utf-8') + suffix + c.RESET)

                line_text = res.line_text.encode('utf-8')
                cursor = 0
                for start, length in res.line_cols:
                    end = start + length
                    sys.stdout.write(line_text[cursor:start])
                    sys.stdout.write(c.MATCH + line_text[start:end] + c.RESET)
                    cursor = end
                sys.stdout.write(line_text[cursor:] + b'\n')

            yield res

BackendFormatter = AgFormatter
