# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
import re
import sys
import unittest
from itertools import chain
from subprocess import Popen, PIPE


project_dir = os.path.dirname(os.path.abspath(__file__))
path = lambda *parts: os.path.join(project_dir, *parts)


def afind(params='', clean=True, sort_results=False, get_errors=False):
    cmd  = 'python ' + path('afind') + ' ' + params
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, env=os.environ)
    out, err = proc.communicate()

    if get_errors:
        return err

    if clean:
        out = re.sub(r'\033\[[0-9;]+m', '', out)

    out = out.decode('utf-8')

    lines = out.splitlines()
    if sort_results:
        lines = list(sorted(lines))

    return lines


class TestAfind(unittest.TestCase):

    def test_01_search_simple(self):
        self.assertEqual(afind('func1 workdir', clean=False), [
            'workdir/file1.py:2:def func1():',
        ])

        self.assertEqual(afind('func1 workdir --force-colors', clean=False), [
            '\033[1;32mworkdir/file1.py\033[0m',
            '\033[1;33m2:\033[0mdef \033[30;43mfunc1\033[0m():',
        ])

        self.assertEqual(afind('func1 workdir -A 1 --force-colors', clean=False), [
            '\033[1;32mworkdir/file1.py\033[0m',
            '\033[1;33m2:\033[0mdef \033[30;43mfunc1\033[0m():',
            '\033[1;33m3:\033[0m    pass',
        ])

    def test_02_search_non_ascii(self):
        self.assertEqual(afind('deutschen workdir --force-colors', clean=False), [
            '\033[1;32mworkdir/file3-non-ascii.txt\033[0m',
            '\033[1;33m1:\033[0mDas Schriftzeichen \xdf ist ein Buchstabe' +
            ' des \033[30;43mdeutschen\033[0m Alphabets.'
        ])

        self.assertEqual(afind('Österreich workdir --force-colors', clean=False), [
            '\033[1;32mworkdir/file3-non-ascii.txt\033[0m',
            '\033[1;33m3:\033[0msowie \033[30;43m\xd6sterreich\033[0m als scharfes S bzw.'
        ])

    def test_03_search_with_space(self):
        self.assertEqual(afind("'def func1' workdir --force-colors", clean=False), [
            '\033[1;32mworkdir/file1.py\033[0m',
            '\033[1;33m2:\033[0m\033[30;43mdef func1\033[0m():',
        ])

    def test_04_exlude_files(self):
        self.assertEqual(afind('def workdir', sort_results=True), [
            'workdir/file1.py:2:def func1():',
            'workdir/file2.scala:2:    def main(args: Array[String]) {',
        ])
        self.assertEqual(afind('def workdir -nG scala', sort_results=True), [
            'workdir/file1.py:2:def func1():',
        ])

    def test_05_handle_decode_error(self):
        self.assertEqual(afind('line_with_special_chars workdir -A 1', get_errors=True), (
            b'@afind decode-error: 2;4 23:\xa9\xc0\xa9\xa4line_with_special_chars\n' +
            b'@afind decode-error: 3:\xa9\xa6      S0_background_app.png\n'
        ))

    def test_06_open_in_sublime(self):
        subl_out = path('workdir', 'bin', 'subl.out')
        os.system('rm -rf ' + subl_out)

        afind('def workdir --subl')

        filenames = list(sorted(open(subl_out).read().strip().split(' ')))
        self.assertEqual(filenames, [
            'workdir/file1.py:2',
            'workdir/file2.scala:2',
        ])

        os.system('rm -rf ' + subl_out)

    def test_07_open_in_atom(self):
        atom_out = path('workdir', 'bin', 'atom.out')
        os.system('rm -rf ' + atom_out)

        afind('def workdir --atom')

        filenames = list(sorted(open(atom_out).read().strip().split(' ')))
        self.assertEqual(filenames, [
            'workdir/file1.py:2',
            'workdir/file2.scala:2',
        ])

        os.system('rm -rf ' + atom_out)


class TestAfindAg(unittest.TestCase):

    def test_01_ag_no_params(self):
        result = afind()
        self.assertTrue(result[1].startswith('Usage: ag'))

    def test_02_ag_print_help(self):
        result = afind('-h')
        self.assertTrue(result[1].startswith('Usage: ag'))

        result = afind('--help')
        self.assertTrue(result[1].startswith('Usage: ag'))

    def test_03_ag_handle_stderr(self):
        err = afind('--wrong-param', get_errors=True)
        self.assertTrue('unrecognized option' in err)

        err = afind('def wrong-workdir', get_errors=True)
        self.assertTrue('No such file or directory' in err)


if __name__ == '__main__':
    os.environ['PATH'] = path('workdir', 'bin') + os.pathsep + os.environ['PATH']
    os.system('chmod +x ' + path('workdir', 'bin', 'subl'))
    os.system('chmod +x ' + path('workdir', 'bin', 'atom'))

    unittest.main(verbosity=2)
