import re
import itertools
try:
    from collections import Sequence
except ImportError:
    from collections.abc import Sequence

from orgparse.date import OrgDate, OrgDateClock, parse_sdc
from orgparse.py3compat import PY3, unicode


def lines_to_chunks(lines):
    chunk = []
    for l in lines:
        if RE_NODE_HEADER.search(l):
            yield chunk
            chunk = []
        chunk.append(l)
    yield chunk

RE_NODE_HEADER = re.compile(r"^\*+ ")


def parse_heading_level(heading):
    """
    Get star-stripped heading and its level

    >>> parse_heading_level('* Heading')
    ('Heading', 1)
    >>> parse_heading_level('******** Heading')
    ('Heading', 8)
    >>> parse_heading_level('not heading')  # None

    """
    match = RE_HEADING_STARS.search(heading)
    if match:
        return (match.group(2), len(match.group(1)))

RE_HEADING_STARS = re.compile('^(\*+)\s*(.*?)\s*$')


def parse_heading_tags(heading):
    """
    Get first tags and heading without tags

    >>> parse_heading_tags('HEADING')
    ('HEADING', [])
    >>> parse_heading_tags('HEADING :TAG1:TAG2:')
    ('HEADING', ['TAG1', 'TAG2'])
    >>> parse_heading_tags('HEADING: this is still heading :TAG1:TAG2:')
    ('HEADING: this is still heading', ['TAG1', 'TAG2'])

    """
    match = RE_HEADING_TAGS.search(heading)
    if match:
        heading = match.group(1)
        tagstr = match.group(2)
        tags = tagstr.split(':')
    else:
        tags = []
    return (heading, tags)

RE_HEADING_TAGS = re.compile(r'(.*?)\s*:([a-zA-Z0-9_:]+):\s*$')


def parse_heading_todos(heading, todo_candidates):
    """
    Get TODO keyword and heading without TODO keyword.

    >>> todos = ['TODO', 'DONE']
    >>> parse_heading_todos('Normal heading', todos)
    ('Normal heading', None)
    >>> parse_heading_todos('TODO Heading', todos)
    ('Heading', 'TODO')

    """
    for todo in todo_candidates:
        todows = '{0} '.format(todo)
        if heading.startswith(todows):
            return (heading[len(todows):], todo)
    return (heading, None)


def parse_heading_priority(heading):
    """
    Get priority and heading without priority field..

    >>> parse_heading_priority('HEADING')
    ('HEADING', None)
    >>> parse_heading_priority('[#A] HEADING')
    ('HEADING', 'A')
    >>> parse_heading_priority('[#0] HEADING')
    ('HEADING', '0')
    >>> parse_heading_priority('[#A]')
    ('', 'A')

    """
    match = RE_HEADING_PRIORITY.search(heading)
    if match:
        return (match.group(2), match.group(1))
    else:
        return (heading, None)

RE_HEADING_PRIORITY = re.compile(r'^\s*\[#([A-Z0-9])\] ?(.*)$')


def parse_property(line):
    """
    Get property from given string.

    >>> parse_property(':Some_property: some value')
    ('Some_property', 'some value')
    >>> parse_property(':Effort: 1:10')
    ('Effort', 70)

    """
    prop_key = None
    prop_val = None
    match = RE_PROP.search(line)
    if match:
        prop_key = match.group(1)
        prop_val = match.group(2)
        if prop_key == 'Effort':
            (h, m) = prop_val.split(":", 2)
            if h.isdigit() and m.isdigit():
                prop_val = int(h) * 60 + int(m)
    return (prop_key, prop_val)

RE_PROP = re.compile('^\s*:(.*?):\s*(.*?)\s*$')


def parse_comment(line):
    """
    Parse special comment such as ``#+SEQ_TODO``

    >>> parse_comment('#+SEQ_TODO: TODO | DONE')
    ('SEQ_TODO', 'TODO | DONE')
    >>> parse_comment('# not a special comment')  # None

    """
    if line.startswith('#+'):
        comment = line.lstrip('#+').split(':', 1)
        if len(comment) == 2:
            return (comment[0], comment[1].strip())


def parse_seq_todo(line):
    """
    Parse value part of SEQ_TODO comment

    >>> parse_seq_todo('TODO | DONE')
    (['TODO'], ['DONE'])
    >>> parse_seq_todo('Fred Sara Lucy Mike | DONE')
    (['Fred', 'Sara', 'Lucy', 'Mike'], ['DONE'])

    """
    todo_done = line.split('|', 1)
    if len(todo_done) == 2:
        (todos, dones) = todo_done
    else:
        (todos, dones) = (line, '')
    return (todos.split(), dones.split())


class OrgEnv(object):

    """
    Information global to the file (e.g, TODO keywords).
    """

    def __init__(self, todos=['TODO'], dones=['DONE'],
                 filename='<undefined>'):
        self._todos = list(todos)
        self._dones = list(dones)
        self._todo_not_specified_in_comment = True
        self._filename = filename
        self._nodes = []

    @property
    def nodes(self):
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
    def filename(self):
        """
        Return a path to the source file or similar information.

        If the org objects are not loaded from a file, this value
        will be a string of the form ``<SOME_TEXT>``.

        :rtype: str

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
    ... ''')
    >>> for node in root:
    ...     print(node)
    <BLANKLINE>
    * Heading 1
    ** Heading 2
    *** Heading 3

    Note that the first blank line is due to the root node, as
    iteration contains the object itself.  To skip that, use
    slice access ``[1:]``:

    >>> for node in root[1:]:
    ...     print(node)
    * Heading 1
    ** Heading 2
    *** Heading 3

    It also support sequence protocol.

    >>> print(root[1])
    * Heading 1
    >>> root[0] is root  # index 0 means itself
    True
    >>> len(root)   # remember, sequence contains itself
    4

    As what ``root[N]`` returns is also an iterative, you can
    use ``root[1]`` instead of ``root[1:]``.

    >>> for node in root[1]:
    ...     print(node)
    * Heading 1
    ** Heading 2
    *** Heading 3

    """

    def __init__(self, env, index=None):
        """
        Create a :class:`OrgBaseNode` object.

        :type env: :class:`OrgEnv`
        :arg  env: This will be set to the :attr:`env` attribute.

        """
        self.env = env

        # content
        self._lines = []

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
        for node in self.env._nodes[self._index + 1:]:
            if node.level > level:
                yield node

    def __len__(self):
        return sum(1 for _ in self)

    def __nonzero__(self):
        # As self.__len__ returns non-zero value always this is not
        # needed.  This function is only for performance.
        return True

    __bool__ = __nonzero__  # PY3

    def __getitem__(self, key):
        if isinstance(key, slice):
            return itertools.islice(self, key.start, key.stop, key.step)
        elif isinstance(key, int):
            if key < 0:
                key += len(self)
            for (i, node) in enumerate(self):
                if i == key:
                    return node
            raise IndexError("Out of range {0}".format(key))
        else:
            raise TypeError("Inappropriate type {0} for {1}"
                            .format(type(key), type(self)))

    # tree structure

    def _find_same_level(self, iterable):
        for node in iterable:
            if node.level < self.level:
                return
            if node.level == self.level:
                return node

    @property
    def previous_same_level(self):
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
        return self._find_same_level(reversed(self.env._nodes[:self._index]))

    @property
    def next_same_level(self):
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
        return self._find_same_level(self.env._nodes[self._index + 1:])

    # FIXME: cache parent node
    def _find_parent(self):
        for node in reversed(self.env._nodes[:self._index]):
            if node.level < self.level:
                return node

    def get_parent(self, max_level=None):
        """
        Return a parent node.

        :arg int max_level:
            In the normally structured org file, it is a level
            of the ancestor node to return.  For example,
            ``get_parent(max_level=0)`` returns a root node.

            In general case, it specify a maximum level of the
            desired ancestor node.  If there is no ancestor node
            which level is equal to ``max_level``, this function
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
        nodeiter = iter(self.env._nodes[self._index + 1:])
        node = next(nodeiter)
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

        """
        return list(self._find_children())

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

    # parser

    @classmethod
    def from_chunk(cls, env, lines):
        self = cls(env)
        self._lines = lines
        self._parse_comments()
        return self

    def _parse_comments(self):
        special_comments = {}
        for line in self._lines:
            parsed = parse_comment(line)
            if parsed:
                (key, val) = parsed
                special_comments.setdefault(key, []).append(val)
        self._special_comments = special_comments
        # parse TODO keys and store in OrgEnv
        for todokey in ['TODO', 'SEQ_TODO', 'TYP_TODO']:
            for val in special_comments.get(todokey, []):
                self.env.add_todo_keys(*parse_seq_todo(val))

    # misc

    @property
    def level(self):
        """
        Level of this node.

        :rtype: int

        """
        raise NotImplemented

    def _get_tags(self, inher=False):
        """
        Return tags

        :arg bool inher:
            Mix with tags of all ancestor nodes if ``True``.

        :rtype: set

        """
        return set()

    @property
    def tags(self):
        """
        Tag of this and parents node.

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
    def shallow_tags(self):
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

    def __unicode__(self):
        return unicode("\n").join(self._lines)

    if PY3:
        __str__ = __unicode__
    else:
        def __str__(self):
            return unicode(self).encode('utf-8')


class OrgRootNode(OrgBaseNode):

    """
    Node to represent a file

    See :class:`OrgBaseNode` for other available functions.

    """

    # getter

    @property
    def level(self):
        return 0

    def get_parent(self, max_level=None):
        return None

    # misc

    def is_root(self):
        return True


class OrgNode(OrgBaseNode):

    """
    Node to represent normal org node

    See :class:`OrgBaseNode` for other available functions.

    """

    def __init__(self, *args, **kwds):
        super(OrgNode, self).__init__(*args, **kwds)
        self._heading = None
        self._level = None
        self._tags = None
        self._todo = None
        self._priority = None
        self._properties = {}
        self._scheduled = OrgDate(None)
        self._deadline = OrgDate(None)
        self._closed = OrgDate(None)
        self._timestamps = []
        self._clocklist = []
        self._body_lines = []
        self._repeated_tasks = []

    # parser

    def _parse_pre(self):
        """Call parsers which must be called before tree structuring"""
        self._parse_heading()
        # FIXME: make the following parsers "lazy"
        ilines = iter(self._lines)
        next(ilines)            # skip heading
        ilines = self._iparse_sdc(ilines)
        ilines = self._iparse_clock(ilines)
        ilines = self._iparse_properties(ilines)
        ilines = self._iparse_repeated_tasks(ilines)
        ilines = self._iparse_timestamps(ilines)
        self._body_lines = list(ilines)

    def _parse_heading(self):
        heading = self._lines[0]
        (heading, self._level) = parse_heading_level(heading)
        (heading, self._tags) = parse_heading_tags(heading)
        (heading, self._todo) = parse_heading_todos(
            heading, self.env.all_todo_keys)
        (heading, self._priority) = parse_heading_priority(heading)
        self._heading = heading

    # The following ``_iparse_*`` methods are simple generator based
    # parser.  See ``_parse_pre`` for how it is used.  The principle
    # is simple: these methods get an iterator and returns an iterator.
    # If the item returned by the input iterator must be dedicated to
    # the parser, do not yield the item or yield it as-is otherwise.

    def _iparse_sdc(self, ilines):
        """
        Parse SCHEDULED, DEADLINE and CLOSED time tamps.

        They are assumed be in the first line.

        """
        line = next(ilines)
        (self._scheduled, self._deadline, self._closed) = parse_sdc(line)

        if not (self._scheduled or
                self._deadline or
                self._closed):
            yield line  # when none of them were found

        for line in ilines:
            yield line

    def _iparse_clock(self, ilines):
        self._clocklist = clocklist = []
        for line in ilines:
            cl = OrgDateClock.from_str(line)
            if cl:
                clocklist.append(cl)
            else:
                yield line

    def _iparse_timestamps(self, ilines):
        self._timestamps = timestamps = []
        for l in ilines:
            timestamps.extend(OrgDate.list_from_str(l))
            yield l

    def _iparse_properties(self, ilines):
        self._properties = properties = {}
        in_property_field = False
        for line in ilines:
            if in_property_field:
                if line.find(":END:") >= 0:
                    break
                else:
                    (key, val) = parse_property(line)
                    if key:
                        properties.update({key: val})
            elif line.find(":PROPERTIES:") >= 0:
                in_property_field = True
            else:
                yield line
        for line in ilines:
            yield line

    def _iparse_repeated_tasks(self, ilines):
        self._repeated_tasks = repeated_tasks = []
        for line in ilines:
            match = self._repeated_tasks_re.search(line)
            if match:
                mdict = match.groupdict()
                done_state = mdict['done']
                todo_state = mdict['todo']
                date = OrgDate.from_str(mdict['date'])
                repeated_tasks.append((done_state, todo_state, date))
            else:
                yield line

    _repeated_tasks_re = re.compile(
        r'''
        \s+ - \s+
        State \s+ "(?P<done> [^"]+)" \s+
        from  \s+ "(?P<todo> [^"]+)" \s+
        \[ (?P<date> [^\]]+) \]''',
        re.VERBOSE)

    # getter

    @property
    def body(self):
        """Return a string of body text."""
        if self._lines:
            return "\n".join(self._body_lines)

    @property
    def heading(self):
        """Return a string of head text without tags and TODO keywords."""
        return self._heading

    @property
    def level(self):
        return self._level

    @property
    def priority(self):
        """Return a string to indicate the priority or None if undefined."""
        return self._priority

    def _get_tags(self, inher=False):
        tags = set(self._tags)
        if inher:
            parent = self.get_parent()
            if parent:
                return tags | parent._get_tags(inher=True)
        return tags

    @property
    def todo(self):
        """
        A TODO keyword of this node if exists or None otherwise.

        >>> from orgparse import loads
        >>> root = loads('* TODO Node 1')
        >>> root.children[0].todo
        'TODO'

        """
        return self._todo

    def get_property(self, key, val=None):
        """
        Return property named ``key`` if exists or ``val`` otherwise.

        :arg str key:
            Key of property.

        :arg val:
            Default value to return.

        """
        return self._properties.get(key, val)

    @property
    def properties(self):
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

    def get_timestamps(self, active=False, inactive=False,
                       range=False, point=False):
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
            ts for ts in self._timestamps if
            (((active and ts.is_active()) or
              (inactive and not ts.is_active())) and
             ((range and ts.has_end()) or
              (point and not ts.has_end())))]

    @property
    def datelist(self):
        """
        Alias of ``.get_timestamps(active=True, inactive=True, point=True)``.

        :rtype: list of :class:`orgparse.date.OrgDate` subclasses

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   CLOSED: [2012-02-25 Sat 21:15]
        ...   Some inactive timestamp [2012-02-26 Sun] in body text.
        ...   Some active timestamp <2012-02-27 Mon> in body text.
        ... ''')
        >>> root.children[0].datelist
        [OrgDate((2012, 2, 26), None, False), OrgDate((2012, 2, 27))]

        """
        return self.get_timestamps(active=True, inactive=True, point=True)

    @property
    def rangelist(self):
        """
        Alias of ``.get_timestamps(active=True, inactive=True, range=True)``.

        :rtype: list of :class:`orgparse.date.OrgDate` subclasses

        >>> from orgparse import loads
        >>> root = loads('''
        ... * Node
        ...   CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] => 0:05
        ...   Some inactive time range [2012-02-25 Sat]--[2012-02-27 Mon].
        ...   Some active time range <2012-02-26 Sun>--<2012-02-28 Tue>.
        ... ''')
        >>> root.children[0].rangelist     # doctest: +NORMALIZE_WHITESPACE
        [OrgDate((2012, 2, 25), (2012, 2, 27), False),
         OrgDate((2012, 2, 26), (2012, 2, 28))]

        """
        return self.get_timestamps(active=True, inactive=True, range=True)

    def has_date(self):
        """
        Return ``True`` if it has any kind of timestamp
        """
        return (self.scheduled or
                self.deadline or
                self.datelist or
                self.rangelist)

    @property
    def repeated_tasks(self):
        # FIXME: use OrgDateRpeatedTask
        """
        Get repeated tasks marked DONE in a entry having repeater

        A repeater is something like ``+1m`` in a timestamp,
        such as::

            ** TODO Pay the rent
               DEADLINE: <2005-10-01 Sat +1m>
               - State "DONE"  from "TODO"  [2005-09-01 Thu 16:10]
               - State "DONE"  from "TODO"  [2005-08-01 Mon 19:44]
               - State "DONE"  from "TODO"  [2005-07-01 Fri 17:27]

        See: http://orgmode.org/manual/Repeated-tasks.html

        """
        return self._repeated_tasks


def parse_lines(lines, filename):
    env = OrgEnv(filename=filename)
    # parse into node of list (environment will be parsed)
    nodelist = list(env.from_chunks(lines_to_chunks(lines)))
    # parse headings (level, TODO, TAGs, and heading)
    nodelist[0]._index = 0
    for (i, node) in enumerate(nodelist[1:], 1):   # nodes except root node
        node._index = i
        node._parse_pre()
    env._nodes = nodelist
    return nodelist[0]  # root
