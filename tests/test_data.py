import os
from glob import glob
from nose.tools import eq_

from orgparse import load


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
        return [c.get_heading() for c in node.get_children()]
    elif key in ('parent_heading',
                 'previous_heading',
                 'next_heading',
                 ):
        othernode = getattr(node, 'get_{0}'.format(key.split('_', 1)[0]))()
        if othernode and not othernode.is_root():
            return othernode.get_heading()
        else:
            return
    else:
        return getattr(node, "get_{0}".format(key))()


def data_path(dataname, ext):
    return os.path.join(DATADIR, '{0}.{1}'.format(dataname, ext))


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
                msg=('check value of {0}-th node of key "{1}" from "{2}". '
                     'parsed = "{3}" != "{4}" = real.'
                     ).format(i, key, dataname, val, kwds[key]))


def test_data():
    """
    Compare parsed data from 'data/*.org' and its correct answer 'data/*.py'
    """
    for oname in sorted(glob(os.path.join(DATADIR, '*.org'))):
        dataname = os.path.splitext(os.path.basename(oname))[0]
        yield (check_data, dataname)
