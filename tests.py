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


def afind(params='', sort_results=False, get_errors=False):
    cmd  = 'python ' + path('afind') + ' ' + params
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True, env=os.environ)
    out, err = proc.communicate()

    if get_errors:
        return err

    out = out.decode('utf-8')

    lines = out.splitlines()
    if sort_results:
        lines = list(sorted(lines))

    return lines


class TestAfind(unittest.TestCase):

    def test_01_search_simple(self):
        self.assertEqual(afind('func1 workdir'), [
            'workdir/file1.py:2:def func1():',
        ])

        self.assertEqual(afind('func1 workdir --force-colors'), [
            '\033[1;32mworkdir/file1.py\033[0m',
            '\033[1;33m2:\033[0mdef \033[30;43mfunc1\033[0m():',
        ])

    def test_02_search_with_context(self):
        self.assertEqual(afind('func1 workdir -B 1'), [
            'workdir/file1.py:1-',
            'workdir/file1.py:2:def func1():',
        ])

        self.assertEqual(afind('func1 workdir -A 1'), [
            'workdir/file1.py:2:def func1():',
            'workdir/file1.py:3-    pass',
        ])

        self.assertEqual(afind('func1 workdir -C 1 --force-colors'), [
            '\033[1;32mworkdir/file1.py\033[0m',
            '\033[1;33m1-\033[0m',
            '\033[1;33m2:\033[0mdef \033[30;43mfunc1\033[0m():',
            '\033[1;33m3-\033[0m    pass',
        ])

    def test_03_search_with_group_delimeter(self):
        self.assertEqual(afind('println workdir -C 1'), [
            'workdir/file2.scala:2-    def main(args: Array[String]) {',
            'workdir/file2.scala:3:        println("Hello, world!")',
            'workdir/file2.scala:4-        // empty line',
            'workdir/file2.scala:5:        println("Second print")',
            'workdir/file2.scala:6-        // three',
            '--',
            'workdir/file2.scala:8-        // lines',
            'workdir/file2.scala:9:        println("Third print")',
            'workdir/file2.scala:10-    }',
        ])

    def test_04_search_non_ascii(self):
        self.assertEqual(afind('deutschen workdir --force-colors'), [
            '\033[1;32mworkdir/file3-non-ascii.txt\033[0m',
            '\033[1;33m1:\033[0mDas Schriftzeichen \xdf ist ein Buchstabe' +
            ' des \033[30;43mdeutschen\033[0m Alphabets.'
        ])

        self.assertEqual(afind('Österreich workdir --force-colors'), [
            '\033[1;32mworkdir/file3-non-ascii.txt\033[0m',
            '\033[1;33m3:\033[0msowie \033[30;43m\xd6sterreich\033[0m als scharfes S bzw.'
        ])

    def test_05_search_with_space(self):
        self.assertEqual(afind("'def func1' workdir --force-colors"), [
            '\033[1;32mworkdir/file1.py\033[0m',
            '\033[1;33m2:\033[0m\033[30;43mdef func1\033[0m():',
        ])

    def test_06_exlude_files(self):
        self.assertEqual(afind('def workdir', sort_results=True), [
            'workdir/file1.py:2:def func1():',
            'workdir/file2.scala:2:    def main(args: Array[String]) {',
        ])
        self.assertEqual(afind('def workdir -nG scala', sort_results=True), [
            'workdir/file1.py:2:def func1():',
        ])

    def test_07_handle_decode_error(self):
        self.assertEqual(afind('line_with_special_chars workdir -A 1', get_errors=True), (
            b'@afind decode-error: 2;4 23:\xa9\xc0\xa9\xa4line_with_special_chars\n' +
            b'@afind decode-error: 3:\xa9\xa6      S0_background_app.png\n'
        ))

    def test_08_open_in_sublime(self):
        subl_out = path('workdir', 'bin', 'subl.out')
        os.system('rm -rf ' + subl_out)

        afind('def workdir --subl')

        filenames = list(sorted(open(subl_out).read().strip().split(' ')))
        self.assertEqual(filenames, [
            'workdir/file1.py:2',
            'workdir/file2.scala:2',
        ])

        os.system('rm -rf ' + subl_out)

    def test_09_open_in_atom(self):
        atom_out = path('workdir', 'bin', 'atom.out')
        os.system('rm -rf ' + atom_out)

        afind('def workdir --atom')

        filenames = list(sorted(open(atom_out).read().strip().split(' ')))
        self.assertEqual(filenames, [
            'workdir/file1.py:2',
            'workdir/file2.scala:2',
        ])

        os.system('rm -rf ' + atom_out)

    def test_10_generate_patch(self):

        # backend search utulity can output results in different order
        results = afind('def workdir -A 1 --make-patch')
        results = ' ' + '\n'.join(results).strip(' \n')
        results = ['--- a' + r for r in results.split('--- a')[1:]]
        results = ''.join(sorted(results)).splitlines()

        self.assertEqual(results, [
            '--- a/workdir/file1.py',
            '+++ b/workdir/file1.py',
            '@@ -2,2 +2,2 @@',
            '-def func1():',
            '+def func1():',
            '     pass',
            '--- a/workdir/file2.scala',
            '+++ b/workdir/file2.scala',
            '@@ -2,2 +2,2 @@',
            '-    def main(args: Array[String]) {',
            '+    def main(args: Array[String]) {',
            '         println("Hello, world!")',
        ])

        self.assertEqual(afind('println workdir -C 1 --make-patch'), [
            '--- a/workdir/file2.scala',
            '+++ b/workdir/file2.scala',
            '@@ -2,5 +2,5 @@',
            '     def main(args: Array[String]) {',
            '-        println("Hello, world!")',
            '+        println("Hello, world!")',
            '         // empty line',
            '-        println("Second print")',
            '+        println("Second print")',
            '         // three',
            '@@ -8,3 +8,3 @@',
            '         // lines',
            '-        println("Third print")',
            '+        println("Third print")',
            '     }',
        ])

    def test_11_apply_patch(self):

        # example case if we need to change several translations
        for lang in ['en', 'de']:
            filename = path('workdir', 'lang-' + lang + '.json')

            with open(filename, 'w') as target_file:
                target_file.writelines([
                    '{\n',
                    '    "network_unavalable": "Network is unavalable"\n',
                    '}\n',
                ])

        with open(path('workdir', 'test_apply_patch.patch'), 'w') as patchfile:
            patch_data = [
                '--- a/workdir/lang-en.json',
                '+++ b/workdir/lang-en.json',
                '@@ -2,1 +2,1 @@',
                '-    "network_unavalable": "Network is unavalable"',
                '+    "network_unavalable": "Sorry, network is unavalable"',
                '--- a/workdir/lang-de.json',
                '+++ b/workdir/lang-de.json',
                '@@ -2,1 +2,1 @@',
                '-    "network_unavalable": "Network is unavalable"',
                '+    "network_unavalable": "Entschuldigung, Netzwerk nicht verfügbar ist"',
                '',
            ]

            patchfile.write('\n'.join(patch_data).encode('utf-8'))

        self.assertEqual(afind('--apply-patch ' + path('workdir', 'test_apply_patch.patch')), [
            'patching file workdir/lang-en.json',
            'patching file workdir/lang-de.json',
        ])

        os.system('rm -rf ' + path('workdir', 'test_apply_patch.patch'))

        self.assertEqual(afind('network_unavalable workdir', sort_results=True), [
            'workdir/lang-de.json:2:    "network_unavalable": "Entschuldigung, Netzwerk nicht verfügbar ist"',
            'workdir/lang-en.json:2:    "network_unavalable": "Sorry, network is unavalable"',
        ])

        for lang in ['en', 'de']:
            os.system('rm -rf ' + path('workdir', 'lang-' + lang + '.json'))



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
