from __future__ import annotations

import itertools
import re
from collections.abc import Iterable, Iterator, Sequence
from typing import Any, Optional, TypeVar, cast

from .date import (
    OrgDate,
    OrgDateClock,
    OrgDateClosed,
    OrgDateDeadline,
    OrgDateRepeatedTask,
    OrgDateScheduled,
    parse_sdc,
)
from .extra import Rich, to_rich_text
from .inline import to_plain_text
from .lines import (  # noqa: F401
    ClockLine,
    HeadingLine,
    LineItem,
    LogbookEndLine,
    LogbookStartLine,
    PropertyDrawerEndLine,
    PropertyDrawerStartLine,
    PropertyEntryLine,
    PropertyValue,
    RepeatTaskLine,
    SdcLine,
    TextLine,
    parse_duration_to_minutes,
    parse_duration_to_minutes_float,
    parse_heading_level,
    parse_heading_priority,
    parse_heading_tags,
    parse_heading_todos,
    parse_property,
)


def lines_to_chunks(lines: Iterable[str]) -> Iterable[list[str]]:
    chunk: list[str] = []
    for l in lines:
        if RE_NODE_HEADER.search(l):
            yield chunk
            chunk = []
        chunk.append(l)
    yield chunk


RE_NODE_HEADER = re.compile(r"^\s*\*+ ")


TOrgDate = TypeVar("TOrgDate", bound=OrgDate)


class LogbookDrawer:
    def __init__(
        self,
        start_line: LogbookStartLine,
        end_line: LogbookEndLine,
        entries: list[RepeatTaskLine],
        indent: str,
        *,
        generated: bool,
    ) -> None:
        self.start_line = start_line
        self.end_line = end_line
        self.entries = entries
        self.indent = indent
        self.generated = generated


class PropertyDrawer:
    def __init__(
        self,
        start_line: PropertyDrawerStartLine,
        end_line: PropertyDrawerEndLine,
        entries: list[PropertyEntryLine],
        indent: str,
    ) -> None:
        self.start_line = start_line
        self.end_line = end_line
        self.entries = entries
        self.indent = indent


#  -> Optional[Tuple[str, Sequence[str]]]: # todo wtf?? it says 'ABCMeta isn't subscriptable??'
def parse_comment(line: str):
    """
    Parse special comment such as ``#+SEQ_TODO``

    >>> parse_comment('#+SEQ_TODO: TODO | DONE')
    ('SEQ_TODO', ['TODO | DONE'])
    >>> parse_comment('# not a special comment')  # None

    >>> parse_comment('#+FILETAGS: :tag1:tag2:')
    ('FILETAGS', ['tag1', 'tag2'])
    """
    match = re.match(r'\s*#\+', line)
    if match:
        end = match.end(0)
        comment = line[end:].split(':', maxsplit=1)
        if len(comment) >= 2:
            key = comment[0]
            value = comment[1].strip()
            if key.upper() == 'FILETAGS':
                # just legacy behaviour; it seems like filetags is the only one that separated by ':'
                # see https://orgmode.org/org.html#In_002dbuffer-Settings
                return (key, [c.strip() for c in value.split(':') if len(c.strip()) > 0])
            else:
                return (key, [value])
    return None


def parse_seq_todo(line):
    """
    Parse value part of SEQ_TODO/TODO/TYP_TODO comment.

    >>> parse_seq_todo('TODO | DONE')
    (['TODO'], ['DONE'])
    >>> parse_seq_todo(' Fred  Sara   Lucy Mike  |  DONE  ')
    (['Fred', 'Sara', 'Lucy', 'Mike'], ['DONE'])
    >>> parse_seq_todo('| CANCELED')
    ([], ['CANCELED'])
    >>> parse_seq_todo('REPORT(r) BUG(b) KNOWNCAUSE(k) | FIXED(f)')
    (['REPORT', 'BUG', 'KNOWNCAUSE'], ['FIXED'])

    See also:

    * (info "(org) Per-file keywords")
    * (info "(org) Fast access to TODO states")

    """
    todo_done = line.split('|', 1)
    if len(todo_done) == 2:
        (todos, dones) = todo_done
    else:
        (todos, dones) = (line, '')
    strip_fast_access_key = lambda x: x.split('(', 1)[0]
    return (
        list(map(strip_fast_access_key, todos.split())),
        list(map(strip_fast_access_key, dones.split())),
    )


class OrgEnv:
    """
    Information global to the file (e.g, TODO keywords).
    """

    def __init__(
        self,
        todos: Sequence[str] | None = None,
        dones: Sequence[str] | None = None,
        filename: str = '<undefined>',
    ) -> None:
        if dones is None:
            dones = ['DONE']
        if todos is None:
            todos = ['TODO']
        self._todos = list(todos)
        self._dones = list(dones)
        self._todo_not_specified_in_comment = True
        self._filename = filename
        self._nodes: list[OrgBaseNode] = []

    @property
    def nodes(self) -> list[OrgBaseNode]:
        """
        A list of org nodes.

        >>> OrgEnv().nodes   # default is empty (of course)
        []

        >>> from orgparse import loads
        >>> loads('''
        ... * Heading 1
        ... ** Heading 2
        ... *** Heading 3
        ... ''').env.nodes      # doctest: +ELLIPSIS  +NORMALIZE_WHITESPACE
        [<orgparse.node.OrgRootNode object at 0x...>,
         <orgparse.node.OrgNode object at 0x...>,
         <orgparse.node.OrgNode object at 0x...>,
         <orgparse.node.OrgNode object at 0x...>]

        """
        return self._nodes

    def add_todo_keys(self, todos, dones):
        if self._todo_not_specified_in_comment:
            self._todos = []
            self._dones = []
            self._todo_not_specified_in_comment = False
        self._todos.extend(todos)
        self._dones.extend(dones)

    @property
    def todo_keys(self):
        """
        TODO keywords defined for this document (file).

        >>> env = OrgEnv()
        >>> env.todo_keys
        ['TODO']

        """
        return self._todos

    @property
    def done_keys(self):
        """
        DONE keywords defined for this document (file).

        >>> env = OrgEnv()
        >>> env.done_keys
        ['DONE']

        """
        return self._dones

    @property
    def all_todo_keys(self):
        """
        All TODO keywords (including DONEs).

        >>> env = OrgEnv()
        >>> env.all_todo_keys
        ['TODO', 'DONE']

        """
        return self._todos + self._dones

    @property
    def filename(self) -> str:
        """
        Return a path to the source file or similar information.

        If the org objects are not loaded from a file, this value
        will be a string of the form ``<SOME_TEXT>``.
        """
        return self._filename

    # parser

    def from_chunks(self, chunks):
        yield OrgRootNode.from_chunk(self, next(chunks))
        for chunk in chunks:
            yield OrgNode.from_chunk(self, chunk)


class OrgBaseNode(Sequence):
    """
    Base class for :class:`OrgRootNode` and :class:`OrgNode`

    .. attribute:: env

       An instance of :class:`OrgEnv`.
       All nodes in a same file shares same instance.

    :class:`OrgBaseNode` is an iterable object:

    >>> from orgparse import loads
    >>> root = loads('''
    ... * Heading 1
    ... ** Heading 2
    ... *** Heading 3
    ... * Heading 4
    ... ''')
    >>> for node in root:
    ...     print(node)
    <BLANKLINE>
    * Heading 1
    ** Heading 2
    *** Heading 3
    * Heading 4

    Note that the first blank line is due to the root node, as
    iteration contains the object itself.  To skip that, use
    slice access ``[1:]``:

    >>> for node in root[1:]:
    ...     print(node)
    * Heading 1
    ** Heading 2
    *** Heading 3
    * Heading 4

    It also supports sequence protocol.

    >>> print(root[1])
    * Heading 1
    >>> root[0] is root  # index 0 means itself
    True
    >>> len(root)   # remember, sequence contains itself
    5

    Note the difference between ``root[1:]`` and ``root[1]``:

    >>> for node in root[1]:
    ...     print(node)
    * Heading 1
    ** Heading 2
    *** Heading 3

    Nodes remember the line number information (1-indexed):

    >>> print(root.children[1].linenumber)
    5
    """

    _body_lines: list[str]  # set by the child classes

    def __init__(self, env: OrgEnv, index: int | None = None) -> None:
        self.env = env

        self.linenumber = cast(int, None)  # set in parse_lines

        # content
        self._line_items: list[LineItem] = []
        self._lines: list[str] = []
        self._lines_dirty = False

        self._properties: dict[str, PropertyValue] = {}
        self._property_drawer: PropertyDrawer | None = None
        self._timestamps: list[OrgDate] = []

        # FIXME: use `index` argument to set index.  (Currently it is
        # done externally in `parse_lines`.)
        if index is not None:
            self._index = index
            """
            Index of `self` in `self.env.nodes`.

            It must satisfy an equality::

                self.env.nodes[self._index] is self

            This value is used for quick access for iterator and
            tree-like traversing.

            """

    def __iter__(self):
        yield self
        level = self.level
        for node in self.env._nodes[self._index + 1 :]:
            if node.level > level:
                yield node
            else:
                break

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        # As self.__len__ returns non-zero value always this is not
        # needed.  This function is only for performance.
        return True

    def __getitem__(self, key):
        if isinstance(key, slice):
            return itertools.islice(self, key.start, key.stop, key.step)
        elif isinstance(key, int):
            if key < 0:
                key += len(self)
            for i, node in enumerate(self):
                if i == key:
                    return node
            raise IndexError(f"Out of range {key}")
        else:
            raise TypeError(f"Inappropriate type {type(key)} for {type(self)}")

    # tree structure

    def _find_same_level(self, iterable) -> OrgBaseNode | None:
        for node in iterable:
            if node.level < self.level:
                return None
            if node.level == self.level:
                return node
        return None

    @property
    def previous_same_level(self) -> OrgBaseNode | None:
        """
        Return previous node if exists or None otherwise.

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node 1
        ... * Node 2
        ... ** Node 3
        ... ''')
        >>> (n1, n2, n3) = list(root[1:])
        >>> n1.previous_same_level is None
        True
        >>> n2.previous_same_level is n1
        True
        >>> n3.previous_same_level is None  # n2 is not at the same level
        True

        """
        return self._find_same_level(reversed(self.env._nodes[: self._index]))

    @property
    def next_same_level(self) -> OrgBaseNode | None:
        """
        Return next node if exists or None otherwise.

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node 1
        ... * Node 2
        ... ** Node 3
        ... ''')
        >>> (n1, n2, n3) = list(root[1:])
        >>> n1.next_same_level is n2
        True
        >>> n2.next_same_level is None  # n3 is not at the same level
        True
        >>> n3.next_same_level is None
        True

        """
        return self._find_same_level(self.env._nodes[self._index + 1 :])

    # FIXME: cache parent node
    def _find_parent(self):
        for node in reversed(self.env._nodes[: self._index]):
            if node.level < self.level:
                return node
        return None

    def get_parent(self, max_level: int | None = None):
        """
        Return a parent node.

        :arg int max_level:
            In the normally structured org file, it is a level
            of the ancestor node to return.  For example,
            ``get_parent(max_level=0)`` returns a root node.

            In the general case, it specify a maximum level of the
            desired ancestor node.  If there is no ancestor node
            whose level is equal to ``max_level``, this function
            try to find an ancestor node which level is smaller
            than ``max_level``.

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node 1
        ... ** Node 2
        ... ** Node 3
        ... ''')
        >>> (n1, n2, n3) = list(root[1:])
        >>> n1.get_parent() is root
        True
        >>> n2.get_parent() is n1
        True
        >>> n3.get_parent() is n1
        True

        For simplicity, accessing :attr:`parent` is alias of calling
        :meth:`get_parent` without argument.

        >>> n1.get_parent() is n1.parent
        True
        >>> root.parent is None
        True

        This is a little bit pathological situation -- but works.

        >>> root = loads('''
        ... * Node 1
        ... *** Node 2
        ... ** Node 3
        ... ''')
        >>> (n1, n2, n3) = list(root[1:])
        >>> n1.get_parent() is root
        True
        >>> n2.get_parent() is n1
        True
        >>> n3.get_parent() is n1
        True

        Now let's play with `max_level`.

        >>> root = loads('''
        ... * Node 1 (level 1)
        ... ** Node 2 (level 2)
        ... *** Node 3 (level 3)
        ... ''')
        >>> (n1, n2, n3) = list(root[1:])
        >>> n3.get_parent() is n2
        True
        >>> n3.get_parent(max_level=2) is n2  # same as default
        True
        >>> n3.get_parent(max_level=1) is n1
        True
        >>> n3.get_parent(max_level=0) is root
        True

        """
        if max_level is None:
            max_level = self.level - 1
        parent = self._find_parent()
        while parent.level > max_level:
            parent = parent.get_parent()
        return parent

    @property
    def parent(self):
        """
        Alias of :meth:`get_parent()` (calling without argument).
        """
        return self.get_parent()

    # FIXME: cache children nodes
    def _find_children(self):
        nodeiter = iter(self.env._nodes[self._index + 1 :])
        try:
            node = next(nodeiter)
        except StopIteration:
            return
        if node.level <= self.level:
            return
        yield node
        last_child_level = node.level
        for node in nodeiter:
            if node.level <= self.level:
                return
            if node.level <= last_child_level:
                yield node
                last_child_level = node.level

    @property
    def children(self):
        """
        A list of child nodes.

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node 1
        ... ** Node 2
        ... *** Node 3
        ... ** Node 4
        ... ''')
        >>> (n1, n2, n3, n4) = list(root[1:])
        >>> (c1, c2) = n1.children
        >>> c1 is n2
        True
        >>> c2 is n4
        True

        Note the difference to ``n1[1:]``, which returns the Node 3 also:

        >>> (m1, m2, m3) = list(n1[1:])
        >>> m2 is n3
        True

        """
        return list(self._find_children())

    @children.setter
    def children(self, value: Iterable[OrgNode]) -> None:
        new_children = list(value)
        if len(set(new_children)) != len(new_children):
            raise ValueError("Duplicate children are not allowed")
        for child in new_children:
            if not isinstance(child, OrgNode):
                raise TypeError(f"Child must be OrgNode, got {type(child)}")
            if child.env is not self.env:
                raise ValueError("Child must belong to the same OrgEnv")
            if self._node_contains(child, self):
                raise ValueError("Cannot reparent an ancestor under its descendant")
        for child in new_children:
            for other in new_children:
                if child is other:
                    continue
                if self._node_contains(child, other):
                    raise ValueError("Cannot reparent a node alongside its descendant")

        subtree_map: dict[OrgNode, list[OrgBaseNode]] = {}
        for child in new_children:
            subtree_map[child] = self._collect_subtree_nodes(child)

        for start, end in reversed(self._direct_children_ranges()):
            del self.env._nodes[start:end]

        for child in new_children:
            self._remove_subtree_if_present(child)

        for child in new_children:
            desired_level = self.level + 1
            delta = desired_level - child.level
            if delta:
                for node in subtree_map[child]:
                    if isinstance(node, OrgNode):
                        node._shift_level(delta)

        insert_at = self.env._nodes.index(self) + 1
        for child in new_children:
            nodes = subtree_map[child]
            self.env._nodes[insert_at:insert_at] = nodes
            insert_at += len(nodes)

        for index, node in enumerate(self.env._nodes):
            node._index = index

    def _subtree_end_index(self, start: int, level: int) -> int:
        end = start + 1
        while end < len(self.env._nodes) and self.env._nodes[end].level > level:
            end += 1
        return end

    def _collect_subtree_nodes(self, node: OrgBaseNode) -> list[OrgBaseNode]:
        try:
            start = self.env._nodes.index(node)
        except ValueError as exc:
            raise ValueError("Child must belong to the current OrgEnv node list") from exc
        end = self._subtree_end_index(start, node.level)
        return self.env._nodes[start:end]

    def _direct_children_ranges(self) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        index = self._index + 1
        while index < len(self.env._nodes) and self.env._nodes[index].level > self.level:
            node = self.env._nodes[index]
            if node.level == self.level + 1:
                end = self._subtree_end_index(index, node.level)
                ranges.append((index, end))
                index = end
            else:
                index += 1
        return ranges

    def _remove_subtree_if_present(self, node: OrgBaseNode) -> None:
        try:
            start = self.env._nodes.index(node)
        except ValueError:
            return
        end = self._subtree_end_index(start, node.level)
        del self.env._nodes[start:end]

    def _node_contains(self, ancestor: OrgBaseNode, node: OrgBaseNode) -> bool:
        try:
            start = self.env._nodes.index(ancestor)
        except ValueError:
            return False
        end = self._subtree_end_index(start, ancestor.level)
        try:
            target_index = self.env._nodes.index(node)
        except ValueError:
            return False
        return start < target_index < end

    @property
    def root(self):
        """
        The root node.

        >>> from orgparse import loads
        >>> root = loads('* Node 1')
        >>> n1 = root[1]
        >>> n1.root is root
        True

        """
        root = self
        while True:
            parent = root.get_parent()
            if not parent:
                return root
            root = parent

    @property
    def properties(self) -> dict[str, PropertyValue]:
        """
        Node properties as a dictionary.

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   :PROPERTIES:
        ...   :SomeProperty: value
        ...   :END:
        ... ''')
        >>> root.children[0].properties['SomeProperty']
        'value'

        """
        return self._properties

    @properties.setter
    def properties(self, value: dict[str, PropertyValue] | None) -> None:
        new_props = {} if value is None else dict(value)
        normalized: dict[str, PropertyValue] = {}
        render_values: dict[str, str] = {}
        for key, prop_value in new_props.items():
            (norm_value, render_value) = self._normalize_property_value(key, prop_value)
            normalized[key] = norm_value
            render_values[key] = render_value
        self._properties = normalized

        if not normalized:
            if self._property_drawer is not None:
                start_index = self._line_items.index(self._property_drawer.start_line)
                end_index = self._line_items.index(self._property_drawer.end_line)
                for index in range(end_index, start_index - 1, -1):
                    self._remove_line_item(index)
                self._property_drawer = None
                self._lines_dirty = True
            return

        drawer = self._property_drawer
        if drawer is None:
            drawer = self._create_property_drawer()

        entries_by_key: dict[str, list[PropertyEntryLine]] = {}
        for entry in drawer.entries:
            entries_by_key.setdefault(entry.key, []).append(entry)

        keys_to_remove = {entry.key for entry in drawer.entries if entry.key not in normalized}
        if keys_to_remove:
            for entry in list(drawer.entries):
                if entry.key in keys_to_remove:
                    index = self._line_items.index(entry)
                    self._remove_line_item(index)
                    drawer.entries.remove(entry)

        for key, prop_value in normalized.items():
            render_value = render_values[key]
            entries = entries_by_key.get(key, [])
            if entries:
                entries[-1].update_value(prop_value, render_value)
            else:
                insert_index = self._line_items.index(drawer.end_line)
                entry = PropertyEntryLine(
                    raw=f"{drawer.indent}:{key}: {render_value}" if render_value else f"{drawer.indent}:{key}:",
                    key=key,
                    value=prop_value,
                    render_value=render_value,
                    prefix=drawer.indent,
                )
                self._insert_line_item(insert_index, entry)
                drawer.entries.append(entry)
        self._lines_dirty = True

    def get_property(self, key, val=None) -> Optional[PropertyValue]:
        """
        Return property named ``key`` if exists or ``val`` otherwise.

        :arg str key:
            Key of property.

        :arg val:
            Default value to return.

        """
        return self._properties.get(key, val)

    # parser

    @classmethod
    def from_chunk(cls, env, lines):
        self = cls(env)
        self._lines = list(lines)
        self._line_items = [TextLine(line) for line in self._lines]
        self._parse_comments()
        return self

    def _parse_comments(self):
        special_comments: dict[str, list[str]] = {}
        for line in self._lines:
            parsed = parse_comment(line)
            if parsed:
                (key, vals) = parsed
                key = key.upper()  # case insensitive, so keep as uppercase
                special_comments.setdefault(key, []).extend(vals)
        self._special_comments = special_comments
        # parse TODO keys and store in OrgEnv
        for todokey in ['TODO', 'SEQ_TODO', 'TYP_TODO']:
            for val in special_comments.get(todokey, []):
                self.env.add_todo_keys(*parse_seq_todo(val))

    def _normalize_property_value(self, key: str, value: PropertyValue) -> tuple[PropertyValue, str]:
        if key == "Effort" and isinstance(value, str):
            return (parse_duration_to_minutes(value), value)
        return (value, str(value))

    def _create_property_drawer(self) -> PropertyDrawer:
        insert_at = self._property_drawer_insert_index()
        indent = self._property_drawer_indent(insert_at)
        start_line = PropertyDrawerStartLine(f"{indent}:PROPERTIES:")
        end_line = PropertyDrawerEndLine(f"{indent}:END:")
        self._insert_line_item(insert_at, start_line)
        self._insert_line_item(insert_at + 1, end_line)
        drawer = PropertyDrawer(start_line, end_line, [], indent)
        self._property_drawer = drawer
        return drawer

    def _property_drawer_insert_index(self) -> int:
        return 0

    def _property_drawer_indent(self, insert_at: int) -> str:
        if insert_at < len(self._line_items):
            line = self._line_items[insert_at].render()
            return line[: len(line) - len(line.lstrip(" "))]
        return ""

    def _sync_property_drawer_from_lines(self) -> None:
        self._property_drawer = None
        index = 0
        while index < len(self._line_items):
            line_item = self._line_items[index]
            line = line_item.render()
            if isinstance(line_item, PropertyDrawerStartLine) or line.strip() == ":PROPERTIES:":
                start_line = PropertyDrawerStartLine(line)
                self._update_line_item(index, start_line)
                indent = line[: len(line) - len(line.lstrip(" "))]
                entries: list[PropertyEntryLine] = []
                end_index = index + 1
                while end_index < len(self._line_items):
                    end_line_item = self._line_items[end_index]
                    end_line = end_line_item.render()
                    if isinstance(end_line_item, PropertyDrawerEndLine) or end_line.strip() == ":END:":
                        end_line_item = PropertyDrawerEndLine(end_line)
                        self._update_line_item(end_index, end_line_item)
                        self._property_drawer = PropertyDrawer(start_line, end_line_item, entries, indent)
                        return
                    entry = PropertyEntryLine.from_line(end_line)
                    if entry is not None:
                        self._update_line_item(end_index, entry)
                        entries.append(entry)
                    end_index += 1
                return
            index += 1

    def _iparse_properties(self, ilines: Iterator[str]) -> Iterator[str]:
        self._properties = {}
        in_property_field = False
        for line in ilines:
            if in_property_field:
                if line.find(":END:") >= 0:
                    break
                else:
                    (key, val) = parse_property(line)
                    if key is not None and val is not None:
                        self._properties.update({key: val})
            elif line.find(":PROPERTIES:") >= 0:
                in_property_field = True
            else:
                yield line
        for line in ilines:
            yield line

    # misc

    @property
    def level(self) -> int:
        """
        Level of this node.
        """
        raise NotImplementedError

    def _get_tags(self, *, inher: bool = False) -> set[str]:  # noqa: ARG002
        """
        Return tags

        :arg inher:
            Mix with tags of all ancestor nodes if ``True``.
        """
        return set()

    @property
    def tags(self) -> set[str]:
        """
        Tags of this and parent's node.

        >>> from orgparse import loads
        >>> n2 = loads('''
        ... * Node 1    :TAG1:
        ... ** Node 2   :TAG2:
        ... ''')[2]
        >>> n2.tags == set(['TAG1', 'TAG2'])
        True

        """
        return self._get_tags(inher=True)

    @property
    def shallow_tags(self) -> set[str]:
        """
        Tags defined for this node (don't look-up parent nodes).

        >>> from orgparse import loads
        >>> n2 = loads('''
        ... * Node 1    :TAG1:
        ... ** Node 2   :TAG2:
        ... ''')[2]
        >>> n2.shallow_tags == set(['TAG2'])
        True

        """
        return self._get_tags(inher=False)

    @staticmethod
    def _get_text(text, format: str = 'plain'):  # noqa: A002
        if format == 'plain':
            return to_plain_text(text)
        elif format == 'raw':
            return text
        elif format == 'rich':
            return to_rich_text(text)
        else:
            raise ValueError(f'format={format} is not supported.')

    def get_body(self, format: str = 'plain') -> str:  # noqa: A002
        """
        Return a string of body text.

        See also: :meth:`get_heading`.

        """
        return self._get_text('\n'.join(self._body_lines), format) if self._lines else ''

    @property
    def body(self) -> str:
        """Alias of ``.get_body(format='plain')``."""
        return self.get_body()

    @body.setter
    def body(self, value: str) -> None:
        new_lines = value.splitlines()
        self._replace_body_lines(new_lines)

    @property
    def body_rich(self) -> Iterator[Rich]:
        r = self.get_body(format='rich')
        return cast(Iterator[Rich], r)  # meh..

    def _replace_body_lines(self, new_lines: list[str]) -> None:
        body_indices = self._body_line_indices()
        if body_indices:
            insert_at = body_indices[0]
            for index in reversed(body_indices):
                self._remove_line_item(index)
        else:
            insert_at = self._body_insert_index()
        for offset, line in enumerate(new_lines):
            self._insert_line_item(insert_at + offset, TextLine(line))
        self._body_lines = list(new_lines)
        self._lines_dirty = True
        self._refresh_timestamps_after_body_change()

    def _body_line_indices(self) -> list[int]:
        return [index for index, item in enumerate(self._line_items) if self._is_body_line_item(index, item)]

    def _is_body_line_item(self, index: int, item: LineItem) -> bool:  # noqa: ARG002
        return not isinstance(
            item,
            (
                PropertyDrawerStartLine,
                PropertyDrawerEndLine,
                PropertyEntryLine,
            ),
        )

    def _body_insert_index(self) -> int:
        return len(self._line_items)

    def _refresh_timestamps_after_body_change(self) -> None:
        self._timestamps = []
        for line in self._body_lines:
            self._timestamps.extend(OrgDate.list_from_str(line))

    @property
    def heading(self) -> str:
        raise NotImplementedError

    def is_root(self):
        """
        Return ``True`` when it is a root node.

        >>> from orgparse import loads
        >>> root = loads('* Node 1')
        >>> root.is_root()
        True
        >>> n1 = root[1]
        >>> n1.is_root()
        False

        """
        return False

    def get_timestamps(self, active=False, inactive=False, range=False, point=False):  # noqa: FBT002,A002  # will fix later
        """
        Return a list of timestamps in the body text.

        :type   active: bool
        :arg    active: Include active type timestamps.
        :type inactive: bool
        :arg  inactive: Include inactive type timestamps.
        :type    range: bool
        :arg     range: Include timestamps which has end date.
        :type    point: bool
        :arg     point: Include timestamps which has no end date.

        :rtype: list of :class:`orgparse.date.OrgDate` subclasses


        Consider the following org node:

        >>> from orgparse import loads
        >>> node = loads('''
        ... * Node
        ...   CLOSED: [2012-02-26 Sun 21:15] SCHEDULED: <2012-02-26 Sun>
        ...   CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] =>  0:05
        ...   Some inactive timestamp [2012-02-23 Thu] in body text.
        ...   Some active timestamp <2012-02-24 Fri> in body text.
        ...   Some inactive time range [2012-02-25 Sat]--[2012-02-27 Mon].
        ...   Some active time range <2012-02-26 Sun>--<2012-02-28 Tue>.
        ... ''').children[0]

        The default flags are all off, so it does not return anything.

        >>> node.get_timestamps()
        []

        You can fetch appropriate timestamps using keyword arguments.

        >>> node.get_timestamps(inactive=True, point=True)
        [OrgDate((2012, 2, 23), None, False)]
        >>> node.get_timestamps(active=True, point=True)
        [OrgDate((2012, 2, 24))]
        >>> node.get_timestamps(inactive=True, range=True)
        [OrgDate((2012, 2, 25), (2012, 2, 27), False)]
        >>> node.get_timestamps(active=True, range=True)
        [OrgDate((2012, 2, 26), (2012, 2, 28))]

        This is more complex example.  Only active timestamps,
        regardless of range/point type.

        >>> node.get_timestamps(active=True, point=True, range=True)
        [OrgDate((2012, 2, 24)), OrgDate((2012, 2, 26), (2012, 2, 28))]

        """
        return [
            ts
            for ts in self._timestamps
            if (
                ((active and ts.is_active()) or (inactive and not ts.is_active()))
                and ((range and ts.has_end()) or (point and not ts.has_end()))
            )
        ]

    @property
    def datelist(self):
        """
        Alias of ``.get_timestamps(active=True, inactive=True, point=True)``.

        :rtype: list of :class:`orgparse.date.OrgDate` subclasses

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node with point dates <2012-02-25 Sat>
        ...   CLOSED: [2012-02-25 Sat 21:15]
        ...   Some inactive timestamp [2012-02-26 Sun] in body text.
        ...   Some active timestamp <2012-02-27 Mon> in body text.
        ... ''')
        >>> root.children[0].datelist      # doctest: +NORMALIZE_WHITESPACE
        [OrgDate((2012, 2, 25)),
         OrgDate((2012, 2, 26), None, False),
         OrgDate((2012, 2, 27))]

        """
        return self.get_timestamps(active=True, inactive=True, point=True)

    @property
    def rangelist(self):
        """
        Alias of ``.get_timestamps(active=True, inactive=True, range=True)``.

        :rtype: list of :class:`orgparse.date.OrgDate` subclasses

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node with range dates <2012-02-25 Sat>--<2012-02-28 Tue>
        ...   CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] => 0:05
        ...   Some inactive time range [2012-02-25 Sat]--[2012-02-27 Mon].
        ...   Some active time range <2012-02-26 Sun>--<2012-02-28 Tue>.
        ...   Some time interval <2012-02-27 Mon 11:23-12:10>.
        ... ''')
        >>> root.children[0].rangelist     # doctest: +NORMALIZE_WHITESPACE
        [OrgDate((2012, 2, 25), (2012, 2, 28)),
         OrgDate((2012, 2, 25), (2012, 2, 27), False),
         OrgDate((2012, 2, 26), (2012, 2, 28)),
         OrgDate((2012, 2, 27, 11, 23, 0), (2012, 2, 27, 12, 10, 0))]

        """
        return self.get_timestamps(active=True, inactive=True, range=True)

    def __str__(self) -> str:
        return "\n".join(self._render_lines())

    def _render_lines(self) -> list[str]:
        if self._lines_dirty:
            self._lines = [line.render() for line in self._line_items]
            self._lines_dirty = False
        return self._lines

    def _update_line_item(self, index: int, item: LineItem) -> None:
        self._line_items[index] = item
        if self._lines:
            self._lines[index] = item.render()
        else:
            self._lines_dirty = True

    def _insert_line_item(self, index: int, item: LineItem) -> None:
        self._line_items.insert(index, item)
        self._lines_dirty = True

    def _remove_line_item(self, index: int) -> None:
        del self._line_items[index]
        self._lines_dirty = True

    # todo hmm, not sure if it really belongs here and not to OrgRootNode?
    def get_file_property_list(self, property: str):  # noqa: A002
        """
        Return a list of the selected property
        """
        vals = self._special_comments.get(property.upper(), None)
        return [] if vals is None else vals

    def get_file_property(self, property: str):  # noqa: A002
        """
        Return a single element of the selected property or None if it doesn't exist
        """
        vals = self._special_comments.get(property.upper(), None)
        if vals is None:
            return None
        elif len(vals) == 1:
            return vals[0]
        else:
            raise RuntimeError(f'Multiple values for property {property}: {vals}')


class OrgRootNode(OrgBaseNode):
    """
    Node to represent a file. Its body contains all lines before the first
    headline

    See :class:`OrgBaseNode` for other available functions.
    """

    @property
    def heading(self) -> str:
        return ''

    def _get_tags(self, *, inher: bool = False) -> set[str]:  # noqa: ARG002
        filetags = self.get_file_property_list('FILETAGS')
        return set(filetags)

    @property
    def level(self) -> int:
        return 0

    def get_parent(self, max_level=None):  # noqa: ARG002
        return None

    def is_root(self) -> bool:
        return True

    # parsers

    def _parse_pre(self):
        """Call parsers which must be called before tree structuring"""
        ilines: Iterator[str] = iter(self._lines)
        ilines = self._iparse_properties(ilines)
        ilines = self._iparse_timestamps(ilines)
        self._body_lines = list(ilines)
        self._sync_property_drawer_from_lines()

    def _iparse_timestamps(self, ilines: Iterator[str]) -> Iterator[str]:
        self._timestamps = []
        for line in ilines:
            self._timestamps.extend(OrgDate.list_from_str(line))
            yield line

    def _property_drawer_indent(self, insert_at: int) -> str:  # noqa: ARG002
        return ""


class OrgNode(OrgBaseNode):
    """
    Node to represent normal org node

    See :class:`OrgBaseNode` for other available functions.

    """

    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, **kwds)
        # fixme instead of casts, should organize code in such a way that they aren't necessary
        self._heading = cast(str, None)
        self._level: int | None = None
        self._tags = cast(list[str], None)
        self._todo: Optional[str] = None
        self._priority: Optional[str] = None
        self._heading_line: HeadingLine | None = None
        self._sdc_line: SdcLine | None = None
        self._clock_lines: list[ClockLine] = []
        self._scheduled = OrgDateScheduled(None)
        self._deadline = OrgDateDeadline(None)
        self._closed = OrgDateClosed(None)
        self._clocklist: list[OrgDateClock] = []
        self._body_lines: list[str] = []
        self._repeated_tasks: list[OrgDateRepeatedTask] = []
        self._logbook_drawers: list[LogbookDrawer] = []

    # parser

    def _parse_pre(self):
        """Call parsers which must be called before tree structuring"""
        self._parse_heading()
        # FIXME: make the following parsers "lazy"
        ilines: Iterator[str] = iter(self._lines)
        try:
            next(ilines)  # skip heading
        except StopIteration:
            return
        self._clock_line_indices = iter(self._find_clock_line_indices())
        ilines = self._iparse_sdc(ilines)
        ilines = self._iparse_clock(ilines)
        ilines = self._iparse_properties(ilines)
        ilines = self._iparse_repeated_tasks(ilines)
        ilines = self._iparse_timestamps(ilines)
        self._body_lines = list(ilines)
        self._sync_property_drawer_from_lines()
        self._sync_logbook_drawers_from_lines()

    def _parse_heading(self) -> None:
        heading_line = HeadingLine.from_line(self._lines[0], self.env.all_todo_keys)
        self._heading_line = heading_line
        self._level = heading_line.level
        self._tags = list(heading_line.tags)
        self._todo = heading_line.todo
        self._priority = heading_line.priority
        self._heading = heading_line.heading
        self._update_line_item(0, heading_line)

    def _normalize_tags(self, tags: Iterable[str] | None) -> list[str]:
        if tags is None:
            return []
        if isinstance(tags, str):
            return [tags]
        if isinstance(tags, set):
            return sorted(tags)
        return list(tags)

    def _shift_level(self, delta: int) -> None:
        if self._level is None:
            return
        self._level += delta
        if self._heading_line is not None:
            self._heading_line.level = self._level
            self._heading_line.mark_dirty()
            self._update_line_item(0, self._heading_line)

    def _is_body_line_item(self, index: int, item: LineItem) -> bool:  # noqa: ARG002
        return not isinstance(
            item,
            (
                HeadingLine,
                SdcLine,
                ClockLine,
                PropertyDrawerStartLine,
                PropertyDrawerEndLine,
                PropertyEntryLine,
                RepeatTaskLine,
            ),
        )

    def _refresh_timestamps_after_body_change(self) -> None:
        self._timestamps = []
        self._timestamps.extend(OrgDate.list_from_str(self._heading))
        for line in self._body_lines:
            self._timestamps.extend(OrgDate.list_from_str(line))

    def _update_heading_line(self) -> None:
        if self._heading_line is None:
            return
        self._heading_line.todo = self._todo
        self._heading_line.priority = self._priority
        self._heading_line.heading = self._heading
        self._heading_line.tags = list(self._tags)
        self._heading_line.mark_dirty()
        self._update_line_item(0, self._heading_line)

    def _find_clock_line_indices(self) -> list[int]:
        indices: list[int] = []
        for index, line in enumerate(self._lines):
            if OrgDateClock.from_str(line):
                indices.append(index)
        return indices

    def _coerce_sdc_date(self, value: Any, cls: type[TOrgDate]) -> TOrgDate:
        if value is None:
            return cls(None)
        if isinstance(value, OrgDate):
            return cls(value.start, value.end, active=value.is_active())
        return cls(value)

    def _update_sdc_entry(self, label: str, date: OrgDate) -> None:
        if self._sdc_line is None:
            if not date:
                return
            self._sdc_line = SdcLine.from_entries({label: date})
            self._insert_line_item(1, self._sdc_line)
            return
        self._sdc_line.update_entry(label, date)
        if self._sdc_line.is_empty():
            index = self._line_items.index(self._sdc_line)
            self._remove_line_item(index)
            self._sdc_line = None
        else:
            self._lines_dirty = True

    def _format_clock_line(self, clock: OrgDateClock) -> ClockLine:
        prefix = "  CLOCK: "
        suffix = ""
        if clock.has_end():
            minutes = int(clock.duration.total_seconds() // 60)
            hours, mins = divmod(minutes, 60)
            suffix = f" => {hours}:{mins:02d}"
        return ClockLine(f"{prefix}{clock}{suffix}", prefix, clock, suffix)

    def _sync_logbook_drawers_from_lines(self) -> None:
        self._logbook_drawers = []
        in_logbook = False
        start_line: LogbookStartLine | None = None
        entries: list[RepeatTaskLine] = []
        indent = ""
        index = 0
        while index < len(self._line_items):
            line_item = self._line_items[index]
            line = line_item.render()
            if line.lstrip().startswith("#"):
                index += 1
                continue
            if line.strip().upper() == ":LOGBOOK:":
                start_line = LogbookStartLine(line)
                self._update_line_item(index, start_line)
                in_logbook = True
                entries = []
                indent = line[: len(line) - len(line.lstrip(" "))]
                index += 1
                continue
            if in_logbook and line.strip().upper() == ":END:":
                end_line = LogbookEndLine(line)
                self._update_line_item(index, end_line)
                assert start_line is not None
                self._logbook_drawers.append(LogbookDrawer(start_line, end_line, entries, indent, generated=False))
                in_logbook = False
                index += 1
                continue
            if in_logbook:
                entry = RepeatTaskLine.from_line(line)
                if entry is not None:
                    self._update_line_item(index, entry)
                    entries.append(entry)
                index += 1
                continue
            entry = RepeatTaskLine.from_line(line)
            if entry is not None:
                self._update_line_item(index, entry)
            index += 1

    def _repeat_task_lines_in_order(self) -> list[RepeatTaskLine]:
        return [item for item in self._line_items if isinstance(item, RepeatTaskLine)]

    def _logbook_drawer_insert_index(self) -> int:
        index = 1
        while index < len(self._line_items):
            item = self._line_items[index]
            if isinstance(item, (SdcLine, ClockLine)):
                index += 1
                continue
            if isinstance(item, (PropertyDrawerStartLine, PropertyDrawerEndLine, PropertyEntryLine)):
                index += 1
                continue
            break
        return index

    def _logbook_drawer_indent(self, insert_at: int) -> str:
        if insert_at > 0:
            before = self._line_items[insert_at - 1].render()
            indent = before[: len(before) - len(before.lstrip(" "))]
            return indent or "  "
        return "  "

    def _create_logbook_drawer(self) -> LogbookDrawer:
        insert_at = self._logbook_drawer_insert_index()
        indent = self._logbook_drawer_indent(insert_at)
        start_line = LogbookStartLine(f"{indent}:LOGBOOK:")
        end_line = LogbookEndLine(f"{indent}:END:")
        self._insert_line_item(insert_at, start_line)
        self._insert_line_item(insert_at + 1, end_line)
        drawer = LogbookDrawer(start_line, end_line, [], indent, generated=True)
        self._logbook_drawers.append(drawer)
        return drawer

    def _property_drawer_insert_index(self) -> int:
        index = 1
        while index < len(self._line_items):
            item = self._line_items[index]
            if isinstance(item, (SdcLine, ClockLine)):
                index += 1
                continue
            break
        return index

    def _property_drawer_indent(self, insert_at: int) -> str:
        if insert_at > 0:
            before = self._line_items[insert_at - 1].render()
            return before[: len(before) - len(before.lstrip(" "))] or "  "
        return "  "

    # The following ``_iparse_*`` methods are simple generator based
    # parser.  See ``_parse_pre`` for how it is used.  The principle
    # is simple: these methods get an iterator and returns an iterator.
    # If the item returned by the input iterator must be dedicated to
    # the parser, do not yield the item or yield it as-is otherwise.

    def _iparse_sdc(self, ilines: Iterator[str]) -> Iterator[str]:
        """
        Parse SCHEDULED, DEADLINE and CLOSED time tamps.

        They are assumed be in the first line.

        """
        try:
            line = next(ilines)
        except StopIteration:
            return
        sdc_line = SdcLine.from_line(line)
        if sdc_line is not None:
            self._sdc_line = sdc_line
            self._update_line_item(1, sdc_line)
            scheduled_entry = sdc_line._entries.get("SCHEDULED")
            deadline_entry = sdc_line._entries.get("DEADLINE")
            closed_entry = sdc_line._entries.get("CLOSED")
            self._scheduled = (
                cast(OrgDateScheduled, scheduled_entry.date) if scheduled_entry is not None else OrgDateScheduled(None)
            )
            self._deadline = (
                cast(OrgDateDeadline, deadline_entry.date) if deadline_entry is not None else OrgDateDeadline(None)
            )
            self._closed = cast(OrgDateClosed, closed_entry.date) if closed_entry is not None else OrgDateClosed(None)
        else:
            (self._scheduled, self._deadline, self._closed) = parse_sdc(line)
            if not (self._scheduled or self._deadline or self._closed):
                yield line  # when none of them were found

        for line in ilines:
            yield line

    def _iparse_clock(self, ilines: Iterator[str]) -> Iterator[str]:
        self._clocklist = []
        self._clock_lines = []
        for line in ilines:
            cl = OrgDateClock.from_str(line)
            if cl:
                self._clocklist.append(cl)
                clock_line = ClockLine.from_line(line)
                if clock_line is not None:
                    self._clock_lines.append(clock_line)
                    index = next(self._clock_line_indices, None)
                    if index is not None:
                        self._update_line_item(index, clock_line)
            else:
                yield line

    def _iparse_timestamps(self, ilines: Iterator[str]) -> Iterator[str]:
        self._timestamps = []
        self._timestamps.extend(OrgDate.list_from_str(self._heading))
        for l in ilines:
            self._timestamps.extend(OrgDate.list_from_str(l))
            yield l

    def _iparse_repeated_tasks(self, ilines: Iterator[str]) -> Iterator[str]:
        self._repeated_tasks = []
        for line in ilines:
            if line.lstrip().startswith("#"):
                yield line
                continue
            match = self._repeated_tasks_re.search(line)
            if match:
                # FIXME: move this parsing to OrgDateRepeatedTask.from_str
                mdict = match.groupdict()
                done_state = mdict['done']
                todo_state = mdict['todo']
                date = OrgDate.from_str(mdict['date'])
                self._repeated_tasks.append(OrgDateRepeatedTask(date.start, todo_state, done_state))
            else:
                yield line

    _repeated_tasks_re = re.compile(
        r'''
        \s*- \s+
        State \s+ "(?P<done> [^"]+)" \s+
        from  \s+ "(?P<todo> [^"]+)" \s+
        \[ (?P<date> [^\]]+) \]''',
        re.VERBOSE,
    )

    def get_heading(self, format: str = 'plain') -> str:  # noqa: A002
        """
        Return a string of head text without tags and TODO keywords.

        >>> from orgparse import loads
        >>> node = loads('* TODO Node 1').children[0]
        >>> node.get_heading()
        'Node 1'

        It strips off inline markup by default (``format='plain'``).
        You can get the original raw string by specifying
        ``format='raw'``.

        >>> node = loads('* [[link][Node 1]]').children[0]
        >>> node.get_heading()
        'Node 1'
        >>> node.get_heading(format='raw')
        '[[link][Node 1]]'

        """
        return self._get_text(self._heading, format)

    @property
    def heading(self) -> str:
        """Alias of ``.get_heading(format='plain')``."""
        return self.get_heading()

    @heading.setter
    def heading(self, value: str) -> None:
        self._heading = value
        self._update_heading_line()

    @property
    def level(self):
        """
        Level attribute of this node.  Top level node is level 1.

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node 1
        ... ** Node 2
        ... ''')
        >>> (n1, n2) = list(root[1:])
        >>> root.level
        0
        >>> n1.level
        1
        >>> n2.level
        2

        """
        return self._level

    @property
    def priority(self) -> str | None:
        """
        Priority attribute of this node.  It is None if undefined.

        >>> from orgparse import loads
        >>> (n1, n2) = loads('''
        ... * [#A] Node 1
        ... * Node 2
        ... ''').children
        >>> n1.priority
        'A'
        >>> n2.priority is None
        True

        """
        return self._priority

    @priority.setter
    def priority(self, value: str | None) -> None:
        if value == "":
            value = None
        self._priority = value
        self._update_heading_line()

    def _get_tags(self, *, inher: bool = False) -> set[str]:
        tags = set(self._tags)
        if inher:
            parent = self.get_parent()
            if parent:
                return tags | parent._get_tags(inher=True)
        return tags

    @property
    def todo(self) -> Optional[str]:
        """
        A TODO keyword of this node if exists or None otherwise.

        >>> from orgparse import loads
        >>> root = loads('* TODO Node 1')
        >>> root.children[0].todo
        'TODO'

        """
        return self._todo

    @todo.setter
    def todo(self, value: Optional[str]) -> None:
        if value == "":
            value = None
        self._todo = value
        self._update_heading_line()

    @property
    def tags(self) -> set[str]:
        return self._get_tags(inher=True)

    @tags.setter
    def tags(self, value: Iterable[str] | None) -> None:
        self._tags = self._normalize_tags(value)
        self._update_heading_line()

    @property
    def scheduled(self):
        """
        Return scheduled timestamp

        :rtype: a subclass of :class:`orgparse.date.OrgDate`

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   SCHEDULED: <2012-02-26 Sun>
        ... ''')
        >>> root.children[0].scheduled
        OrgDateScheduled((2012, 2, 26))

        """
        return self._scheduled

    @scheduled.setter
    def scheduled(self, value: Any) -> None:
        date = self._coerce_sdc_date(value, OrgDateScheduled)
        self._scheduled = date
        self._update_sdc_entry("SCHEDULED", date)

    @property
    def deadline(self):
        """
        Return deadline timestamp.

        :rtype: a subclass of :class:`orgparse.date.OrgDate`

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   DEADLINE: <2012-02-26 Sun>
        ... ''')
        >>> root.children[0].deadline
        OrgDateDeadline((2012, 2, 26))

        """
        return self._deadline

    @deadline.setter
    def deadline(self, value: Any) -> None:
        date = self._coerce_sdc_date(value, OrgDateDeadline)
        self._deadline = date
        self._update_sdc_entry("DEADLINE", date)

    @property
    def closed(self):
        """
        Return timestamp of closed time.

        :rtype: a subclass of :class:`orgparse.date.OrgDate`

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   CLOSED: [2012-02-26 Sun 21:15]
        ... ''')
        >>> root.children[0].closed
        OrgDateClosed((2012, 2, 26, 21, 15, 0))

        """
        return self._closed

    @closed.setter
    def closed(self, value: Any) -> None:
        date = self._coerce_sdc_date(value, OrgDateClosed)
        self._closed = date
        self._update_sdc_entry("CLOSED", date)

    @property
    def clock(self):
        """
        Return a list of clocked timestamps

        :rtype: a list of a subclass of :class:`orgparse.date.OrgDate`

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] =>  0:05
        ... ''')
        >>> root.children[0].clock
        [OrgDateClock((2012, 2, 26, 21, 10, 0), (2012, 2, 26, 21, 15, 0))]

        """
        return self._clocklist

    @clock.setter
    def clock(self, value: Iterable[OrgDateClock]) -> None:
        new_clocks = list(value)
        self._clocklist = new_clocks
        existing_indices = [i for i, item in enumerate(self._line_items) if isinstance(item, ClockLine)]
        if existing_indices:
            for i, clock in enumerate(new_clocks):
                if i < len(existing_indices):
                    line_item = self._line_items[existing_indices[i]]
                    if isinstance(line_item, ClockLine):
                        line_item.update(clock)
                    else:
                        self._update_line_item(existing_indices[i], self._format_clock_line(clock))
                else:
                    insert_at = existing_indices[-1] + (i - len(existing_indices) + 1)
                    self._insert_line_item(insert_at, self._format_clock_line(clock))
            for i in reversed(existing_indices[len(new_clocks) :]):
                self._remove_line_item(i)
        else:
            insert_at = 1
            if self._sdc_line is not None:
                insert_at = self._line_items.index(self._sdc_line) + 1
            for i, clock in enumerate(new_clocks):
                self._insert_line_item(insert_at + i, self._format_clock_line(clock))
        self._lines_dirty = True

    def has_date(self):
        """
        Return ``True`` if it has any kind of timestamp
        """
        return self.scheduled or self.deadline or self.datelist or self.rangelist

    @property
    def repeated_tasks(self):
        """
        Get repeated tasks marked DONE in an entry having repeater.

        :rtype: list of :class:`orgparse.date.OrgDateRepeatedTask`

        >>> from orgparse import loads
        >>> node = loads('''
        ... * TODO Pay the rent
        ...   DEADLINE: <2005-10-01 Sat +1m>
        ...   - State "DONE"  from "TODO"  [2005-09-01 Thu 16:10]
        ...   - State "DONE"  from "TODO"  [2005-08-01 Mon 19:44]
        ...   - State "DONE"  from "TODO"  [2005-07-01 Fri 17:27]
        ... ''').children[0]
        >>> node.repeated_tasks            # doctest: +NORMALIZE_WHITESPACE
        [OrgDateRepeatedTask((2005, 9, 1, 16, 10, 0), 'TODO', 'DONE'),
         OrgDateRepeatedTask((2005, 8, 1, 19, 44, 0), 'TODO', 'DONE'),
         OrgDateRepeatedTask((2005, 7, 1, 17, 27, 0), 'TODO', 'DONE')]
        >>> node.repeated_tasks[0].before
        'TODO'
        >>> node.repeated_tasks[0].after
        'DONE'

        Repeated tasks in ``:LOGBOOK:`` can be fetched by the same code.

        >>> node = loads('''
        ... * TODO Pay the rent
        ...   DEADLINE: <2005-10-01 Sat +1m>
        ...   :LOGBOOK:
        ...   - State "DONE"  from "TODO"  [2005-09-01 Thu 16:10]
        ...   - State "DONE"  from "TODO"  [2005-08-01 Mon 19:44]
        ...   - State "DONE"  from "TODO"  [2005-07-01 Fri 17:27]
        ...   :END:
        ... ''').children[0]
        >>> node.repeated_tasks            # doctest: +NORMALIZE_WHITESPACE
        [OrgDateRepeatedTask((2005, 9, 1, 16, 10, 0), 'TODO', 'DONE'),
         OrgDateRepeatedTask((2005, 8, 1, 19, 44, 0), 'TODO', 'DONE'),
         OrgDateRepeatedTask((2005, 7, 1, 17, 27, 0), 'TODO', 'DONE')]

        See: `(info "(org) Repeated tasks")
        <http://orgmode.org/manual/Repeated-tasks.html>`_

        """
        return self._repeated_tasks

    @repeated_tasks.setter
    def repeated_tasks(self, value: Iterable[OrgDateRepeatedTask]) -> None:
        new_repeats = list(value)
        self._repeated_tasks = new_repeats
        existing_lines = self._repeat_task_lines_in_order()

        for line, repeat in zip(existing_lines, new_repeats):
            line.update_repeat(repeat)

        for line in reversed(existing_lines[len(new_repeats) :]):
            index = self._line_items.index(line)
            self._remove_line_item(index)
            for drawer in self._logbook_drawers:
                if line in drawer.entries:
                    drawer.entries.remove(line)

        for repeat in new_repeats[len(existing_lines) :]:
            insert_drawer: LogbookDrawer | None
            insert_index: int
            indent: str
            (insert_drawer, insert_index, indent) = self._repeat_task_insert_target(existing_lines)
            entry = RepeatTaskLine.from_repeat(repeat, indent)
            self._insert_line_item(insert_index, entry)
            if insert_drawer is not None:
                insert_drawer.entries.append(entry)
            existing_lines.append(entry)

        self._remove_empty_generated_logbooks()
        self._lines_dirty = True

    def _repeat_task_insert_target(
        self,
        existing_lines: list[RepeatTaskLine],
    ) -> tuple[LogbookDrawer | None, int, str]:
        if self._logbook_drawers:
            drawer = self._logbook_drawers[-1]
            insert_index = self._line_items.index(drawer.end_line)
            return (drawer, insert_index, drawer.indent)
        if existing_lines:
            last_line = existing_lines[-1]
            insert_index = self._line_items.index(last_line) + 1
            return (None, insert_index, last_line.indent)
        drawer = self._create_logbook_drawer()
        insert_index = self._line_items.index(drawer.end_line)
        return (drawer, insert_index, drawer.indent)

    def _remove_empty_generated_logbooks(self) -> None:
        for drawer in list(self._logbook_drawers):
            if drawer.generated and not drawer.entries:
                start_index = self._line_items.index(drawer.start_line)
                end_index = self._line_items.index(drawer.end_line)
                for index in range(end_index, start_index - 1, -1):
                    self._remove_line_item(index)
                self._logbook_drawers.remove(drawer)


def parse_lines(lines: Iterable[str], filename, env=None) -> OrgNode:
    if not env:
        env = OrgEnv(filename=filename)
    elif env.filename != filename:
        raise ValueError('If env is specified, filename must match')

    # parse into node of list (environment will be parsed)
    ch1, ch2 = itertools.tee(lines_to_chunks(lines))
    linenos = itertools.accumulate(itertools.chain([0], (len(c) for c in ch1)))
    nodes = env.from_chunks(ch2)
    nodelist = []
    for lineno, node in zip(linenos, nodes):
        lineno += 1  # in text editors lines are 1-indexed
        node.linenumber = lineno
        nodelist.append(node)
    # parse headings (level, TODO, TAGs, and heading)
    nodelist[0]._index = 0
    # parse the root node
    nodelist[0]._parse_pre()
    for i, node in enumerate(nodelist[1:], 1):  # nodes except root node
        node._index = i
        node._parse_pre()
    env._nodes = nodelist
    return nodelist[0]  # root
