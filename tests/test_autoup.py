# test_autoup

import sys
from os.path import abspath, basename, dirname, getsize, split


print(dirname(dirname(abspath(__file__))))
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import os
import mock

from autoup import Autoup

@mock.patch('__builtin__.open')
@mock.patch('os.makedirs')
def test_scan(a, b):
    #d = os.makedirs('test_scan_dir')
    f = open('Cake.s01e02.mkv', 'w')
    print f
    x = Autoup().scan(dirname(abspath(__file__)))
    for z in x:
        print(z)



test_scan()