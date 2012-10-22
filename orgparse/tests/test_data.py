import os
from glob import glob
import pickle
from nose.tools import eq_

from orgparse import load
from orgparse.py3compat import execfile


DATADIR = os.path.join(os.path.dirname(__file__), 'data')


def load_data(path):
    """Load data from python file"""
    ns = {}
    execfile(path, ns)
    return ns['data']


def value_from_data_key(node, key):
    """
    Helper function for check_data. Get value from Orgnode by key.
    """
    if key == 'tags_inher':
        return node.get_tags(inher=True)
    elif key == 'children_heading':
        return [c.heading for c in node.children]
    elif key in ('parent_heading',
                 'previous_heading',
                 'next_heading',
                 ):
        othernode = getattr(node, key.split('_', 1)[0])
        if othernode and not othernode.is_root():
            return othernode.heading
        else:
            return
    else:
        return getattr(node, key)


def data_path(dataname, ext):
    return os.path.join(DATADIR, '{0}.{1}'.format(dataname, ext))


def get_datanames():
    for oname in sorted(glob(os.path.join(DATADIR, '*.org'))):
        yield os.path.splitext(os.path.basename(oname))[0]


def check_data(dataname):
    """Helper function for test_data"""
    oname = data_path(dataname, "org")
    data = load_data(data_path(dataname, "py"))
    root = load(oname)

    for (i, (node, kwds)) in enumerate(zip(
            root.traverse(include_self=False), data)):
        for key in kwds:
            val = value_from_data_key(node, key)
            eq_(kwds[key], val,
                msg=('check value of {0}-th node of key "{1}" from "{2}".'
                     '\n\nParsed:\n{3}\n\nReal:\n{4}'
                     ).format(i, key, dataname, val, kwds[key]))

    eq_(root.env.filename, oname)


def test_data():
    """
    Compare parsed data from 'data/*.org' and its correct answer 'data/*.py'
    """
    for dataname in get_datanames():
        yield (check_data, dataname)


def check_picklable(dataname):
    oname = data_path(dataname, "org")
    root = load(oname)
    pickle.dumps(root)


def test_picklable():
    for dataname in get_datanames():
        yield (check_picklable, dataname)
