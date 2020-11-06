'''
Tests for rich formatting: tables etc.
'''
from .. import load, loads
from ..extra import Table

import pytest # type: ignore


def test_table() -> None:
    root = loads('''
|       |           |     |
|       | "heading" |     |
|       |           |     |
|-------+-----------+-----|
| reiwf | fef       |     |
|-------+-----------+-----|
|-------+-----------+-----|
| aba   | caba      | 123 |
| yeah  |           |   X |

    |------------------------+-------|
    | when                   | count |
    | datetime               | int   |
    |------------------------+-------|
    |                        | -1    |
    | [2020-11-05 Thu 23:44] |       |
    | [2020-11-06 Fri 01:00] | 1     |
    |------------------------+-------|

some irrelevant text

| simple |
|--------|
| value1 |
| value2 |
    ''')

    # FIXME need to parse properly
    t1 = Table(root._lines[1:10])
    t2 = Table(root._lines[11:19])
    t3 = Table(root._lines[22:26])

    assert ilen(t1.blocks) == 4
    assert list(t1.blocks)[2] == []
    assert ilen(t1.rows) == 6

    with pytest.raises(RuntimeError):
        list(t1.as_dicts) # not sure what should it be

    assert ilen(t2.blocks) == 2
    assert ilen(t2.rows) == 5
    assert list(t2.rows)[3] == ['[2020-11-05 Thu 23:44]', '']


    assert ilen(t3.blocks) == 2
    assert list(t3.rows) == [['simple'], ['value1'], ['value2']]
    assert t3.as_dicts.columns == ['simple']
    assert list(t3.as_dicts) == [{'simple': 'value1'}, {'simple': 'value2'}]


def ilen(x) -> int:
    return len(list(x))
