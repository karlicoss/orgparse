"""Exercise the public parser API on upstream examples and real-world Org documents."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from .. import OrgEnv, OrgRootNode, load
from ..extra import Table
from ..node import OrgNode

CORPUS = Path(__file__).resolve().parents[3] / 'testdata' / 'external'
CORPUS_DIRS = (
    'org-mode/testing/examples',
    'sachac',
    'exobrain',
    'nvim-orgmode',
)


def corpus_files() -> list[Path]:
    paths = []
    for directory in CORPUS_DIRS:
        files = sorted((CORPUS / directory).rglob('*.org'))
        assert len(files) > 0, f'Missing Org corpus {directory}: run git submodule update --init --recursive'
        paths.extend(files)
    return paths


@pytest.mark.parametrize('path', corpus_files(), ids=lambda path: path.relative_to(CORPUS).as_posix())
def test_corpus(path: Path) -> None:
    """Check parser robustness and tree consistency across examples, configurations, notes, and documentation.

    Exercise heading/body formatting, property lookups, table row/block iteration,
        and formatting of populated timestamps.
    Check tag inclusion, parent/child links, a shared root, increasing heading line numbers,
        and heading levels against the source text.
    Check that entry line ranges cover the source without gaps or overlaps.
    These are smoke and consistency checks; exact parsed values require separate expected-output tests.
    """
    root = load(path)
    lines = path.read_text(encoding='utf-8').splitlines()
    assert root.is_root()
    assert root.parent is None

    previous_line = 0
    previous_end = 0
    for node in root:
        assert node.linenumber == previous_end + 1
        previous_end = node.end_linenumber
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

        dates = node.get_timestamps(active=True, inactive=True, point=True, range=True)
        if isinstance(node, OrgNode):
            dates = [*dates, node.scheduled, node.deadline, node.closed, *node.clock, *node.repeated_tasks]
        for timestamp in dates:
            if timestamp.start is not None:
                str(timestamp)

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

    assert previous_end == len(lines)


def test_exobrain_axol() -> None:
    """Check concrete parser results against Axol notes in the pinned exobrain submodule.

    Cover file metadata, five-level outlines, navigation, TODO states, priorities, inherited tags,
        properties, dated headings, raw/plain links, Unicode, duplicate IDs, and source line ranges.
    Expected values come from the source document rather than a snapshot of parser output.
    """
    path = CORPUS / 'exobrain' / 'projects' / 'axol.org'
    # The export omits TODO declarations, so supply the custom states used in the document.
    env = OrgEnv(todos=['TODO', 'STRT'], dones=['DONE', 'CANCEL'], filename=str(path))
    root = load(path, env=env)

    def by_id(node_id: str) -> OrgNode:
        [node] = [node for node in root[1:] if node.get_property('ID') == node_id]
        assert isinstance(node, OrgNode)
        return node

    assert isinstance(root, OrgRootNode)
    assert root.env is env
    assert root.env.filename == str(path)
    assert root.get_file_property('title') == 'Axol: search alerts'
    assert root.get_file_property('LOGSEQ_TITLE') == 'axol'
    assert root.get_file_property('OPTIONS') == 'toc:nil'
    assert root.get_file_property('TOC') == 'headlines 2'
    assert root.tags == {'axol'}
    assert "Eventually I'll write about it here" in root.body
    assert "Eventually I'll write about it [[https://beepb00p.xyz/axol.html][here]]" in root.get_body(format='raw')
    assert (root.linenumber, root.end_linenumber) == (1, 8)
    assert len(root) == 184
    assert root[0] is root
    assert len(root.children) == 51
    assert [node.heading for node in root.children[:8]] == [
        'Motivation',
        'Similar/existing projects',
        '* Make it more user friendly',
        '* Blacklisting',
        'What would be a good UI for axol?',
        'Queries',
        'Sources',
        'CI/testing',
    ]

    motivation = by_id('mtvtn')
    assert motivation is root[1]
    assert motivation.parent is root
    assert motivation.todo is None
    assert motivation.priority == 'A'
    assert motivation.shallow_tags == set()
    assert motivation.tags == {'axol'}
    assert motivation.previous_same_level is None
    assert motivation.next_same_level is by_id('smlrxstngprjcts')
    assert (motivation.linenumber, motivation.end_linenumber) == (9, 12)

    doctor = by_id('ddxldctrcnfg')
    assert doctor.heading == 'add axol doctor config'
    assert doctor.todo == 'TODO'
    assert doctor.priority is None
    assert doctor.properties == {'CREATED': '[2020-11-30]', 'ID': 'ddxldctrcnfg'}
    assert doctor.shallow_tags == {'project'}
    assert doctor.tags == {'axol', 'project'}
    assert doctor.body == 'also axol doctor to check individual providers + reuse in tests'
    # A timestamp inside a property drawer is a property value, not a body timestamp.
    assert doctor.datelist == []

    bret = by_id('ddbrtvctr')
    interface = by_id('hndprprntrfcfrt')
    gui = by_id('whtsthqckstpssblwytcrtgssthncnfgrghtprhpsslfchckng')
    leaf = by_id('kjstmnfnctnsndsk')
    assert bret.heading == 'add bret victor?'
    assert bret.todo == 'STRT'
    assert bret.priority == 'C'
    assert gui.todo == 'STRT'
    assert [node.level for node in (bret, interface, gui, leaf)] == [2, 3, 4, 5]
    assert bret.parent is by_id('qrs')
    assert interface.parent is bret
    assert gui.parent is interface
    assert leaf.parent is gui
    assert leaf.root is root
    assert bret.children == [interface]
    assert list(bret) == [bret, interface, gui, leaf]
    assert list(bret[1:]) == [interface, gui, leaf]
    assert bret[-1] is leaf
    assert leaf.children == []
    assert bret.shallow_tags == {'bretvictor'}
    assert leaf.shallow_tags == set()
    assert leaf.tags == {'axol', 'bretvictor'}
    assert leaf.get_property('CREATED') is None
    assert (bret.linenumber, bret.end_linenumber) == (368, 372)
    assert (leaf.linenumber, leaf.end_linenumber) == (381, 384)
    assert bret.next_same_level is by_id('tdchngprttynctsrchntwttr')

    bookmark = by_id('spnbrdntgpnbrdbkmrkstggdg')
    assert bookmark.heading == '[2020-05-01] Pinboard bookmarks tagged eeg'
    assert (
        bookmark.get_heading(format='raw')
        == '[2020-05-01] [[https://pinboard.in/t:eeg][Pinboard bookmarks tagged eeg]]'
    )
    assert bookmark.todo == 'TODO'
    assert bookmark.priority == 'D'
    [timestamp] = bookmark.get_timestamps(inactive=True, point=True)
    assert timestamp.start == date(2020, 5, 1)
    assert timestamp.end is None
    assert not timestamp.is_active()
    assert not timestamp.has_time()
    assert bookmark.datelist == [timestamp]
    assert bookmark.get_timestamps(active=True, point=True) == []
    assert bookmark.rangelist == []

    done = by_id('gtsmgdrsltsntwttr')
    assert done.heading == '[2019-07-28] "виктор аргонов" got some good results on twitter'
    assert done.todo == 'DONE'
    assert done.priority is None
    assert done.tags == {'axol', 'argonov'}
    assert [timestamp.start for timestamp in done.datelist] == [date(2019, 7, 28)]
    cancelled = by_id('rst')
    assert cancelled.todo == 'CANCEL'
    assert cancelled.heading == 'rust?'

    # Repeated IDs and identical headings must remain separate entries in document order.
    duplicates = [node for node in root[1:] if node.get_property('ID') == 'twttrmypymnflx']
    assert [node.linenumber for node in duplicates] == [190, 196, 203, 210]
    assert [node.heading for node in duplicates] == [
        '[2020-01-01] twitter_mypy (211) - Miniflux',
        '[2020-01-01] twitter_mypy (211) - Miniflux',
        '[2020-01-01] twitter_mypy (111) - Miniflux',
        '[2020-01-01] twitter_mypy (111) - Miniflux',
    ]
    assert duplicates[0].next_same_level is duplicates[1]
    assert duplicates[1].previous_same_level is duplicates[0]
    assert duplicates[0].body == 'https://axol.karlicoss.xyz/feed/53/entries\n: /mypy1031'
    assert 'みどりさん！' in duplicates[1].body  # noqa: RUF001

    tasks = by_id('smtds')
    assert tasks.children == []
    assert tasks.body.splitlines()[:3] == [
        '- [ ] move individual data sources to files within the repo.. not even submodules, too much hassle',
        '  if someone needs, they can just import axol.sources.src directly',
        '- [ ] cleanup the json shit.. ideally use some proper library',
    ]

    last = by_id('prnngfrnwvsqltdbbrwsrmksrtlcksthdb')
    assert root[-1] is last
    assert root.children[-1] is last
    assert last.next_same_level is None
    assert last.get_property('CREATED') == '[2021-02-09]'
    assert last.body == ''
    assert (last.linenumber, last.end_linenumber) == (1002, 1006)


def test_sachac_config() -> None:
    """Check planning, clocking, logbook, and rich-body results from Sacha's pinned configuration.

    Assert exact source values for combined planning lines, state transitions, ordinary and multi-day clocks,
        open and zero-duration clocks, a named table, and its accompanying source block.
    These cases complement the outline and metadata coverage in the exobrain test.
    """
    root = load(CORPUS / 'sachac' / 'Sacha.org')

    def by_custom_id(node_id: str) -> OrgNode:
        [node] = [node for node in root[1:] if node.get_property('CUSTOM_ID') == node_id]
        assert isinstance(node, OrgNode)
        return node

    which_key = by_custom_id('which-key-replacements')
    assert which_key.heading == 'Changing the which-key labels for shortcuts'
    assert which_key.todo == 'DONE'
    assert which_key.scheduled.start == date(2025, 1, 5)
    assert which_key.scheduled.end is None
    assert which_key.scheduled.is_active()
    assert not which_key.scheduled.has_time()
    assert which_key.closed.start == datetime(2025, 1, 6, 13, 50)
    assert not which_key.closed.is_active()
    assert which_key.deadline.start is None
    assert which_key.get_property('CREATED') == '[2025-01-04 Sat 21:11]'
    [transition] = which_key.repeated_tasks
    assert (transition.before, transition.after) == ('TODO', 'DONE')
    assert transition.start == datetime(2025, 1, 6, 13, 50)
    assert not transition.is_active()
    # Planning, property, and state-change timestamps are metadata rather than body timestamps.
    assert which_key.get_timestamps(active=True, inactive=True, point=True, range=True) == []

    azure = by_custom_id('writing-and-editing-learning-french-speech-synthesis-azure')
    assert azure.heading == 'Azure'
    assert azure.todo == 'DONE'
    assert azure.closed.start == datetime(2026, 3, 24, 9, 30)
    assert azure.deadline.start == date(2026, 3, 7)
    assert azure.deadline.end is None
    assert azure.deadline.is_active()
    assert azure.scheduled.start is None

    blog = by_custom_id('completion-consult-consult-omni-blog-posts')
    assert blog.heading == 'Finding my blog posts with consult-omni'
    assert blog.get_property('Effort') == 30
    assert blog.get_property('EXPORT_DATE') == '2025-07-21T23:12:28-0400'
    [clock] = blog.clock
    assert clock.start == datetime(2025, 7, 21, 22, 27)
    assert clock.end == datetime(2025, 7, 21, 23, 16)
    assert clock.duration == timedelta(minutes=49)
    assert clock.is_duration_consistent()
    assert not clock.is_active()
    [transition] = blog.repeated_tasks
    assert (transition.before, transition.after) == ('STARTED', 'DONE')
    assert transition.start == datetime(2025, 7, 21, 23, 37)
    assert blog.get_timestamps(inactive=True, range=True) == []

    french = by_custom_id(
        'writing-and-editing-learning-french-emacs-and-french-focus-flycheck-grammalecte-on-the-narrowed-part-of-the-buffer'
    )
    [clock] = french.clock
    assert clock.start == datetime(2026, 1, 30, 21, 3)
    assert clock.end == datetime(2026, 2, 1, 11, 23)
    assert clock.duration == timedelta(hours=38, minutes=20)
    assert clock.is_duration_consistent()
    # The later update is a body timestamp, independent of the clock and logbook metadata.
    [updated] = french.get_timestamps(inactive=True, point=True)
    assert updated.start == date(2026, 4, 11)
    assert updated.end is None

    find_function = by_custom_id('org-mode-org-babel-fix-find-function-when-i-ve-evaluated-something-from-org-babel')
    [open_clock, zero_clock] = find_function.clock
    assert open_clock.start == datetime(2026, 4, 5, 14, 59)
    assert open_clock.end is None
    assert not open_clock.has_end()
    assert zero_clock.start == datetime(2026, 4, 5, 14, 59)
    assert zero_clock.end == datetime(2026, 4, 5, 14, 59)
    assert zero_clock.has_end()
    assert zero_clock.duration == timedelta(0)
    assert zero_clock.is_duration_consistent()

    abbreviations = by_custom_id('completion-define-abbreviations')
    assert abbreviations.heading == 'Define abbreviations'
    [table] = [part for part in abbreviations.body_rich if isinstance(part, Table)]
    assert table.name == 'global-abbrev'
    expected_rows = [
        ['meweb', 'https://sachachua.com'],
        ['mehub', 'https://github.com/sachac'],
        ['mem', 'sacha@sachachua.com'],
        ['mema', '@sacha@social.sachachua.com'],
    ]
    assert list(table.rows) == expected_rows
    assert list(table.blocks) == [expected_rows]
    body = abbreviations.get_body(format='raw')
    assert '#+NAME: global-abbrev' in body
    assert (
        '''#+begin_src emacs-lisp :var abbrevs=global-abbrev
(setq-default abbrev-mode 1)
(define-abbrev global-abbrev-table "ot" ""
  (lambda () (insert (format-time-string "[%Y-%m-%d %a %H:%M]"))))
(define-abbrev global-abbrev-table "ots" ""
  (lambda () (insert (format-time-string "[%Y-%m-%d %a %H:%M:%S]"))))
(dolist (row abbrevs)
\t(define-abbrev global-abbrev-table (elt row 0) (elt row 1)))
#+end_src'''
        in body
    )


def test_nvim_orgmode_repeating_deadline() -> None:
    """Check that loading a real task fixture preserves its timed deadline and weekly repeater."""
    root = load(CORPUS / 'nvim-orgmode' / 'tests' / 'plenary' / 'fixtures' / 'todo.org')
    [task] = [node for node in root[1:] if node.heading == 'Repeatable task']
    assert isinstance(task, OrgNode)
    assert task.todo == 'TODO'
    assert task.deadline.start == datetime(2021, 9, 7, 12, 0)
    assert task.deadline.end is None
    assert task.deadline.is_active()
    assert task.deadline.has_time()
    assert str(task.deadline) == '<2021-09-07 Tue 12:00 +1w>'
    assert task.get_timestamps(active=True, point=True) == []
    assert task.body == ''
