from orgparse.date import OrgDate, OrgDateScheduled, OrgDateDeadline, OrgDateClock, OrgDateClosed
import datetime


def test_date_as_string() -> None:

    testdate = datetime.date(2021, 9, 3)
    testdate2 = datetime.date(2021, 9, 5)
    testdatetime = datetime.datetime(2021, 9, 3, 16, 19, 13)
    testdatetime2 = datetime.datetime(2021, 9, 3, 17, 0, 1)
    testdatetime_nextday = datetime.datetime(2021, 9, 4, 0, 2, 1)

    assert str(OrgDate(testdate)) == "<2021-09-03 Fri>"
    assert str(OrgDate(testdatetime)) == "<2021-09-03 Fri 16:19>"
    assert str(OrgDate(testdate, active=False)) == "[2021-09-03 Fri]"
    assert str(OrgDate(testdatetime, active=False)) == "[2021-09-03 Fri 16:19]"

    assert str(OrgDate(testdate, testdate2)) == "<2021-09-03 Fri>--<2021-09-05 Sun>"
    assert str(OrgDate(testdate, testdate2)) == "<2021-09-03 Fri>--<2021-09-05 Sun>"
    assert str(OrgDate(testdatetime, testdatetime2)) == "<2021-09-03 Fri 16:19--17:00>"
    assert str(OrgDate(testdate, testdate2, active=False)) == "[2021-09-03 Fri]--[2021-09-05 Sun]"
    assert str(OrgDate(testdate, testdate2, active=False)) == "[2021-09-03 Fri]--[2021-09-05 Sun]"
    assert str(OrgDate(testdatetime, testdatetime2, active=False)) == "[2021-09-03 Fri 16:19--17:00]"

    assert str(OrgDateScheduled(testdate)) == "<2021-09-03 Fri>"
    assert str(OrgDateScheduled(testdatetime)) == "<2021-09-03 Fri 16:19>"
    assert str(OrgDateDeadline(testdate)) == "<2021-09-03 Fri>"
    assert str(OrgDateDeadline(testdatetime)) == "<2021-09-03 Fri 16:19>"
    assert str(OrgDateClosed(testdate)) == "[2021-09-03 Fri]"
    assert str(OrgDateClosed(testdatetime)) == "[2021-09-03 Fri 16:19]"

    assert str(OrgDateClock(testdatetime, testdatetime2)) == "[2021-09-03 Fri 16:19]--[2021-09-03 Fri 17:00]"
    assert str(OrgDateClock(testdatetime, testdatetime_nextday)) == "[2021-09-03 Fri 16:19]--[2021-09-04 Sat 00:02]"
    assert str(OrgDateClock(testdatetime)) == "[2021-09-03 Fri 16:19]"


def test_date_as_datetime() -> None:
    testdate = (2021, 9, 3)
    testdatetime = (2021, 9, 3, 16, 19, 13)

    assert OrgDate._as_datetime(datetime.date(*testdate)) == datetime.datetime(*testdate, 0, 0, 0)
    assert OrgDate._as_datetime(datetime.datetime(*testdatetime)) == datetime.datetime(*testdatetime)