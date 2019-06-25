import sys

def execfile(filename, *args):
    return exec(compile(open(filename).read(), filename, 'exec'), *args)
