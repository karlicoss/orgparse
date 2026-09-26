'''
Tests for rich formatting: tables etc.
'''

import pytest

from .. import loads
from ..extra import Table


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

    [_gap1, t1, _gap2, t2, _gap3, t3, _gap4] = root.body_rich

    t1 = Table(root._lines[1:10])
    t2 = Table(root._lines[11:19])
    t3 = Table(root._lines[22:26])

    assert t1.name is None
    assert ilen(t1.blocks) == 4
    assert list(t1.blocks)[2] == []
    assert ilen(t1.rows) == 6

    with pytest.raises(RuntimeError):
        list(t1.as_dicts)  # not sure what should it be

    assert ilen(t2.blocks) == 2
    assert ilen(t2.rows) == 5
    assert list(t2.rows)[3] == ['[2020-11-05 Thu 23:44]', '']

    assert ilen(t3.blocks) == 2
    assert list(t3.rows) == [['simple'], ['value1'], ['value2']]
    assert t3.as_dicts.columns == ['simple']
    assert list(t3.as_dicts) == [{'simple': 'value1'}, {'simple': 'value2'}]


def test_table_2() -> None:
    root = loads('''
* item

#+tblname: something
| date                 | value | comment                       |
|----------------------+-------+-------------------------------|
| 14.04.17             |  11   | aaaa                          |
| May 26 2017 08:00    |  12   | what + about + pluses?        |
| May 26 09:00 - 10:00 |  13   | time is                       |

    some comment

#+BEGIN_SRC python :var fname="plot.png" :var table=something :results file
fig.savefig(fname)
return fname
#+END_SRC

#+RESULTS:
[[file:plot.png]]
''')
    [_, t, _] = root.children[0].body_rich
    assert isinstance(t, Table)
    assert t.name == 'something'
    assert ilen(t.as_dicts) == 3


def test_named_table() -> None:
    """Expose the table name requested in https://github.com/karlicoss/orgparse/issues/34."""
    root = loads('''
#+caption: Some caption for a table
#+name: tabname
| x | y |
|---+---|
| 1 | 2 |
''')
    [table] = [part for part in root.body_rich if isinstance(part, Table)]
    assert table.name == 'tabname'
    assert list(table.rows) == [['x', 'y'], ['1', '2']]
    assert list(table.as_dicts) == [{'x': '1', 'y': '2'}]
    assert '#+name: tabname' in root.get_body(format='raw')


@pytest.mark.parametrize(
    ('metadata', 'expected_name'),
    [
        ('', None),
        ('  #+NaMe:\t Mixed.Name \t\n', 'Mixed.Name'),
        ('#+NAME:\n', ''),
        ('#+NAME: first\n#+NAME: last\n', 'last'),
        (
            '#+NAME: data\n#+CAPTION[short]: A longer caption\n#+ATTR_HTML: :border 2\n#+PLOT: title:"Data"\n',
            'data',
        ),
        ('#+NAME: data\n#+HEADER: :results table\n#+RESULTS[hash]: source\n', 'data'),
        ('#+NAME: data\n\n', None),
        ('#+NAME: data\n \t\n', None),
        ('#+NAME: data\nSome intervening text\n', None),
        ('#+NAME: data\n# A comment\n', None),
        ('#+NAME: data\n#+TITLE: A different keyword\n', None),
        ('#+NAME: data\n#+NAME[invalid]: other\n', None),
        ('#+NAME: data\n#+BEGIN_SRC python\nprint(1)\n#+END_SRC\n', None),
    ],
)
def test_table_name_affiliation(metadata: str, expected_name: str | None) -> None:
    root = loads(metadata + '  | value |\n')
    [table] = [part for part in root.body_rich if isinstance(part, Table)]
    assert table.name == expected_name
    assert list(table.rows) == [['value']]


def test_table_names_are_local() -> None:
    """Keep each name on its own table, without leaking across tables or headings."""
    root = loads('''
#+NAME: first
| 1 |

| 2 |
#+NAME: third
| 3 |
* Heading
| 4 |
#+NAME: fifth
| 5 |
''')
    tables = [part for part in root.body_rich if isinstance(part, Table)]
    assert [table.name for table in tables] == ['first', None, 'third']
    child_tables = [part for part in root.children[0].body_rich if isinstance(part, Table)]
    assert [table.name for table in child_tables] == [None, 'fifth']


def ilen(x) -> int:
    return len(list(x))
