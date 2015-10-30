from __future__ import unicode_literals, print_function
import sys
from os import path as p
from importlib import import_module

sys.path.append(p.dirname(p.dirname(p.abspath(__file__))))
import_module('afind.entry_point').main()
