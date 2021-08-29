from typing import Dict, Any

from orgparse.date import (
    OrgDate, OrgDateScheduled, OrgDateDeadline, OrgDateClosed,
    OrgDateClock,
)

Raw = Dict[str, Any]

node1: Raw = dict(
    heading="A node with a lot of attributes",
    priority='A',
    scheduled=OrgDateScheduled((2010, 8, 6)),
    deadline=OrgDateDeadline((2010, 8, 10)),
    closed=OrgDateClosed((2010, 8, 8, 18, 0)),
    clock=[
        OrgDateClock((2010, 8, 8, 17, 40), (2010, 8, 8, 17, 50), 10),
        OrgDateClock((2010, 8, 8, 17, 00), (2010, 8, 8, 17, 30), 30),
        ],
    properties=dict(Effort=70),
    datelist=[OrgDate((2010, 8, 16))],
    rangelist=[
        OrgDate((2010, 8, 7), (2010, 8, 8)),
        OrgDate((2010, 8, 9, 0, 30), (2010, 8, 10, 13, 20)),
        OrgDate((2019, 8, 10, 16, 30, 0), (2019, 8, 10, 17, 30, 0)),
        ],
    body="""\
  - <2010-08-16 Mon> DateList
  - <2010-08-07 Sat>--<2010-08-08 Sun>
  - <2010-08-09 Mon 00:30>--<2010-08-10 Tue 13:20> RangeList
  - <2019-08-10 Sat 16:30-17:30> TimeRange"""
)

node2: Raw = dict(
    heading="A node without any attributed",
    priority=None,
    scheduled=OrgDateScheduled(None),
    deadline=OrgDateDeadline(None),
    closed=OrgDateClosed(None),
    clock=[],
    properties={},
    datelist=[],
    rangelist=[],
    body="",
)

node3: Raw = dict(
    heading="range in deadline",
    priority=None,
    scheduled=OrgDateScheduled(None),
    deadline=OrgDateDeadline((2019, 9, 6, 10, 0), (2019, 9, 6, 11, 20)),
    closed=OrgDateClosed(None),
    clock=[],
    properties={},
    datelist=[],
    rangelist=[],
    body="  body",
)

node4: Raw = dict(
    heading="node with a second line but no date",
    priority=None,
    scheduled=OrgDateScheduled(None),
    deadline=OrgDateDeadline(None),
    closed=OrgDateClosed(None),
    clock=[],
    properties={},
    datelist=[],
    rangelist=[],
    body="body",
)

data = [node1, node2, node1, node3, node4]
