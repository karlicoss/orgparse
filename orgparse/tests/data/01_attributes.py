from orgparse.date import (
    OrgDate, OrgDateScheduled, OrgDateDeadline, OrgDateClosed,
    OrgDateClock,
)

node1 = dict(
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
        ],
    body="""\
  - <2010-08-16 Mon> DateList
  - <2010-08-07 Sat>--<2010-08-08 Sun>
  - <2010-08-09 Mon 00:30>--<2010-08-10 Tue 13:20> RangeList"""
)

node2 = dict(
    heading="A node without any attributed",
    priority=None,
    scheduled=OrgDate(None),
    deadline=OrgDate(None),
    closed=OrgDate(None),
    clock=[],
    properties={},
    datelist=[],
    rangelist=[],
    body="",
)

data = [node1, node2, node1]
