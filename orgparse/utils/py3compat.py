import sys

PY3 = (sys.version_info[0] >= 3)

if PY3:
    basestring = unicode = str
else:
    unicode = unicode
    basestring = basestring

if PY3:
    from ._py3compat import execfile
else:
    execfile = execfile
