from collections import OrderedDict


class SearchResults(OrderedDict):
    '''
    Stores matched filenames with linenumbers
    eg:
    {
        'filename.js': [12, 23],
        'filename.css': [77, 160],
    }
    '''

    def add_result(self, filename, linenum=None):
        self.setdefault(filename, [])
        if linenum:
            self[filename].append(linenum)

    def get_filenames(self, only_first_line=False):
        result = ''

        for filename in self.keys():
            line_numbers = self[filename]

            if line_numbers:
                line_numbers = line_numbers[:1] if only_first_line else line_numbers
                result += ' '.join('{}:{}'.format(filename, ln) for ln in line_numbers)
            else:
                result += filename

            result += ' '

        return result.strip()
