from orgparse.date import OrgDateClock

data = [dict(
    heading='LOGBOOK drawer test',
    clock=[
        OrgDateClock((2012, 10, 26, 14, 50), (2012, 10, 26, 15, 00)),
        OrgDateClock((2012, 10, 26, 14, 30), (2012, 10, 26, 14, 40)),
        OrgDateClock((2012, 10, 26, 14, 10), (2012, 10, 26, 14, 20)),
    ]
)]
