from orgparse import get_datetime, parse_daterangelist


def test_parse_daterangelist():
    datefmt0 = "<%(Y)04d-%(M)02d-%(D)02d %(d)s>"
    datefmt1 = "<%(Y)04d-%(M)02d-%(D)02d %(d)s %(h)02d:%(m)02d>"

    dates = [
        dict(Y=2010, M=6, D=21, d='Mon', h=12, m=0),
        dict(Y=2010, M=6, D=21, d='Mon', h=13, m=0),
        dict(Y=2010, M=6, D=21, d='Mon', h=None, m=None),
        ]

    datestr = " ".join([
        datefmt1 % dates[0],
        datefmt1 % dates[1],
        datefmt0 % dates[2],
        ("%s--%s" % (datefmt1 % dates[0], datefmt1 % dates[1]))
        ])

    desired_datelist = [get_datetime(d['Y'], d['M'], d['D'], d['h'], d['m'])
                        for d in dates]
    d0 = dates[0]
    d1 = dates[1]
    desired_rangelist = [
        (get_datetime(d0['Y'], d0['M'], d0['D'], d0['h'], d0['m']),
         get_datetime(d1['Y'], d1['M'], d1['D'], d1['h'], d1['m']))]

    for context in ["%s", " %s", "%s ", "aaa%sbbb"]:
        (datelist, rangelist) = parse_daterangelist(context % datestr)
        for (des, act) in zip(desired_datelist, datelist):
            assert des == act
        for (des, act) in zip(desired_rangelist, rangelist):
            assert des == act
