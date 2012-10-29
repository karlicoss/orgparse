"""
Python 3 compatibility code which is loaded only when from Python 3.
"""


def execfile(filename, *args):
    return exec(
        compile(open(filename).read(), filename, 'exec'),
        *args)
