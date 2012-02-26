from datetime import date, datetime

node1 = dict(
    heading="A node with a lot of attributes",
    scheduled=date(2010, 8, 6),
    deadline=date(2010, 8, 10),
    closed=datetime(2010, 8, 8, 18, 0),
    clock=[
        (datetime(2010, 8, 8, 17, 40), datetime(2010, 8, 8, 17, 50), 10),
        (datetime(2010, 8, 8, 17, 00), datetime(2010, 8, 8, 17, 30), 30),
        ],
    properties=dict(Effort=70),
    datelist=[date(2010, 8, 16)],
    rangelist=[
        (date(2010, 8, 7), date(2010, 8, 8)),
        (datetime(2010, 8, 9, 0, 30), datetime(2010, 8, 10, 13, 20)),
        ],
    body="""\
  - <2010-08-16 Mon> DateList
  - <2010-08-07 Sat>--<2010-08-08 Sun>
  - <2010-08-09 Mon 00:30>--<2010-08-10 Tue 13:20> RangeList"""
)

node2 = dict(
    heading="A node without any attributed",
    scheduled=None,
    deadline=None,
    closed=None,
    clock=[],
    properties={},
    datelist=[],
    rangelist=[],
    body="",
)

data = [node1, node2, node1]
