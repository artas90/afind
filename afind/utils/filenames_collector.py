import os
import sys
from collections import OrderedDict


class FilenamesCollector(object):
    '''
    Collect matched filenames with linenumbers
    eg:
    {
        'filename.js': [12, 23],
        'filename.css': [77, 160],
    }
    '''

    def __init__(self, results_stream):
        self._results_stream = results_stream
        self._filenames = OrderedDict()

    def __iter__(self):
        for res in self._results_stream:

            if res.filename:
                self._filenames.setdefault(res.filename, [])

                if res.line_num:
                    self._filenames[res.filename].append(res.line_num)

            yield res

    def get_filenames(self, only_first_line=False):
        result = ''

        for filename in self._filenames.keys():
            line_numbers = self._filenames[filename]

            if line_numbers:
                line_numbers = line_numbers[:1] if only_first_line else line_numbers
                result += ' '.join('{}:{}'.format(filename, ln) for ln in line_numbers)
            else:
                result += filename

            result += ' '

        return result.strip()

    def onen_in_editor(self, editor_title, editor_cmd):
        """
        :param: editor_title - string
        :param: editor_cmd   - string
        :param: filenames    - SearchResults instance
        """

        if not self._filenames:
            return

        if len(self._filenames) > 15:
            msg = '\nDo you want to open {} files? [y/n]: '.format(len(self._filenames))
            if raw_input(msg).strip().lower() != 'y':
                return

        files = self.get_filenames(only_first_line=True)

        sys.stdout.write('@afind open: {}...\n'.format(editor_title))
        cmd = "echo {} | xargs {}".format(files, editor_cmd)
        os.system(cmd)
        
