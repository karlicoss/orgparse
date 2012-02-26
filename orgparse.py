import re
import datetime

__all__ = ["load", "loads", "loadi"]


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


def parse_heaindg_todos(heading, todo_candidates):
    """
    Get TODO keyword and heading without TODO keyword.

    >>> todos = ['TODO', 'DONE']
    >>> parse_heaindg_todos('Normal heading', todos)
    ('Normal heading', None)
    >>> parse_heaindg_todos('TODO Heading', todos)
    ('Heading', 'TODO')

    """
    for todo in todo_candidates:
        todows = '{0} '.format(todo)
        if heading.startswith(todows):
            return (heading[len(todows):], todo)
    return (heading, None)


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


def get_datetime(year, month, day, hour=None, minute=None, second=None):
    if "" in (year, month, day):
        raise ValueError("First three arguments must not contain empty str")
    if None in (year, month, day):
        raise ValueError("First three arguments must not contain None")

    ymdhms = []
    for a in [year, month, day, hour, minute, second]:
        if a != None and a != "":
            ymdhms.append(int(a))

    if len(ymdhms) > 3:
        return datetime.datetime(*ymdhms)
    else:
        return datetime.date(*ymdhms)


def re_compile_date():
    """
    >>> re_date = re_compile_date()
    >>> re_date.match('')
    >>> m = re_date.match('<2010-06-21 Mon>')
    >>> m.group()
    '<2010-06-21 Mon>'
    >>> m.group(1)
    >>> m.group(16)
    '<2010-06-21 Mon>'
    >>> m = re_date.match('<2010-06-21 Mon 12:00>--<2010-06-21 Mon 12:00>')
    >>> m.group()
    '<2010-06-21 Mon 12:00>--<2010-06-21 Mon 12:00>'
    >>> m.group(1)
    '<2010-06-21 Mon 12:00>--<2010-06-21 Mon 12:00>'
    >>> m.group(16)
    """
    date_pattern = "<(\d+)\-(\d+)\-(\d+)([^>\d]*)((\d+)\:(\d+))?>"
    re_date = re.compile('(%(dtp)s--%(dtp)s)|(%(dtp)s)'
                         % dict(dtp=date_pattern))
    return re_date


def parse_daterangelist(string):
    datelist = []
    rangelist = []
    for dm in RE_DATE.findall(string):
        if dm[0]:
            d1 = get_datetime(dm[1], dm[2], dm[3], dm[6], dm[7])
            d2 = get_datetime(dm[8], dm[9], dm[10], dm[13], dm[14])
            rangelist.append((d1, d2))
        else:
            dt = get_datetime(dm[16], dm[17], dm[18], dm[21], dm[22])
            datelist.append(dt)
    return (datelist, rangelist)

RE_DATE = re_compile_date()


def parse_scheduled(line):
    """
    Get SCHEDULED from given string.

    Return datetime object if found else None.
    """
    sdre = RE_SCHEDULED.search(line)
    if sdre:
        if sdre.group(4) == None:
            sched_date = datetime.date(int(sdre.group(1)),
                                       int(sdre.group(2)),
                                       int(sdre.group(3)))
        else:
            sched_date = datetime.datetime(int(sdre.group(1)),
                                           int(sdre.group(2)),
                                           int(sdre.group(3)),
                                           int(sdre.group(5)),
                                           int(sdre.group(6)))
    else:
        sched_date = None
    return sched_date

RE_SCHEDULED = re.compile(
    'SCHEDULED:\s+<(\d+)\-(\d+)\-(\d+)[^>\d]*((\d+)\:(\d+))?>')


def parse_deadline(line):
    """
    Get DEADLINE from given string.

    Return datetime object if found else None.
    """
    ddre = RE_DEADLINE.search(line)
    if ddre:
        if ddre.group(4) == None:
            deadline_date = datetime.date(int(ddre.group(1)),
                                          int(ddre.group(2)),
                                          int(ddre.group(3)))
        else:
            deadline_date = datetime.datetime(int(ddre.group(1)),
                                              int(ddre.group(2)),
                                              int(ddre.group(3)),
                                              int(ddre.group(5)),
                                              int(ddre.group(6)))
    else:
        deadline_date = None
    return deadline_date

RE_DEADLINE = re.compile(
    'DEADLINE:\s+<(\d+)\-(\d+)\-(\d+)[^>\d]*((\d+)\:(\d+))?>')


def parse_closed(line):
    """
    Get CLOSED from given string.

    Return datetime object if found else None.
    """
    match = RE_CLOSED.search(line)
    if match:
        if match.group(4) == None:
            closed_date = datetime.date(int(match.group(1)),
                                        int(match.group(2)),
                                        int(match.group(3)))
        else:
            closed_date = datetime.datetime(int(match.group(1)),
                                            int(match.group(2)),
                                            int(match.group(3)),
                                            int(match.group(5)),
                                            int(match.group(6)))
    else:
        closed_date = None
    return closed_date

RE_CLOSED = re.compile(
    r'CLOSED:\s+\[(\d+)\-(\d+)\-(\d+)[^\]\d]*((\d+)\:(\d+))?\]')


def parse_clock(line):
    """
    Get CLOCK from given string.

    Return three tuple (start, stop, length) which is datetime object
    of start time, datetime object of stop time and length in minute.

    """
    match = RE_CLOCK.search(line)
    if match is None:
        return None
    groups = [int(d) for d in match.groups()]
    ymdhm1 = groups[:5]
    ymdhm2 = groups[5:10]
    hm3 = groups[10:]
    return (
        datetime.datetime(*ymdhm1),
        datetime.datetime(*ymdhm2),
        hm3[0] * 60 + hm3[1],
    )

RE_CLOCK = re.compile(
    r'CLOCK:\s+'
    r'\[(\d+)\-(\d+)\-(\d+)[^\]\d]*(\d+)\:(\d+)\]--'
    r'\[(\d+)\-(\d+)\-(\d+)[^\]\d]*(\d+)\:(\d+)\]\s+=>\s+(\d+)\:(\d+)'
    )


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

    def __init__(self, todos=['TODO'], dones=['DONE']):
        self._todos = list(todos)
        self._dones = list(dones)
        self._todo_not_specified_in_comment = True

    def add_todo_keys(self, todos, dones):
        if self._todo_not_specified_in_comment:
            self._todos = []
            self._dones = []
            self._todo_not_specified_in_comment = False
        self._todos.extend(todos)
        self._dones.extend(dones)

    def get_todo_keys(self, todo=True, done=True):
        if todo and done:
            return self._todos + self._dones
        elif todo:
            return self._todos
        elif done:
            return self._dones

    def from_chunks(self, chunks):
        yield OrgRootNode.from_chunk(self, next(chunks))
        for chunk in chunks:
            yield OrgNode.from_chunk(self, chunk)


class OrgBaseNode(object):

    def __init__(self, env):
        self.env = env

        # tree structure
        self._next = None
        self._previous = None
        self._parent = None
        self._children = []

        # content
        self._lines = []

    def traverse(self, include_self=True):
        if include_self:
            yield self
        for child in self.get_children():
            for grandchild in child.traverse():
                yield grandchild

    # tree structure

    def set_previous(self, previous):
        self._previous = previous
        previous._next = self   # FIXME: find a better way to do this

    def get_previous(self):
        return self._previous

    def get_next(self):
        return self._next

    def set_parent(self, parent):
        self._parent = parent
        parent.add_children(self)

    def add_children(self, child):
        self._children.append(child)

    def get_parent(self, max_level=None):
        if max_level is None:
            max_level = self.get_level() - 1
        parent = self._parent
        while parent.get_level() > max_level:
            parent = parent.get_parent()
        return parent

    def get_children(self):
        return self._children

    def get_root(self):
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

    def __unicode__(self):
        return u"\n".join(self._lines)

    def __str__(self):
        return unicode(self).encode('utf-8')


class OrgRootNode(OrgBaseNode):

    # getter

    def get_level(self):
        return 0

    def get_tags(self, inher=False):
        return set()


class OrgNode(OrgBaseNode):

    def __init__(self, *args, **kwds):
        super(OrgNode, self).__init__(*args, **kwds)
        self._heading = None
        self._level = None
        self._tags = None
        self._todo = None
        self._properties = {}
        self._scheduled = None
        self._deadline = None
        self._datelist = None
        self._rangelist = None
        self._closed = None
        self._clocklist = None
        self._body_lines = []

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
        ilines = self._iparse_timestamps(ilines)
        self._body_lines = list(ilines)

    def _parse_heading(self):
        heading = self._lines[0]
        (heading, self._level) = parse_heading_level(heading)
        (heading, self._tags) = parse_heading_tags(heading)
        (heading, self._todo) = parse_heaindg_todos(
            heading, self.env.get_todo_keys())
        self._heading = heading

    def _iparse_sdc(self, ilines):
        """
        Parse SCHEDULED, DEADLINE and CLOSED time tamps.

        They are assumed be in the first line.

        """
        line = next(ilines)
        self._scheduled = parse_scheduled(line)
        self._deadline = parse_deadline(line)
        self._closed = parse_closed(line)

        if not (self._scheduled or
                self._deadline or
                self._closed):
            yield line  # when none of them were found

        for line in ilines:
            yield line

    def _iparse_clock(self, ilines):
        self._clocklist = clocklist = []
        for line in ilines:
            cl = parse_clock(line)
            if cl:
                clocklist.append(cl)
            else:
                yield line

    def _iparse_timestamps(self, ilines):
        self._datelist = datelist = []
        self._rangelist = rangelist = []
        for line in ilines:
            (d, r) = parse_daterangelist(line)
            datelist.extend(d)
            rangelist.extend(r)
            yield line

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

    # getter

    def get_body(self):
        if self._lines:
            return "\n".join(self._body_lines)

    def get_heading(self):
        return self._heading

    def get_level(self):
        return self._level

    def get_priority(self):
        raise NotImplementedError  # FIXME: implement!

    def get_tags(self, inher=False):
        tags = set(self._tags)
        if inher:
            parent = self.get_parent()
            if parent:
                return tags | parent.get_tags(inher=True)
        return tags

    def get_todo(self):
        return self._todo

    def get_property(self, key, val=None):
        return self._properties.get(key, val)

    def get_properties(self):
        return self._properties

    def get_scheduled(self):
        return self._scheduled

    def get_deadline(self):
        return self._deadline

    def get_datelist(self):
        return self._datelist

    def get_rangelist(self):
        return self._rangelist

    def get_closed(self):
        return self._closed

    def get_clock(self):
        return self._clocklist

    def has_date(self):
        return (self.get_scheduled() or
                self.get_deadline() or
                self.get_datelist() or
                self.get_rangelist())

    def get_repeated_tasks(self):
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
        raise NotImplementedError  # FIXME: implement!


def load(path):
    """Load org-mode document from a file."""
    if isinstance(path, basestring):
        orgfile = file(path)
    else:
        orgfile = path
    return loadi(l.rstrip('\n') for l in orgfile.readlines())


def loads(string):
    """Load org-mode document from a string"""
    return loadi(string.splitlines())


def loadi(lines):
    """Load org-mode document from an iterative object"""
    env = OrgEnv()
    # parse into node of list (environment will be parsed)
    nodelist = list(env.from_chunks(lines_to_chunks(lines)))
    # parse headings (level, TODO, TAGs, and heading)
    for node in nodelist[1:]:   # nodes except root node
        node._parse_pre()
    # set the node tree structure
    for (n1, n2) in zip(nodelist[:-1], nodelist[1:]):
        level_n1 = n1.get_level()
        level_n2 = n2.get_level()
        if level_n1 == level_n2:
            n2.set_parent(n1.get_parent())
            n2.set_previous(n1)
        elif level_n1 < level_n2:
            n2.set_parent(n1)
        else:
            # FIXME: add more tests for this path
            np = n1.get_parent(max_level=n2.get_level())
            n2.set_parent(np.get_parent())
            n2.set_previous(np)
    return nodelist[0]  # root
