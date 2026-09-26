"""Check concrete table contents and names in the pinned upstream corpus.

Load complete Org documents through the public API.
Expected values come from the source files, including tables embedded in larger documents.
"""

from pathlib import Path

import pytest

from ... import OrgRootNode, load
from ...extra import Table

CORPUS = Path(__file__).resolve().parents[4] / 'testdata' / 'external'
ORG_EXAMPLES = CORPUS / 'org-mode' / 'testing' / 'examples'


@pytest.fixture(scope='module')
def sachac() -> OrgRootNode:
    return load(CORPUS / 'sachac' / 'Sacha.org')


@pytest.mark.parametrize(
    ('filename', 'heading', 'expected_tables'),
    [
        (
            'ob-maxima-test.org',
            'Table input',
            [
                ('test_tbl_col', [['1.0'], ['2.0']]),
                ('test_tbl_row', [['1.0', '2.0']]),
                ('test_tbl_mtr', [['1.0', '1.0']]),
            ],
        ),
        (
            'ob-fortran-test.org',
            'matrix',
            [
                ('fortran-input-matrix1', [['0.0', '42.0'], ['0.0', '0.0'], ['0.0', '0.0']]),
                ('fortran-input-matrix2', [['0.0', '0.0', '0.0'], ['0.0', '0.0', '42.0']]),
            ],
        ),
    ],
    ids=['maxima', 'fortran'],
)
def test_org_named_matrices(*, filename: str, heading: str, expected_tables: list[tuple[str, list[list[str]]]]) -> None:
    """Distinguish named tables in one heading, preserving their shapes and numeric text."""
    root = load(ORG_EXAMPLES / filename)
    [node] = [node for node in root[1:] if node.heading == heading]
    tables = [part for part in node.body_rich if isinstance(part, Table)]
    assert [table.name for table in tables] == [name for name, _ in expected_tables]
    for table, (_, rows) in zip(tables, expected_tables, strict=True):
        assert list(table.rows) == rows
        assert list(table.blocks) == [rows]


def test_org_captioned_table() -> None:
    """Associate an uppercase NAME and preceding caption with a single-cell table."""
    root = load(ORG_EXAMPLES / 'include.org')
    [node] = [node for node in root[1:] if node.get_property('CUSTOM_ID') == 'ht']
    [table] = [part for part in node.body_rich if isinstance(part, Table)]
    assert table.name == 'tbl'
    assert list(table) == [['1']]
    assert list(table.blocks) == [[['1']]]


def test_org_heterogeneous_table() -> None:
    """Read indented rows with text and numbers, using the header for dictionary keys."""
    root = load(ORG_EXAMPLES / 'ob-C-test.org')
    [node] = [node for node in root[1:] if node.heading == 'Inhomogeneous table']
    [table] = [part for part in node.body_rich if isinstance(part, Table)]
    assert table.name == 'tinomogen'
    assert table.as_dicts.columns == ['day', 'quty']
    assert list(table.as_dicts) == [
        {'day': 'monday',    'quty': '34'},
        {'day': 'tuesday',   'quty': '41'},
        {'day': 'wednesday', 'quty': '56'},
        {'day': 'thursday',  'quty': '17'},
        {'day': 'friday',    'quty': '12'},
        {'day': 'saturday',  'quty': '7'},
        {'day': 'sunday',    'quty': '4'},
    ]  # fmt: skip


def test_org_multiple_blocks() -> None:
    """Preserve separator-delimited sections and refuse ambiguous dictionary conversion."""
    root = load(ORG_EXAMPLES / 'ob-header-arg-defaults.org')
    [node] = [node for node in root[1:] if node.heading == 'Overwrite']
    [table] = [part for part in node.body_rich if isinstance(part, Table)]
    assert table.name is None
    assert list(table.blocks) == [
        [
            ['Global',                 't1',  't2',  't3',  't4',  't5',  't6',  't7',  't8',  't9'],
        ],
        [
            ['header-args',            'gh1', 'gh2', '---', 'gh4', '---', '---', '---', '---', '---'],
            ['header-args:emacs-lisp', 'ge1', '---', '---', 'ge4', 'ge5', '---', '---', '---', '---'],
        ],
        [
            ['Tree',                   't1',  't2',  't3',  't4',  't5',  't6',  't7',  't8',  't9'],
        ],
        [
            ['header-args',            '---', '---', '---', '---', '---', '---', 'th7', '---', '---'],
            ['header-args:emacs-lisp', '---', '---', '---', '---', '---', '---', '---', 'te8', '---'],
        ],
        [
            ['Result #+CALL',          'ge1', 'gh2', '--3', 'ge4', 'ge5', '--6', 'th7', 'te8', '--9'],
            ['Result noweb',           '--1', '--2', '--3', '--4', '--5', '--6', 'th7', 'te8', '--9'],
        ],
    ]  # fmt: skip
    with pytest.raises(RuntimeError, match='Need two-block table'):
        list(table.as_dicts)


def test_sachac_lispy_bindings(sachac: OrgRootNode) -> None:
    """Read an indented named table inside a special block, including empty cells and punctuation keys."""
    [node] = [node for node in sachac[1:] if node.get_property('CUSTOM_ID') == 'hydra-lispy']
    [table] = [part for part in node.body_rich if isinstance(part, Table)]
    assert table.name == 'bindings'
    [header, data] = table.blocks
    assert header == [['key', 'function', 'column']]
    assert len(data) == 69
    records = list(table.as_dicts)
    assert records[0] == {'key': '<', 'function': 'lispy-barf', 'column': ''}
    assert records[-1] == {'key': 'm', 'function': 'lispy-mark-list', 'column': 'Other'}
    assert [row for row in records if row['key'] == '\\'] == [
        {'key': '\\', 'function': 'lispy-splice', 'column': 'Edit'},
    ]
    assert [row for row in records if row['key'] == '-'] == [
        {'key': '-', 'function': 'lispy-ace-subword', 'column': 'Nav'},
    ]


def test_sachac_unicode_and_links(sachac: OrgRootNode) -> None:
    """Keep accented headers and raw Org links when converting an unnamed table to dictionaries."""
    [node] = [node for node in sachac[1:] if node.heading == 'Fréquence des erreurs par catégorie']
    [table] = [part for part in node.body_rich if isinstance(part, Table)]
    assert table.name is None
    assert table.as_dicts.columns == ['Thématique (KwizIQ)', "Nombre d'erreurs"]
    records = list(table.as_dicts)
    assert len(records) == 7
    assert records[0] == {
        'Thématique (KwizIQ)': '[[https://french.kwiziq.com/revision/grammar/topics/nouns-articles][Nouns & Articles]]',
        "Nombre d'erreurs": '18',
    }
    assert records[-1] == {
        'Thématique (KwizIQ)': '[[https://french.kwiziq.com/revision/grammar/topics/numbers-time-date][Numbers, Time & Date]]',
        "Nombre d'erreurs": '8',
    }


def test_sachac_link_syntax(sachac: OrgRootNode) -> None:
    """Preserve inline code and several link syntaxes in a table without a header separator."""
    [node] = [
        node
        for node in sachac[1:]
        if node.heading == 'Adding Org Mode link awesomeness elsewhere: sacha-org-insert-link-dwim'
    ]
    [table] = [part for part in node.body_rich if isinstance(part, Table)]
    assert table.name is None
    rows = [
        ['HTML',       '~<a href="https://example.com">title</a>~'],
        ['Org',        '~[[https://example.com][title]]~'],
        ['Plain text', '~title https://example.com~'],
        ['Markdown',   '~[https://example.com](title)~'],
        ['Oddmuse',    '~[https://example.com title]~'],
    ]  # fmt: skip
    assert list(table.rows) == rows
    assert list(table.blocks) == [rows]
    with pytest.raises(RuntimeError, match='Need two-block table'):
        list(table.as_dicts)


def test_sachac_babel_results(sachac: OrgRootNode) -> None:
    """Read separate result tables in drawers without mistaking source/result labels for table names."""
    [node] = [
        node
        for node in sachac[1:]
        if node.heading == 'Emacs and whisper.el: Trying out different speech-to-text backends and models'
    ]
    [cpu, gpu] = [part for part in node.body_rich if isinstance(part, Table)]
    assert cpu.name is None
    assert gpu.name is None
    assert list(cpu.rows) == [
        ['3.694', 'parakeet'],
        ['2.484', 'whisper.cpp base-q4_0'],
        ['1.547', 'speaches whisper-base'],
        ['1.425', 'speaches whisper-base.en'],
        ['4.076', 'speaches whisper-small'],
        ['3.735', 'speaches whisper-small.en'],
        ['2.870', 'speaches lorneluo/whisper-small-ct2-int8'],
        ['4.537', 'whisperx-server Systran/faster-whisper-small'],
    ]
    assert list(gpu.rows) == [
        ['0.596', 'speaches whisper-tiny'],
        ['0.940', 'speaches whisper-base'],
        ['2.909', 'speaches whisper-small'],
        ['8.740', 'speaches whisper-medium'],
    ]
