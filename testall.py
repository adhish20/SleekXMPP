#!/usr/bin/env python

import os
import sys
# This can be used when you are in a test environment and need to make paths right
sys.path=['/Users/jocke/Dropbox/06_dev/SleekXMPP']+sys.path

import logging
import unittest
import distutils.core


from glob import glob
from os.path import splitext, basename, join as pjoin


def run_tests(exlude=[], include=[]):
    """
    Find and run all tests in the tests/ directory.

    Excludes live tests (tests/live_*).
    """
    testfiles = ['tests.test_overall']
    exclude = ['__init__.py', 'test_overall.py']

    #find all testcases that is not part of the exclude list
    for t in glob(pjoin('tests', '*.py')):
        if True not in [t.endswith(ex) for ex in exclude]:
            if basename(t).startswith('test_'):
                testfiles.append('tests.%s' % splitext(basename(t))[0])

    testsToUse=[]
    if not(include==[]):
        # use only test that has any text include in them
        for match in include:
            for test in testfiles:
                if test.find(match)>-1:
                    # add the test'
                    # print "REMOVE "+match + " test " + test + "  " + str(test.find(match))
                    testsToUse.append(test)

    testfiles=testsToUse
    suites = []
    for file in testfiles:
        __import__(file)
        suites.append(sys.modules[file].suite)

    tests = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)

    # Disable logging output
    logging.basicConfig(level=100)
    logging.disable(100)
    #logging.basicConfig(level=1)
    #logging.disable(100)

    result = runner.run(tests)
    return result


# Add a 'test' command for setup.py

class TestCommand(distutils.core.Command):

    user_options = [ ]

    def initialize_options(self):
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def run(self):
        run_tests()


if __name__ == '__main__':
#    result = run_tests(include=['all'])
    result = run_tests(include=['323'])
#    result = run_tests(include=['323','325'])
#    result = run_tests(include=['325'])

    print("<tests %s ran='%s' errors='%s' fails='%s' success='%s' />" % (
        "xmlns='http//andyet.net/protocol/tests'",
        result.testsRun, len(result.errors),
        len(result.failures), result.wasSuccessful()))
