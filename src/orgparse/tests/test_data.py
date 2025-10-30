import pickle
from collections.abc import Iterator
from pathlib import Path

import pytest

from .. import load, loads

DATADIR = Path(__file__).parent / 'data'


def load_data(path: Path):
    """Load data from python file"""
    ns = {}  # type: ignore[var-annotated]
    # read_bytes() and compile hackery to avoid encoding issues (e.g. see 05_tags)
    exec(compile(path.read_bytes(), path, 'exec'), ns)
    return ns['data']


def value_from_data_key(node, key):
    """
    Helper function for check_data. Get value from Orgnode by key.
    """
    if key == 'tags_inher':
        return node.tags
    elif key == 'children_heading':
        return [c.heading for c in node.children]
    elif key in (
        'parent_heading',
        'previous_same_level_heading',
        'next_same_level_heading',
    ):
        othernode = getattr(node, key.rsplit('_', 1)[0])
        if othernode and not othernode.is_root():
            return othernode.heading
        else:
            return None
    else:
        return getattr(node, key)


def data_path(dataname: str, ext: str) -> Path:
    return DATADIR / f'{dataname}.{ext}'


def get_datanames() -> Iterator[str]:
    for oname in sorted(DATADIR.glob('*.org')):
        yield oname.stem


@pytest.mark.parametrize('dataname', get_datanames())
def test_data(dataname):
    """
    Compare parsed data from 'data/*.org' and its correct answer 'data/*.py'
    """
    oname = data_path(dataname, "org")
    data = load_data(data_path(dataname, "py"))
    root = load(oname)

    for i, (node, kwds) in enumerate(zip(root[1:], data)):
        for key in kwds:
            val = value_from_data_key(node, key)
            assert kwds[key] == val, (
                f'check value of {i}-th node of key "{key}" from "{dataname}".\n\nParsed:\n{val}\n\nReal:\n{kwds[key]}'
            )
            assert type(kwds[key]) == type(val), (  # noqa: E721
                f'check type of {i}-th node of key "{key}" from "{dataname}".\n\nParsed:\n{type(val)}\n\nReal:\n{type(kwds[key])}'
            )

    assert root.env.filename == str(oname)


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


def test_commented_headings_do_not_appear_as_children():
    root = loads("""\
* H1
#** H2
** H3
#* H4
#** H5
* H6
""")
    assert root.linenumber == 1
    top_level = root.children
    assert len(top_level) == 2

    h1 = top_level[0]
    assert h1.heading == "H1"
    assert h1.get_body() == "#** H2"
    assert h1.linenumber == 1

    [h3] = h1.children
    assert h3.heading == "H3"
    assert h3.get_body() == "#* H4\n#** H5"
    assert h3.linenumber == 3

    h6 = top_level[1]
    assert h6.heading == "H6"
    assert len(h6.children) == 0
    assert h6.linenumber == 6


def test_commented_clock_entries_are_ignored_by_node_clock():
    root = loads("""\
* Heading
# * Floss
# SCHEDULED: <2019-06-22 Sat 08:30 .+1w>
# :LOGBOOK:
# CLOCK: [2019-06-04 Tue 16:00]--[2019-06-04 Tue 17:00] =>  1:00
# :END:
""")
    [node] = root.children[0]
    assert node.heading == "Heading"
    assert node.clock == []


def test_commented_scheduled_marker_is_ignored_by_node_scheduled():
    root = loads("""\
* Heading
# SCHEDULED: <2019-06-22 Sat 08:30 .+1w>
""")
    [node] = root.children[0]
    assert node.heading == "Heading"
    assert node.scheduled.start is None


def test_commented_property_is_ignored_by_node_get_property():
    root = loads("""\
* Heading
# :PROPERTIES:
# :PROPER-TEA: backup
# :END:
""")
    [node] = root.children[0]
    assert node.heading == "Heading"
    assert node.get_property("PROPER-TEA") is None
