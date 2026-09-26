"""Exercise the public parser API on Org mode's upstream example files."""

from pathlib import Path

import pytest

from .. import load
from ..extra import Table
from ..node import OrgNode

CORPUS = Path(__file__).resolve().parents[3] / 'testdata' / 'external' / 'org-mode' / 'testing' / 'examples'


def corpus_files() -> list[Path]:
    paths = sorted(CORPUS.rglob('*.org'))
    assert len(paths) > 0, 'Missing Org corpus: run git submodule update --init --recursive'
    return paths


@pytest.mark.parametrize('path', corpus_files(), ids=lambda path: path.relative_to(CORPUS).as_posix())
def test_corpus(path: Path) -> None:
    """Check parser robustness and tree consistency across upstream Org examples.

    Exercise heading/body formatting, property lookups, table row/block iteration,
        and formatting of populated timestamps.
    Check tag inclusion, parent/child links, a shared root, increasing heading line numbers,
        and heading levels against the source text.
    These are smoke and consistency checks; exact parsed values require separate expected-output tests.
    """
    root = load(path)
    lines = path.read_text(encoding='utf-8').splitlines()
    assert root.is_root()
    assert root.parent is None

    previous_line = 0
    for node in root:
        # Access lazy formatting as well as the eagerly parsed attributes.
        assert isinstance(node.heading, str)
        assert isinstance(node.body, str)
        assert node.shallow_tags <= node.tags
        for key, value in node.properties.items():
            assert node.get_property(key) == value
        for part in node.body_rich:
            if isinstance(part, Table):
                list(part.rows)
                list(part.blocks)

        dates = node.get_timestamps(active=True, inactive=True)
        if isinstance(node, OrgNode):
            dates = [*dates, node.scheduled, node.deadline, node.closed, *node.clock, *node.repeated_tasks]
        for date in dates:
            if date.start is not None:
                str(date)

        assert node.root is root
        for child in node.children:
            assert child.parent is node
            assert child.level > node.level
        if node is root:
            continue

        assert previous_line < node.linenumber <= len(lines)
        previous_line = node.linenumber
        heading_line = lines[node.linenumber - 1]
        assert heading_line[: node.level] == '*' * node.level
        assert heading_line[node.level].isspace()
        parent = node.parent
        assert parent is not None
        assert parent.level < node.level
        assert any(child is node for child in parent.children)
