import sys
from afind.utils.term_colors import TermColors


class DefaultColors(object):
    RESET    = TermColors.RESET
    FILENAME = TermColors.make_flags(TermColors.green,  bold=True)
    LINENUM  = TermColors.make_flags(TermColors.yellow, bold=True)
    MATCH    = TermColors.make_flags(TermColors.black,  bg=TermColors.yellow)



class FormatterBase(object):

    def __init__(self, results_stream, colors=None):
        self._results_stream = results_stream
        self._colors = colors or DefaultColors()


class TtyFormatter(FormatterBase):

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



class PipeFormatter(FormatterBase):

    def __iter__(self):
        current_filename = ''

        for res in self._results_stream:
            if res.is_file_finished:
                pass

            elif res.is_title:
                current_filename = res.filename.encode('utf-8')

            elif res.is_group_delimiter:
                sys.stdout.write(b'--\n')

            elif res.line_text is not None:
                prefix = b':' if res.line_cols else b'-'
                sys.stdout.write(current_filename + b':')
                sys.stdout.write(res.line_num.encode('utf-8') + prefix + res.line_text.encode('utf-8'))
                sys.stdout.write(b'\n')
            
            yield res



class PatchBlock(object):

    def __init__(self):
        self._results = []

    def add_result(self, result):
        self._results.append(result)

    def flush(self):
        if not self._results:
            return

        try:
            first_line = int(self._results[0].line_num)
            last_line = int(self._results[-1].line_num)
            context_count = last_line - first_line + 1
            sys.stdout.write(b'@@ -{0},{1} +{0},{1} @@\n'.format(first_line, context_count))

        except (IndexError, ValueError, TypeError) as e:
            sys.stderr.write(b'@@ WRONG BLOCK @@\n')
            self._results = []
            return

        for res in self._results:
            line_text = res.line_text.encode('utf-8')

            if res.line_cols: # lines with matches
                sys.stdout.write(b'-' + line_text + b'\n')
                sys.stdout.write(b'+' + line_text + b'\n')
            else: # context lines
                sys.stdout.write(b' ' + line_text + b'\n')

        self._results = []


class PatchFormatter(FormatterBase):

    def __iter__(self):
        current_filename = ''

        block = PatchBlock()

        for res in self._results_stream:
            if res.is_file_finished or res.is_group_delimiter or res.is_results_finished:
                block.flush()

            elif res.is_title:
                current_filename = res.filename.encode('utf-8')
                sys.stdout.write(b'--- a/' + current_filename + b'\n')
                sys.stdout.write(b'+++ b/' + current_filename + b'\n')

            elif res.line_text is not None:
                block.add_result(res)

            yield res

