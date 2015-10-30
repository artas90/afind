#!/usr/bin/env python
from __future__ import print_function, unicode_literals
import os


project_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    files = [
        'afind/utils/search_results.py',
        'afind/utils/term_colors.py',
        'afind/adapters/_base.py',
        'afind/adapters/ag.py',
        'afind/application.py',
        'afind/entry_point.py',
    ]

    outname = os.path.join(project_dir, 'dist', 'af.py')
    outfile = open(outname, 'w')

    outfile.writelines([
        '#!/usr/bin/env python\n',
        'from __future__ import print_function, unicode_literals\n',
        '\n',
    ])

    for filename in files:
        with open(filename) as f:
            lines = f.read().splitlines()
            lines = [
                '\n',
                '#-- {} {}\n'.format(filename, '-' * 20)
            ] + [
                (ln + '\n') for ln in lines
                if not ln.startswith('from afind.') and not ln.startswith('from __future__')
            ]

            outfile.writelines(lines)

    print('Created ' + outname)


if __name__ == '__main__':
    main()
