import datetime
import re


def total_seconds(td):
    """Equivalent to `datetime.timedelta.total_seconds`."""
    return float(td.microseconds +
                 (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def total_minutes(td):
    """Alias for ``total_seconds(td) / 60``."""
    return total_seconds(td) / 60


def gene_timestamp_regex(brtype, prefix=None, nocookie=False):
    """
    Generate timetamp regex for active/inactive/nobrace brace type

    :type brtype: {'active', 'inactive', 'nobrace'}
    :arg  brtype:
        It specifies a type of brace.
        active: <>-type; inactive: []-type; nobrace: no braces.

    :type prefix: str or None
    :arg  prefix:
        It will be appended to the head of keys of the "groupdict".
        For example, if prefix is ``'active_'`` the groupdict has
        keys such as ``'active_year'``, ``'active_month'``, and so on.
        If it is None it will be set to ``brtype`` + ``'_'``.

    :type nocookie: bool
    :arg  nocookie:
        Cookie part (e.g., ``'-3d'`` or ``'+6m'``) is not included if
        it is ``True``.  Default value is ``False``.

    >>> timestamp_re = re.compile(
    ...     gene_timestamp_regex('active', prefix=''),
    ...     re.VERBOSE)
    >>> timestamp_re.match('no match')  # returns None
    >>> m = timestamp_re.match('<2010-06-21 Mon>')
    >>> m.group()
    '<2010-06-21 Mon>'
    >>> '{year}-{month}-{day}'.format(**m.groupdict())
    '2010-06-21'
    >>> m = timestamp_re.match('<2005-10-01 Sat 12:30 +7m -3d>')
    >>> m.groupdict() == {
    ...     'year': '2005', 'month': '10', 'day': '01',
    ...     'hour': '12', 'min': '30',
    ...     'repeatpre': '+', 'repeatnum': '7', 'repeatdwmy': 'm',
    ...     'warnpre': '-', 'warnnum': '3', 'warndwmy': 'd'}
    True

    When ``brtype = 'nobrace'``, cookie part cannot be retrieved.

    >>> timestamp_re = re.compile(
    ...     gene_timestamp_regex('nobrace', prefix=''),
    ...     re.VERBOSE)
    >>> timestamp_re.match('no match')  # returns None
    >>> m = timestamp_re.match('2010-06-21 Mon')
    >>> m.group()
    '2010-06-21'
    >>> '{year}-{month}-{day}'.format(**m.groupdict())
    '2010-06-21'
    >>> m = timestamp_re.match('2005-10-01 Sat 12:30 +7m -3d')
    >>> m.groupdict() == {
    ...     'year': '2005', 'month': '10', 'day': '01',
    ...     'hour': '12', 'min': '30'}
    True

    """

    if brtype == 'active':
        (bo, bc) = ('<', '>')
    elif brtype == 'inactive':
        (bo, bc) = (r'\[', r'\]')
    elif brtype == 'nobrace':
        (bo, bc) = ('', '')
    else:
        raise ValueError("brtype='{0!r}' is invalid".format(brtype))

    if brtype == 'nobrace':
        ignore = r'[\s\w]'
    else:
        ignore = '[^{bc}]'.format(bc=bc)

    if prefix is None:
        prefix = '{0}_'.format(brtype)

    regex_date_time = r"""
        (?P<{prefix}year>\d{{4}}) -
        (?P<{prefix}month>\d{{2}}) -
        (?P<{prefix}day>\d{{2}})
        (  # optional time field
           ({ignore}+?)
           (?P<{prefix}hour>\d{{2}}) :
           (?P<{prefix}min>\d{{2}})
        )?
        """
    regex_cookie = r"""
        (  # optional repeater
           ({ignore}+?)
           (?P<{prefix}repeatpre>  [\.\+]{{1,2}})
           (?P<{prefix}repeatnum>  \d+)
           (?P<{prefix}repeatdwmy> [dwmy])
        )?
        (  # optional warning
           ({ignore}+?)
           (?P<{prefix}warnpre>  \-)
           (?P<{prefix}warnnum>  \d+)
           (?P<{prefix}warndwmy> [dwmy])
        )?
        """
    # http://www.pythonregex.com/
    regex = ''.join([
        bo,
        regex_date_time,
        regex_cookie if nocookie or brtype != 'nobrace' else '',
        '({ignore}*?)',
        bc])
    return regex.format(prefix=prefix, ignore=ignore)


TIMESTAMP_NOBRACE_RE = re.compile(
    gene_timestamp_regex('nobrace', prefix=''),
    re.VERBOSE)

TIMESTAMP_RE = re.compile(
    '|'.join((gene_timestamp_regex('active'),
              gene_timestamp_regex('inactive'))),
    re.VERBOSE)


class OrgDate(object):

    _active_default = True
    """
    The default active value.

    When the `active` argument to ``__init__`` is ``None``,
    This value will be used.

    """

    def __init__(self, start, end=None, active=None):
        """
        Create :class:`OrgDate` object

        :type start: datetime, date, tuple, int, float or None
        :type   end: datetime, date, tuple, int, float or None
        :arg  start: Starting date.
        :arg    end: Ending date.

        :type active: bool or None
        :arg  active: Active/inactive flag.
                      None means using its default value, which
                      may be different for different subclasses.

        >>> OrgDate(datetime.date(2012, 2, 10))
        OrgDate((2012, 2, 10))
        >>> OrgDate((2012, 2, 10))
        OrgDate((2012, 2, 10))
        >>> OrgDate((2012, 2))  #doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
            ...
        ValueError: Automatic conversion to the datetime object
        requires at least 3 elements in the tuple.
        Only 2 elements are in the given tuple '(2012, 2)'.
        >>> OrgDate((2012, 2, 10, 12, 20, 30))
        OrgDate((2012, 2, 10, 12, 20, 30))
        >>> OrgDate((2012, 2, 10), (2012, 2, 15), active=False)
        OrgDate((2012, 2, 10), (2012, 2, 15), False)

        OrgDate can be created using unix timestamp:

        >>> OrgDate(datetime.datetime.fromtimestamp(0)) == OrgDate(0)
        True

        """
        self._start = self._to_date(start)
        self._end = self._to_date(end)
        self._active = self._active_default if active is None else active

    @staticmethod
    def _to_date(date):
        if isinstance(date, (tuple, list)):
            if len(date) == 3:
                return datetime.date(*date)
            elif len(date) > 3:
                return datetime.datetime(*date)
            else:
                raise ValueError(
                    "Automatic conversion to the datetime object "
                    "requires at least 3 elements in the tuple. "
                    "Only {0} elements are in the given tuple '{1}'."
                    .format(len(date), date))
        elif isinstance(date, (int, float)):
            return datetime.datetime.fromtimestamp(date)
        else:
            return date

    @staticmethod
    def _date_to_tuple(date):
        if isinstance(date, datetime.datetime):
            return tuple(date.timetuple()[:6])
        elif isinstance(date, datetime.date):
            return tuple(date.timetuple()[:3])

    def __repr__(self):
        args = [
            self.__class__.__name__,
            self._date_to_tuple(self.start),
            self._date_to_tuple(self.end) if self.has_end() else None,
            None if self._active is self._active_default else self._active,
        ]
        if args[2] is None and args[3] is None:
            return '{0}({1!r})'.format(*args)
        elif args[3] is None:
            return '{0}({1!r}, {2!r})'.format(*args)
        else:
            return '{0}({1!r}, {2!r}, {3!r})'.format(*args)

    def __nonzero__(self):
        return bool(self._start)

    __bool__ = __nonzero__  # PY3

    def __eq__(self, other):
        if (isinstance(other, OrgDate) and
            self._start is None and
            other._start is None):
            return True
        return (isinstance(other, self.__class__) and
                self._start == other._start and
                self._end == other._end and
                self._active == other._active)

    @property
    def start(self):
        """
        Get date or datetime object

        >>> OrgDate((2012, 2, 10)).start
        datetime.date(2012, 2, 10)
        >>> OrgDate((2012, 2, 10, 12, 10)).start
        datetime.datetime(2012, 2, 10, 12, 10)

        """
        return self._start

    @property
    def end(self):
        """
        Get date or datetime object

        >>> OrgDate((2012, 2, 10), (2012, 2, 15)).end
        datetime.date(2012, 2, 15)
        >>> OrgDate((2012, 2, 10, 12, 10), (2012, 2, 15, 12, 10)).end
        datetime.datetime(2012, 2, 15, 12, 10)

        """
        return self._end

    def is_active(self):
        """Return true if the date is active"""
        return self._active

    def has_end(self):
        """Return true if it has the end date"""
        return bool(self._end)

    def has_time(self):
        """
        Return true if the start date has time field

        >>> OrgDate((2012, 2, 10)).has_time()
        False
        >>> OrgDate((2012, 2, 10, 12, 10)).has_time()
        True

        """
        return isinstance(self._start, datetime.datetime)

    def has_overlap(self, other):
        """
        Test if it has overlap with other :class:`OrgDate` instance

        If the argument is not an instance of :class:`OrgDate`, it is
        converted to :class:`OrgDate` instance by ``OrgDate(other)``
        first.

        >>> od = OrgDate((2012, 2, 10), (2012, 2, 15))
        >>> od.has_overlap(OrgDate((2012, 2, 11)))
        True
        >>> od.has_overlap(OrgDate((2012, 2, 20)))
        False
        >>> od.has_overlap(OrgDate((2012, 2, 11), (2012, 2, 20)))
        True
        >>> od.has_overlap((2012, 2, 11))
        True

        """
        if not isinstance(other, OrgDate):
            other = OrgDate(other)
        if self.has_end():
            return (self._datetime_in_range(other.start) or
                    self._datetime_in_range(other.end))
        elif other.has_end():
            return other._datetime_in_range(self.start)
        elif self.start == other.get_start:
            return True
        else:
            return False

    def _datetime_in_range(self, date):
        if not isinstance(date, (datetime.datetime, datetime.date)):
            return False
        asdt = self._as_datetime
        if asdt(self.start) <= asdt(date) <= asdt(self.end):
            return True
        return False

    @staticmethod
    def _as_datetime(date):
        if isinstance(date, datetime.date):
            return datetime.datetime(*date.timetuple()[:3])
        return date

    @staticmethod
    def _datetuple_from_groupdict(dct, prefix=''):
        # FIXME: cleanup
        return list(map(int, filter(
            None, (dct["".join((prefix, key))] for key in
                   ['year', 'month', 'day', 'hour', 'min']))))

    @classmethod
    def list_from_str(cls, string):
        """
        Parse string and return a list of :class:`OrgDate` objects

        >>> OrgDate.list_from_str("... <2012-02-10 Fri> and <2012-02-12 Sun>")
        [OrgDate((2012, 2, 10)), OrgDate((2012, 2, 12))]
        >>> OrgDate.list_from_str("<2012-02-10 Fri>--<2012-02-12 Sun>")
        [OrgDate((2012, 2, 10), (2012, 2, 12))]
        >>> OrgDate.list_from_str("<2012-02-10 Fri>--[2012-02-12 Sun]")
        [OrgDate((2012, 2, 10)), OrgDate((2012, 2, 12), None, False)]
        >>> OrgDate.list_from_str("this is not timestamp")
        []

        """
        match = TIMESTAMP_RE.search(string)
        if match:
            rest = string[match.end():]
            mdict = match.groupdict()
            if mdict['active_year']:
                prefix = 'active_'
                active = True
                rangedash = '--<'
            else:
                prefix = 'inactive_'
                active = False
                rangedash = '--['
            has_rangedash = rest.startswith(rangedash)
            match2 = TIMESTAMP_RE.search(rest) if has_rangedash else None
            if has_rangedash and match2:
                rest = rest[match2.end():]
                # no need for check activeness here because of the rangedash
                mdict2 = match2.groupdict()
                odate = cls(
                    cls._datetuple_from_groupdict(mdict, prefix),
                    cls._datetuple_from_groupdict(mdict2, prefix),
                    active=active)
            else:
                odate = cls(
                    cls._datetuple_from_groupdict(mdict, prefix),
                    active=active)
            # FIXME: treat "repeater" and "warn"
            return [odate] + cls.list_from_str(rest)
        else:
            return []

    @classmethod
    def from_str(cls, string):
        """
        Parse string and return an :class:`OrgDate` objects.

        >>> OrgDate.from_str('2012-02-10 Fri')
        OrgDate((2012, 2, 10))
        >>> OrgDate.from_str('2012-02-10 Fri 12:05')
        OrgDate((2012, 2, 10, 12, 5, 0))

        """
        match = cls._from_str_re.match(string)
        if match:
            mdict = match.groupdict()
            return cls(cls._datetuple_from_groupdict(mdict),
                       active=cls._active_default)
        else:
            return cls(None)

    _from_str_re = TIMESTAMP_NOBRACE_RE


def compile_sdc_re(sdctype):
    brtype = 'inactive' if sdctype == 'CLOSED' else 'active'
    return re.compile(
        r'{0}:\s+{1}'.format(
            sdctype,
            gene_timestamp_regex(brtype, prefix='', nocookie=True)),
        re.VERBOSE)


class OrgDateSDCBase(OrgDate):

    _re = None  # override this!

    # FIXME: use OrgDate.from_str
    @classmethod
    def from_str(cls, string):
        match = cls._re.search(string)
        if match:
            mdict = match.groupdict()
            return cls(cls._datetuple_from_groupdict(mdict),
                       active=cls._active_default)
        else:
            return cls(None)


class OrgDateScheduled(OrgDateSDCBase):
    """Date object to represent SCHEDULED attribute."""
    _re = compile_sdc_re('SCHEDULED')
    _active_default = True


class OrgDateDeadline(OrgDateSDCBase):
    """Date object to represent DEADLINE attribute."""
    _re = compile_sdc_re('DEADLINE')
    _active_default = True


class OrgDateClosed(OrgDateSDCBase):
    """Date object to represent CLOSED attribute."""
    _re = compile_sdc_re('CLOSED')
    _active_default = False


def parse_sdc(string):
    return (OrgDateScheduled.from_str(string),
            OrgDateDeadline.from_str(string),
            OrgDateClosed.from_str(string))


class OrgDateClock(OrgDate):

    """
    Date object to represent CLOCK attributes.

    >>> OrgDateClock.from_str(
    ...   'CLOCK: [2010-08-08 Sun 17:00]--[2010-08-08 Sun 17:30] =>  0:30')
    OrgDateClock((2010, 8, 8, 17, 0, 0), (2010, 8, 8, 17, 30, 0))

    """

    _active_default = False

    def __init__(self, start, end, duration=None, active=None):
        """
        Create OrgDateClock object
        """
        super(OrgDateClock, self).__init__(start, end, active=active)
        self._duration = duration

    @property
    def duration(self):
        """
        Get duration of CLOCK.

        >>> duration = OrgDateClock.from_str(
        ...   'CLOCK: [2010-08-08 Sun 17:00]--[2010-08-08 Sun 17:30] => 0:30'
        ... ).duration
        >>> duration
        datetime.timedelta(0, 1800)
        >>> total_minutes(duration)
        30.0

        """
        return self.end - self.start

    def is_duration_consistent(self):
        """
        Check duration value of CLOCK line.

        >>> OrgDateClock.from_str(
        ...   'CLOCK: [2010-08-08 Sun 17:00]--[2010-08-08 Sun 17:30] => 0:30'
        ... ).is_duration_consistent()
        True
        >>> OrgDateClock.from_str(
        ...   'CLOCK: [2010-08-08 Sun 17:00]--[2010-08-08 Sun 17:30] => 0:15'
        ... ).is_duration_consistent()
        False

        """
        return (self._duration is None or
                self._duration == total_minutes(self.duration))

    @classmethod
    def from_str(cls, line):
        """
        Get CLOCK from given string.

        Return three tuple (start, stop, length) which is datetime object
        of start time, datetime object of stop time and length in minute.

        """
        match = cls._re.search(line)
        if not match:
            return cls(None, None)
        groups = [int(d) for d in match.groups()]
        ymdhm1 = groups[:5]
        ymdhm2 = groups[5:10]
        hm3 = groups[10:]
        return cls(
            datetime.datetime(*ymdhm1),
            datetime.datetime(*ymdhm2),
            hm3[0] * 60 + hm3[1],
        )

    _re = re.compile(
        r'CLOCK:\s+'
        r'\[(\d+)\-(\d+)\-(\d+)[^\]\d]*(\d+)\:(\d+)\]--'
        r'\[(\d+)\-(\d+)\-(\d+)[^\]\d]*(\d+)\:(\d+)\]\s+=>\s+(\d+)\:(\d+)'
        )


class OrgDateRpeatedTask(OrgDate):
    _active_default = False

    def __init__(self, start, end, before, after, active=None):
        """
        Create OrgDateRpeatedTask object
        """
        super(OrgDateClock, self).__init__(start, end, active=active)
        # FIXME: better name instead of before/after?
        self._before = before
        self._after = after

    @property
    def before(self):
        return self._before

    @property
    def after(self):
        return self._after
