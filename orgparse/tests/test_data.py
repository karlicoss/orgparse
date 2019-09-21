import os
from glob import glob
import pickle

from .. import load, loads
from ..utils.py3compat import execfile, PY3

import pytest # type: ignore

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
        return node.tags
    elif key == 'children_heading':
        return [c.heading for c in node.children]
    elif key in ('parent_heading',
                 'previous_same_level_heading',
                 'next_same_level_heading',
                 ):
        othernode = getattr(node, key.rsplit('_', 1)[0])
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


@pytest.mark.parametrize('dataname', get_datanames())
def test_data(dataname):
    """
    Compare parsed data from 'data/*.org' and its correct answer 'data/*.py'
    """
    if dataname == '05_tags':
        if not PY3:
            # python2 is end of life, so not worth fixing properly
            pytest.skip('Ignoring test involving unicode')

    oname = data_path(dataname, "org")
    data = load_data(data_path(dataname, "py"))
    root = load(oname)

    for (i, (node, kwds)) in enumerate(zip(root[1:], data)):
        for key in kwds:
            val = value_from_data_key(node, key)
            assert kwds[key] == val, 'check value of {0}-th node of key "{1}" from "{2}".\n\nParsed:\n{3}\n\nReal:\n{4}'.format(i, key, dataname, val, kwds[key])

    assert root.env.filename == oname


@pytest.mark.parametrize('dataname', get_datanames())
def test_picklable(dataname):
    oname = data_path(dataname, "org")
    root = load(oname)
    pickle.dumps(root)



def test_iter_node():
    root = loads("""
* H1
** H2
*** H3
* H4
** H5
""")
    node = root[1]
    assert node.heading == 'H1'

    by_iter = [n.heading for n in node]
    assert by_iter == ['H1', 'H2', 'H3']
