from orgparse.date import OrgDate
import datetime


def test_date_as_datetime() -> None:
    testdate = (2021, 9, 3)
    testdatetime = (2021, 9, 3, 16, 19, 13)

    assert OrgDate._as_datetime(datetime.date(*testdate)) == datetime.datetime(*testdate, 0, 0, 0)
    assert OrgDate._as_datetime(datetime.datetime(*testdatetime)) == datetime.datetime(*testdatetime)
