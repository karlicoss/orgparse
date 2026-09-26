from pathlib import Path

import pytest

from .. import load, loadi, loads


def test_entry_line_ranges() -> None:
    root = loads('''\
Preamble
#+TITLE: Example

* TODO Parent
SCHEDULED: <2026-01-02 Fri>
:PROPERTIES:
:ID: parent
:END:
Body
#* Commented heading

** Child
Child body

*** Grandchild
* Sibling
body

''')
    assert [(node.linenumber, node.end_linenumber) for node in root] == [
        (1, 3),
        (4, 11),
        (12, 14),
        (15, 15),
        (16, 18),
    ]
    assert root[1][-1].end_linenumber == 15
    assert root[-1].end_linenumber == 18


@pytest.mark.parametrize(
    ('content', 'expected_end'),
    [
        ('* Last', 1),
        ('* Last\n', 1),
        ('* Last\n\n', 2),
        ('* Last\nbody', 2),
        ('* Last\nbody\n', 2),
        ('* Last\nbody\n\n', 3),
        ('* Last\r\nbody\r\n\r\n', 3),
    ],
)
def test_final_entry_end_linenumber(content: str, expected_end: int, tmp_path: Path) -> None:
    path = tmp_path / 'input.org'
    path.write_bytes(content.encode('utf-8'))
    for root in (loads(content), loadi(content.splitlines()), load(path)):
        [node] = root.children
        assert node.linenumber == 1
        assert node.end_linenumber == expected_end


@pytest.mark.parametrize(
    ('content', 'expected_end'),
    [
        ('', 0),
        ('\n', 1),
        ('Preamble', 1),
        ('Preamble\n\n', 2),
        ('* Heading', 0),
        ('Preamble\n* Heading', 1),
    ],
)
def test_preamble_end_linenumber(content: str, expected_end: int) -> None:
    root = loads(content)
    assert root.linenumber == 1
    assert root.end_linenumber == expected_end
