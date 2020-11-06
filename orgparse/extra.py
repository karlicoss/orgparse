import re
from typing import List, Sequence, Dict, Iterator, Iterable, Union, Optional


RE_TABLE_SEPARATOR = re.compile(r'\s*\|(\-+\+)*\-+\|')
RE_TABLE_ROW = re.compile(r'\s*\|([^|]+)+\|')
STRIP_CELL_WHITESPACE = True


Row = Sequence[str]

class Table:
    def __init__(self, lines: List[str]) -> None:
        self._lines = lines

    @property
    def blocks(self) -> Iterator[Sequence[Row]]:
        group: List[Row] = []
        first = True
        for r in self._pre_rows():
            if r is None:
                if not first or len(group) > 0:
                    yield group
                    first = False
                group = []
            else:
                group.append(r)
        if len(group) > 0:
            yield group

    def __iter__(self) -> Iterator[Row]:
        return self.rows

    @property
    def rows(self) -> Iterator[Row]:
        for r in self._pre_rows():
            if r is not None:
                yield r

    def _pre_rows(self) -> Iterator[Optional[Row]]:
        for l in self._lines:
            if RE_TABLE_SEPARATOR.match(l):
                yield None
            else:
                pr = l.strip().strip('|').split('|')
                if STRIP_CELL_WHITESPACE:
                    pr = [x.strip() for x in pr]
                yield pr
        # TODO use iparse helper?

    @property
    def as_dicts(self) -> 'AsDictHelper':
        bl = list(self.blocks)
        if len(bl) != 2:
            raise RuntimeError('Need two-block table to non-ambiguously guess column names')
        hrows = bl[0]
        if len(hrows) != 1:
            raise RuntimeError(f'Need single row heading to guess column names, got: {hrows}')
        columns = hrows[0]
        assert len(set(columns)) == len(columns), f'Duplicate column names: {columns}'
        return AsDictHelper(
            columns=columns,
            rows=bl[1],
        )


class AsDictHelper:
    def __init__(self, columns: Sequence[str], rows: Sequence[Row]) -> None:
        self.columns = columns
        self._rows = rows

    def __iter__(self) -> Iterator[Dict[str, str]]:
        for x in self._rows:
            yield {k: v for k, v in zip(self.columns, x)}


class Gap:
    # todo later, add indices etc
    pass


Rich = Union[Table, Gap]
def to_rich_text(text: str) -> Iterator[Rich]:
    '''
    Convert an org-mode text into a 'rich' text, e.g. tables/lists/etc, interleaved by gaps.
    NOTE: you shouldn't rely on the number of items returned by this function,
    it might change in the future when more types are supported.

    At the moment only tables are supported.
    '''
    lines = text.splitlines(keepends=True)
    group: List[str] = []
    last = Gap
    def emit() -> Rich:
        nonlocal group, last
        if   last is Gap:
            res = Gap()
        elif last is Table:
            res = Table(group) # type: ignore
        else:
            raise RuntimeError(f'Unexpected type {last}')
        group = []
        return res

    for line in lines:
        if RE_TABLE_ROW.match(line) or RE_TABLE_SEPARATOR.match(line):
            cur = Table
        else:
            cur = Gap # type: ignore
        if cur is not last:
            if len(group) > 0:
                yield emit()
            last = cur # type: ignore
        group.append(line)
    if len(group) > 0:
        yield emit()
