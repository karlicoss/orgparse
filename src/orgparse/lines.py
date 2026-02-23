from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Optional, Union

from .date import (
    TIMESTAMP_RE,
    OrgDate,
    OrgDateClock,
    OrgDateClosed,
    OrgDateDeadline,
    OrgDateRepeatedTask,
    OrgDateScheduled,
)

PropertyValue = Union[str, int, float]


def parse_heading_level(heading: str) -> tuple[str, int] | None:
    """
    Get star-stripped heading and its level

    >>> parse_heading_level('* Heading')
    ('Heading', 1)
    >>> parse_heading_level('******** Heading')
    ('Heading', 8)
    >>> parse_heading_level('*') # None since no space after star
    >>> parse_heading_level('*bold*') # None
    >>> parse_heading_level('not heading')  # None

    """
    m = RE_HEADING_STARS.search(heading)
    if m is not None:
        return (m.group(2), len(m.group(1)))
    return None


RE_HEADING_STARS = re.compile(r"^\s*(\*+)\s+(.*?)\s*$")


def parse_heading_tags(heading: str) -> tuple[str, list[str]]:
    """
    Get first tags and heading without tags

    >>> parse_heading_tags('HEADING')
    ('HEADING', [])
    >>> parse_heading_tags('HEADING :TAG1:TAG2:')
    ('HEADING', ['TAG1', 'TAG2'])
    >>> parse_heading_tags('HEADING: this is still heading :TAG1:TAG2:')
    ('HEADING: this is still heading', ['TAG1', 'TAG2'])
    >>> parse_heading_tags('HEADING :@tag:_tag_:')
    ('HEADING', ['@tag', '_tag_'])

    Here is the spec of tags from Org Mode manual:

      Tags are normal words containing letters, numbers, ``_``, and
      ``@``.  Tags must be preceded and followed by a single colon,
      e.g., ``:work:``.

      -- (info "(org) Tags")

    """
    match = RE_HEADING_TAGS.search(heading)
    if match:
        heading = match.group(1)
        tagstr = match.group(2)
        tags = tagstr.split(':')
    else:
        tags = []
    return (heading, tags)


# Tags are normal words containing letters, numbers, '_', and '@'. https://orgmode.org/manual/Tags.html
RE_HEADING_TAGS = re.compile(r"(.*?)\s*:([\w@:]+):\s*$")


def parse_heading_todos(heading: str, todo_candidates: list[str]) -> tuple[str, Optional[str]]:
    """
    Get TODO keyword and heading without TODO keyword.

    >>> todos = ['TODO', 'DONE']
    >>> parse_heading_todos('Normal heading', todos)
    ('Normal heading', None)
    >>> parse_heading_todos('TODO Heading', todos)
    ('Heading', 'TODO')

    """
    for todo in todo_candidates:
        if heading == todo:
            return ('', todo)
        if heading.startswith(todo + ' '):
            return (heading[len(todo) + 1 :], todo)
    return (heading, None)


def parse_heading_priority(heading: str) -> tuple[str, Optional[str]]:
    """
    Get priority and heading without priority field.

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


RE_HEADING_PRIORITY = re.compile(r"^\s*\[#([A-Z0-9])\] ?(.*)$")


def parse_property(line: str) -> tuple[Optional[str], Optional[PropertyValue]]:
    """
    Get property from given string.

    >>> parse_property(':Some_property: some value')
    ('Some_property', 'some value')
    >>> parse_property(':Effort: 1:10')
    ('Effort', 70)

    """
    prop_key = None
    prop_val: Optional[Union[str, int, float]] = None
    match = RE_PROP.search(line)
    if match:
        prop_key = match.group(1)
        prop_val = match.group(2)
        if prop_key == 'Effort':
            prop_val = parse_duration_to_minutes(prop_val)
    return (prop_key, prop_val)


RE_PROP = re.compile(r"^\s*:(.*?):\s*(.*?)\s*$")
RE_PROP_LINE = re.compile(r"^(?P<prefix>\s*):(?P<key>[^:]+):\s*(?P<value>.*?)\s*$")
RE_REPEAT_TASK_LINE = re.compile(
    r"^(?P<indent>\s*)-\s+State\s+\"(?P<done>[^\"]+)\"\s+from\s+\"(?P<todo>[^\"]+)\"\s+\[(?P<date>[^\]]+)\](?:\s*\\\\(?P<comment>.*))?\s*$"
)


def parse_duration_to_minutes(duration: str) -> Union[float, int]:
    """
    Parse duration minutes from given string.
    Convert to integer if number has no decimal points

    >>> parse_duration_to_minutes('3:12')
    192
    >>> parse_duration_to_minutes('1:23:45')
    83.75
    >>> parse_duration_to_minutes('1y 3d 3h 4min')
    530464
    >>> parse_duration_to_minutes('1d3h5min')
    1625
    >>> parse_duration_to_minutes('3d 13:35')
    5135
    >>> parse_duration_to_minutes('2.35h')
    141
    >>> parse_duration_to_minutes('10')
    10
    >>> parse_duration_to_minutes('10.')
    10
    >>> parse_duration_to_minutes('1 h')
    60
    >>> parse_duration_to_minutes('')
    0
    """

    minutes = parse_duration_to_minutes_float(duration)
    return int(minutes) if minutes.is_integer() else minutes


def parse_duration_to_minutes_float(duration: str) -> float:
    """
    Parse duration minutes from given string.
    The following code is fully compatible with the 'org-duration-to-minutes' function in org mode:
    https://github.com/emacs-mirror/emacs/blob/master/lisp/org/org-duration.el

    >>> parse_duration_to_minutes_float('3:12')
    192.0
    >>> parse_duration_to_minutes_float('1:23:45')
    83.75
    >>> parse_duration_to_minutes_float('1y 3d 3h 4min')
    530464.0
    >>> parse_duration_to_minutes_float('1d3h5min')
    1625.0
    >>> parse_duration_to_minutes_float('3d 13:35')
    5135.0
    >>> parse_duration_to_minutes_float('2.35h')
    141.0
    >>> parse_duration_to_minutes_float('10')
    10.0
    >>> parse_duration_to_minutes_float('10.')
    10.0
    >>> parse_duration_to_minutes_float('1 h')
    60.0
    >>> parse_duration_to_minutes_float('')
    0.0
    """

    match: Optional[object]
    if duration == "":
        return 0.0
    if isinstance(duration, float):
        return float(duration)
    if RE_ORG_DURATION_H_MM.fullmatch(duration):
        hours, minutes, *seconds_ = map(float, duration.split(":"))
        seconds = seconds_[0] if seconds_ else 0
        return seconds / 60.0 + minutes + 60 * hours
    if RE_ORG_DURATION_FULL.fullmatch(duration):
        minutes = 0
        for match in RE_ORG_DURATION_UNIT.finditer(duration):
            value = float(match.group(1))
            unit = match.group(2)
            minutes += value * ORG_DURATION_UNITS[unit]
        return float(minutes)
    match = RE_ORG_DURATION_MIXED.fullmatch(duration)
    if match:
        units_part = match.groupdict()["A"]
        hms_part = match.groupdict()["B"]
        return parse_duration_to_minutes_float(units_part) + parse_duration_to_minutes_float(hms_part)
    if RE_FLOAT.fullmatch(duration):
        return float(duration)
    raise ValueError(f"Invalid duration format {duration}")


# Conversion factor to minutes for a duration.
ORG_DURATION_UNITS = {
    "min": 1,
    "h": 60,
    "d": 60 * 24,
    "w": 60 * 24 * 7,
    "m": 60 * 24 * 30,
    "y": 60 * 24 * 365.25,
}
# Regexp matching for all units.
ORG_DURATION_UNITS_RE = r"({})".format(r"|".join(ORG_DURATION_UNITS.keys()))
# Regexp matching a duration expressed with H:MM or H:MM:SS format.
# Hours can use any number of digits.
ORG_DURATION_H_MM_RE = r"[ \t]*[0-9]+(?::[0-9]{2}){1,2}[ \t]*"
RE_ORG_DURATION_H_MM = re.compile(ORG_DURATION_H_MM_RE)
# Regexp matching a duration with an unit.
# Allowed units are defined in ORG_DURATION_UNITS.
# Match group 1 contains the bare number.
# Match group 2 contains the unit.
ORG_DURATION_UNIT_RE = r"([0-9]+(?:[.][0-9]*)?)[ \t]*" + ORG_DURATION_UNITS_RE
RE_ORG_DURATION_UNIT = re.compile(ORG_DURATION_UNIT_RE)
# Regexp matching a duration expressed with units.
# Allowed units are defined in ORG_DURATION_UNITS.
ORG_DURATION_FULL_RE = rf"(?:[ \t]*{ORG_DURATION_UNIT_RE})+[ \t]*"
RE_ORG_DURATION_FULL = re.compile(ORG_DURATION_FULL_RE)
# Regexp matching a duration expressed with units and H:MM or H:MM:SS format.
# Allowed units are defined in ORG_DURATION_UNITS.
# Match group A contains units part.
# Match group B contains H:MM or H:MM:SS part.
ORG_DURATION_MIXED_RE = rf"(?P<A>([ \t]*{ORG_DURATION_UNIT_RE})+)[ \t]*(?P<B>[0-9]+(?::[0-9][0-9]){{1,2}})[ \t]*"
RE_ORG_DURATION_MIXED = re.compile(ORG_DURATION_MIXED_RE)
# Regexp matching float numbers.
RE_FLOAT = re.compile(r"[0-9]+([.][0-9]*)?")


class LineItem:
    def render(self) -> str:
        raise NotImplementedError


class TextLine(LineItem):
    def __init__(self, raw: str) -> None:
        self._raw = raw

    def render(self) -> str:
        return self._raw


class HeadingLine(LineItem):
    def __init__(
        self,
        raw: str,
        level: int,
        todo: Optional[str],
        priority: Optional[str],
        heading: str,
        tags: Sequence[str],
    ) -> None:
        self._raw = raw
        self.level = level
        self.todo = todo
        self.priority = priority
        self.heading = heading
        self.tags = list(tags)
        self._dirty = False

    @classmethod
    def from_line(cls, line: str, todo_candidates: list[str]) -> HeadingLine:
        heading_level = parse_heading_level(line)
        if heading_level is None:
            raise ValueError(f"Invalid heading line: {line!r}")
        (heading, level) = heading_level
        (heading, tags) = parse_heading_tags(heading)
        (heading, todo) = parse_heading_todos(heading, todo_candidates)
        (heading, priority) = parse_heading_priority(heading)
        return cls(
            raw=line,
            level=level,
            todo=todo,
            priority=priority,
            heading=heading,
            tags=tags,
        )

    def mark_dirty(self) -> None:
        self._dirty = True

    def render(self) -> str:
        if not self._dirty:
            return self._raw

        stars = "*" * self.level
        tokens: list[str] = []
        if self.todo:
            tokens.append(self.todo)
        if self.priority:
            tokens.append(f"[#{self.priority}]")
        if self.heading:
            tokens.append(self.heading)

        if not tokens and not self.tags:
            rendered = f"{stars} "
            self._raw = rendered
            self._dirty = False
            return rendered

        rendered = f"{stars} "
        if tokens:
            rendered += " ".join(tokens)
        if self.tags:
            if tokens:
                rendered += " "
            rendered += ":" + ":".join(self.tags) + ":"

        self._raw = rendered
        self._dirty = False
        return rendered


class SdcEntry(LineItem):
    def __init__(self, label: str, date: OrgDate, raw: str) -> None:
        self.label = label
        self.date = date
        self._raw = raw
        self._dirty = False

    def update(self, date: OrgDate) -> None:
        self.date = date
        self._dirty = True

    def render(self) -> str:
        if not self._dirty:
            return self._raw
        return f"{self.label}: {self.date}"


class SdcLine(LineItem):
    _label_re = re.compile(r"(SCHEDULED|DEADLINE|CLOSED):\s+")

    def __init__(self, raw: str, parts: list[LineItem | str], entries: dict[str, SdcEntry]) -> None:
        self._raw = raw
        self._parts = parts
        self._entries = entries
        self._dirty = False

    @classmethod
    def from_line(cls, line: str) -> SdcLine | None:
        if line.lstrip().startswith("#"):
            return None
        parts: list[LineItem | str] = []
        entries: dict[str, SdcEntry] = {}
        pos = 0
        for match in cls._label_re.finditer(line):
            ts_match = TIMESTAMP_RE.match(line[match.end() :])
            if not ts_match:
                continue
            entry_start = match.start()
            entry_end = match.end() + ts_match.end()
            if entry_start > pos:
                parts.append(line[pos:entry_start])
            label = match.group(1)
            entry_text = line[entry_start:entry_end]
            if label == "SCHEDULED":
                date = OrgDateScheduled.from_str(entry_text)
            elif label == "DEADLINE":
                date = OrgDateDeadline.from_str(entry_text)
            else:
                date = OrgDateClosed.from_str(entry_text)
            entry = SdcEntry(label, date, entry_text)
            entries[label] = entry
            parts.append(entry)
            pos = entry_end
        if not entries:
            return None
        if pos < len(line):
            parts.append(line[pos:])
        return cls(line, parts, entries)

    @classmethod
    def from_entries(cls, entries: dict[str, OrgDate]) -> SdcLine:
        order = ["SCHEDULED", "DEADLINE", "CLOSED"]
        parts: list[LineItem | str] = []
        raw_parts: list[str] = []
        entry_map: dict[str, SdcEntry] = {}
        for label in order:
            date = entries.get(label)
            if date is None or not date:
                continue
            entry = SdcEntry(label, date, f"{label}: {date}")
            entry_map[label] = entry
            if raw_parts:
                raw_parts.append(" ")
                parts.append(" ")
            raw_parts.append(entry.render())
            parts.append(entry)
        raw = "".join(raw_parts)
        return cls(raw, parts, entry_map)

    def update_entry(self, label: str, date: OrgDate | None) -> None:
        if date is None or not date:
            entry = self._entries.pop(label, None)
            if entry is not None:
                self._parts = [part for part in self._parts if part is not entry]
                self._dirty = True
            return
        entry = self._entries.get(label)
        if entry is None:
            new_entry = SdcEntry(label, date, f"{label}: {date}")
            if self._parts:
                self._parts.append(" ")
            self._parts.append(new_entry)
            self._entries[label] = new_entry
        else:
            entry.update(date)
        self._dirty = True

    def is_empty(self) -> bool:
        return not self._entries

    def render(self) -> str:
        if not self._dirty:
            return self._raw
        rendered_parts: list[str] = []
        for part in self._parts:
            if isinstance(part, LineItem):
                rendered = part.render()
                if rendered:
                    rendered_parts.append(rendered)
            else:
                rendered_parts.append(part)
        rendered = "".join(rendered_parts)
        self._raw = rendered
        self._dirty = False
        return rendered


class ClockLine(LineItem):
    _label_re = re.compile(r"^(?!#)(?P<prefix>\s*CLOCK:\s+)")

    def __init__(self, raw: str, prefix: str, date: OrgDateClock) -> None:
        self._raw = raw
        self._prefix = prefix
        self.date = date
        self._dirty = False

    @classmethod
    def _timestamp_span(cls, line: str, start: int) -> tuple[int, int] | None:
        match = TIMESTAMP_RE.search(line, start)
        if not match:
            return None
        span_start = match.start()
        span_end = match.end()
        if line[span_end : span_end + 2] == "--":
            match2 = TIMESTAMP_RE.match(line[span_end + 2 :])
            if match2:
                span_end = span_end + 2 + match2.end()
        return (span_start, span_end)

    @classmethod
    def from_line(cls, line: str) -> ClockLine | None:
        match = cls._label_re.match(line)
        if not match:
            return None
        span = cls._timestamp_span(line, match.end())
        if not span:
            return None
        date = OrgDateClock.from_str(line)
        if not date:
            return None
        (ts_start, _ts_end) = span
        prefix = line[:ts_start]
        return cls(line, prefix, date)

    def update(self, date: OrgDateClock) -> None:
        self.date = date
        self._dirty = True

    @classmethod
    def _compute_suffix(cls, date: OrgDateClock) -> str:
        if not date.has_end():
            return ""
        minutes = int(date.duration.total_seconds() // 60)
        hours, mins = divmod(minutes, 60)
        return f" => {hours}:{mins:02d}"

    def render(self) -> str:
        if not self._dirty:
            return self._raw
        suffix = self._compute_suffix(self.date)
        rendered = f"{self._prefix}{self.date}{suffix}"
        self._raw = rendered
        self._dirty = False
        return rendered


class LogbookStartLine(LineItem):
    def __init__(self, raw: str) -> None:
        self._raw = raw

    def render(self) -> str:
        return self._raw


class LogbookEndLine(LineItem):
    def __init__(self, raw: str) -> None:
        self._raw = raw

    def render(self) -> str:
        return self._raw


class RepeatTaskLine(LineItem):
    def __init__(
        self,
        raw: str,
        repeat: OrgDateRepeatedTask,
        indent: str,
        comment: str | None,
    ) -> None:
        self._raw = raw
        self.repeat = repeat
        self.indent = indent
        self.comment = comment
        self._dirty = False

    @classmethod
    def match(cls, line: str) -> re.Match[str] | None:
        if line.lstrip().startswith("#"):
            return None
        return RE_REPEAT_TASK_LINE.match(line)

    @classmethod
    def from_line(cls, line: str, comment: str | None = None) -> RepeatTaskLine | None:
        if line.lstrip().startswith("#"):
            return None
        match = RE_REPEAT_TASK_LINE.match(line)
        if not match:
            return None
        inline_comment = match.group("comment")
        if comment is None and inline_comment is not None:
            inline_comment = inline_comment.lstrip()
            comment = inline_comment
        date = OrgDate.from_str(match.group("date"))
        repeat = OrgDateRepeatedTask(date.start, match.group("todo"), match.group("done"), comment=comment)
        return cls(
            raw=line,
            repeat=repeat,
            indent=match.group("indent"),
            comment=comment,
        )

    @classmethod
    def from_repeat(cls, repeat: OrgDateRepeatedTask, indent: str) -> RepeatTaskLine:
        date_str = str(repeat)
        raw = f"{indent}- State \"{repeat.after}\" from \"{repeat.before}\" {date_str}"
        if repeat.comment is not None:
            raw = f"{raw} \\\\"  # comment lines are handled separately
            if repeat.comment and "\n" not in repeat.comment:
                raw = f"{raw} {repeat.comment}"
        return cls(raw=raw, repeat=repeat, indent=indent, comment=repeat.comment)

    def update_repeat(self, repeat: OrgDateRepeatedTask) -> None:
        self.repeat = repeat
        self.comment = repeat.comment
        self._dirty = True

    def render(self) -> str:
        if not self._dirty:
            return self._raw
        date_str = str(self.repeat)
        rendered = f"{self.indent}- State \"{self.repeat.after}\" from \"{self.repeat.before}\" {date_str}"
        if self.comment is not None:
            rendered = f"{rendered} \\\\"  # comment lines are handled separately
            if self.comment and "\n" not in self.comment:
                rendered = f"{rendered} {self.comment}"
        self._raw = rendered
        self._dirty = False
        return rendered


class PropertyDrawerStartLine(LineItem):
    def __init__(self, raw: str) -> None:
        self._raw = raw

    def render(self) -> str:
        return self._raw


class PropertyDrawerEndLine(LineItem):
    def __init__(self, raw: str) -> None:
        self._raw = raw

    def render(self) -> str:
        return self._raw


class PropertyEntryLine(LineItem):
    def __init__(
        self,
        raw: str,
        key: str,
        value: PropertyValue,
        render_value: str,
        prefix: str,
    ) -> None:
        self._raw = raw
        self.key = key
        self.value = value
        self._render_value = render_value
        self._prefix = prefix
        self._dirty = False

    @classmethod
    def from_line(cls, line: str) -> PropertyEntryLine | None:
        match = RE_PROP_LINE.match(line)
        if not match:
            return None
        (key, value) = parse_property(line)
        if key is None or value is None:
            return None
        return cls(
            raw=line,
            key=key,
            value=value,
            render_value=match.group("value"),
            prefix=match.group("prefix"),
        )

    def update_value(self, value: PropertyValue, render_value: str) -> None:
        self.value = value
        self._render_value = render_value
        self._dirty = True

    def render(self) -> str:
        if not self._dirty:
            return self._raw
        if self._render_value == "":
            rendered = f"{self._prefix}:{self.key}:"
        else:
            rendered = f"{self._prefix}:{self.key}: {self._render_value}"
        self._raw = rendered
        self._dirty = False
        return rendered
