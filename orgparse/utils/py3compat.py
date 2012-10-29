import sys

PY3 = (sys.version_info[0] >= 3)

try:
    # Python 2
    unicode = unicode
    basestring = basestring
except NameError:
    # Python 3
    basestring = unicode = str

PY3 = (sys.version_info[0] >= 3)

if PY3:
    from ._py3compat import execfile
else:
    execfile = execfile
