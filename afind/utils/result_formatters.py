import sys
from afind.utils.term_colors import TermColors


class c(object):
    RESET    = TermColors.RESET
    FILENAME = TermColors.make_flags(TermColors.green,  bold=True)
    LINENUM  = TermColors.make_flags(TermColors.yellow, bold=True)
    MATCH    = TermColors.make_flags(TermColors.black,  bg=TermColors.yellow)


def tty_formatter(results):

    for res in results:
        if res.is_file_finished:
            sys.stdout.write('\n')

        elif res.is_title:
            sys.stdout.write(c.FILENAME + res.filename.encode('utf-8') + c.RESET + b'\n')

        elif res.is_group_delimiter:
            sys.stdout.write('--\n')

        else:
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


def pipe_formatter(results):
    current_filename = ''

    for res in results:
        if res.is_file_finished:
            pass

        elif res.is_title:
            current_filename = res.filename.encode('utf-8')

        elif res.is_group_delimiter:
            sys.stdout.write('--\n')

        else:
            suffix = b':' if res.line_cols else b'-'
            sys.stdout.write(current_filename + b':')
            sys.stdout.write(res.line_num.encode('utf-8') + suffix + res.line_text.encode('utf-8'))
            sys.stdout.write(b'\n')
        
        yield res

