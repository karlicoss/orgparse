import datetime

from orgparse.date import OrgDate, OrgDateClock, OrgDateRepeatedTask

from .. import loads


def test_dynamic_heading_edits() -> None:
    content = """* TODO [#A] Heading :tag1:tag2:
  Body line
  Second line"""
    root = loads(content)
    node = root.children[0]
    assert str(node) == content

    node.todo = "DONE"
    assert node.todo == "DONE"
    assert str(node).splitlines()[0] == "* DONE [#A] Heading :tag1:tag2:"

    node.priority = None
    assert node.priority is None
    assert str(node).splitlines()[0] == "* DONE Heading :tag1:tag2:"

    node.heading = "Updated heading"
    assert node.heading == "Updated heading"
    assert str(node).splitlines()[0] == "* DONE Updated heading :tag1:tag2:"

    node.tags = ["x", "y"]
    assert node.shallow_tags == {"x", "y"}
    assert str(node).splitlines()[0] == "* DONE Updated heading :x:y:"

    node.todo = None
    node.priority = "B"
    node.tags = []
    assert str(node).splitlines()[0] == "* [#B] Updated heading"

    assert str(node).splitlines()[1:] == ["  Body line", "  Second line"]


def test_children_setter_reparents_root() -> None:
    content = """* A
** A1
* B
** B1"""
    root = loads(content)
    (a, b) = root.children
    b1 = b.children[0]

    root.children = [b]

    assert root.children == [b]
    assert b.parent is root
    assert b1.parent is b
    assert [node.heading for node in root[1:]] == ["B", "B1"]
    assert a not in list(root)


def test_children_setter_reparents_and_adjusts_levels() -> None:
    content = """* A
** A1
*** A1a
* B
*** B1"""
    root = loads(content)
    a = root.children[0]
    b = root.children[1]
    b1 = b.children[0]

    a.children = [b1]

    assert a.children == [b1]
    assert b.children == []
    assert b1.parent is a
    assert b1.level == a.level + 1
    assert str(b1).splitlines()[0] == "** B1"
    assert [node.heading for node in root[1:]] == ["A", "B1", "B"]


def test_children_setter_reparents_subtree_and_shifts_descendants() -> None:
    content = """* A
** A1
*** A1a
* B
** B1
*** B1a"""
    root = loads(content)
    a1 = root.children[0].children[0]
    b = root.children[1]
    b1 = b.children[0]
    b1a = b1.children[0]

    a1.children = [b1]

    assert a1.children == [b1]
    assert b.children == []
    assert b1.parent is a1
    assert b1.level == a1.level + 1
    assert b1a.level == b1.level + 1
    assert str(b1).splitlines()[0] == "*** B1"
    assert str(b1a).splitlines()[0] == "**** B1a"
    assert "A1a" not in [node.heading for node in root[1:]]


def test_dynamic_timestamp_edits() -> None:
    content = """* Node
  CLOSED: [2012-02-26 Sun 21:15] SCHEDULED: <2012-02-26 Sun>
  CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] =>  0:05
  Body"""
    root = loads(content)
    node = root.children[0]

    node.deadline = datetime.date(2012, 3, 1)
    sdc_line = str(node).splitlines()[1]
    assert "DEADLINE: <2012-03-01 Thu>" in sdc_line
    assert "SCHEDULED: <2012-02-26 Sun>" in sdc_line
    assert "CLOSED: [2012-02-26 Sun 21:15]" in sdc_line

    node.closed = None
    sdc_line = str(node).splitlines()[1]
    assert "CLOSED:" not in sdc_line

    node.clock = [OrgDateClock((2012, 2, 26, 22, 0, 0), (2012, 2, 26, 22, 30, 0))]
    clock_line = str(node).splitlines()[2]
    assert "CLOCK: [2012-02-26 Sun 22:00]--[2012-02-26 Sun 22:30]" in clock_line


def test_add_scheduled_timestamp_line() -> None:
    content = """* Node
  Body"""
    root = loads(content)
    node = root.children[0]

    node.scheduled = datetime.date(2012, 2, 26)
    assert str(node).splitlines()[:2] == ["* Node", "SCHEDULED: <2012-02-26 Sun>"]
    assert str(node).splitlines()[2] == "  Body"


def test_overwrite_existing_dates() -> None:
    content = """* Node
  SCHEDULED: <2012-02-26 Sun> DEADLINE: <2012-02-27 Mon> CLOSED: [2012-02-25 Sat]
  Body"""
    node = loads(content).children[0]

    node.scheduled = datetime.date(2012, 3, 1)
    node.deadline = datetime.date(2012, 3, 2)
    node.closed = datetime.datetime(2012, 3, 3, 10, 30)

    sdc_line = str(node).splitlines()[1]
    assert "SCHEDULED: <2012-03-01 Thu>" in sdc_line
    assert "DEADLINE: <2012-03-02 Fri>" in sdc_line
    assert "CLOSED: [2012-03-03 Sat 10:30]" in sdc_line


def test_add_dates_to_node_without_dates() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]

    node.scheduled = datetime.date(2012, 2, 26)
    node.deadline = datetime.date(2012, 3, 1)
    node.closed = datetime.datetime(2012, 2, 27, 8, 30)

    lines = str(node).splitlines()
    assert lines[0] == "* Node"
    assert lines[1] == "SCHEDULED: <2012-02-26 Sun> DEADLINE: <2012-03-01 Thu> CLOSED: [2012-02-27 Mon 08:30]"
    assert lines[2] == "  Body"


def test_add_dates_to_node_with_existing_dates() -> None:
    content = """* Node
  SCHEDULED: <2012-02-26 Sun>
  Body"""
    node = loads(content).children[0]

    node.deadline = datetime.date(2012, 3, 1)
    node.closed = datetime.datetime(2012, 2, 27, 8, 30)

    sdc_line = str(node).splitlines()[1]
    assert "SCHEDULED: <2012-02-26 Sun>" in sdc_line
    assert "DEADLINE: <2012-03-01 Thu>" in sdc_line
    assert "CLOSED: [2012-02-27 Mon 08:30]" in sdc_line


def test_remove_dates_from_node_without_dates() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]

    node.scheduled = None
    node.deadline = None
    node.closed = None

    assert str(node) == content


def test_remove_dates_from_node_with_dates() -> None:
    content = """* Node
  SCHEDULED: <2012-02-26 Sun> DEADLINE: <2012-03-01 Thu>
  Body"""
    node = loads(content).children[0]

    node.scheduled = None
    assert "SCHEDULED:" not in str(node).splitlines()[1]

    node.deadline = None
    lines = str(node).splitlines()
    assert lines == ["* Node", "  Body"]


def test_duplicate_scheduled_dates() -> None:
    content = """* Node
  SCHEDULED: <2012-02-26 Sun> SCHEDULED: <2012-03-01 Thu>
  Body"""
    node = loads(content).children[0]
    assert node.scheduled.start == datetime.date(2012, 3, 1)

    node.scheduled = datetime.date(2012, 4, 1)
    sdc_line = str(node).splitlines()[1]
    assert "SCHEDULED: <2012-02-26 Sun>" in sdc_line
    assert "SCHEDULED: <2012-04-01 Sun>" in sdc_line


def test_multiple_clock_entries() -> None:
    content = """* Node
  CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] =>  0:05
  CLOCK: [2012-02-26 Sun 22:00]--[2012-02-26 Sun 22:30] =>  0:30
  Body"""
    node = loads(content).children[0]

    node.clock = [
        OrgDateClock((2012, 2, 26, 23, 0, 0), (2012, 2, 26, 23, 30, 0)),
        OrgDateClock((2012, 2, 27, 1, 0, 0), (2012, 2, 27, 1, 15, 0)),
    ]
    lines = str(node).splitlines()
    assert "CLOCK: [2012-02-26 Sun 23:00]--[2012-02-26 Sun 23:30]" in lines[1]
    assert "CLOCK: [2012-02-27 Mon 01:00]--[2012-02-27 Mon 01:15]" in lines[2]

    node.clock = []
    assert all("CLOCK:" not in line for line in str(node).splitlines())


def test_setting_inactive_scheduled_date() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]

    node.scheduled = OrgDate((2012, 2, 26), active=False)
    assert str(node).splitlines()[1] == "SCHEDULED: [2012-02-26 Sun]"


def test_overwrite_properties() -> None:
    content = """* Node
  :PROPERTIES:
  :Owner: Jane
  :Effort: 1:10
  :END:
  Body"""
    node = loads(content).children[0]

    node.properties = {"Owner": "Alex", "Effort": "0:30"}
    lines = str(node).splitlines()
    assert lines[1] == "  :PROPERTIES:"
    assert "  :Owner: Alex" in lines
    assert "  :Effort: 0:30" in lines
    assert lines[-1] == "  Body"
    assert node.properties["Effort"] == 30


def test_add_properties_without_drawer() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]

    node.properties = {"Owner": "Alex"}
    lines = str(node).splitlines()
    assert lines[:3] == ["* Node", "  :PROPERTIES:", "  :Owner: Alex"]
    assert lines[3] == "  :END:"
    assert lines[4] == "  Body"


def test_add_properties_with_existing_drawer() -> None:
    content = """* Node
  :PROPERTIES:
  :Owner: Jane
  :END:
  Body"""
    node = loads(content).children[0]

    node.properties = {"Owner": "Jane", "Project": "Alpha"}
    lines = str(node).splitlines()
    assert "  :Owner: Jane" in lines
    assert "  :Project: Alpha" in lines


def test_remove_properties_without_drawer() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]

    node.properties = {}
    assert str(node) == content


def test_remove_properties_with_drawer() -> None:
    content = """* Node
  :PROPERTIES:
  :Owner: Jane
  :END:
  Body"""
    node = loads(content).children[0]

    node.properties = {}
    assert (
        str(node)
        == """* Node
  Body"""
    )


def test_duplicate_properties_update_last() -> None:
    content = """* Node
  :PROPERTIES:
  :Owner: Jane
  :Owner: Jill
  :END:
  Body"""
    node = loads(content).children[0]
    assert node.properties["Owner"] == "Jill"

    node.properties = {"Owner": "Alex"}
    lines = str(node).splitlines()
    assert "  :Owner: Jane" in lines
    assert "  :Owner: Alex" in lines


def test_properties_preserve_output_when_unchanged() -> None:
    content = """* Node
  :PROPERTIES:
  :Owner: Jane
  :END:
  Body"""
    node = loads(content).children[0]
    assert str(node) == content


def test_root_node_properties() -> None:
    content = """Intro

:PROPERTIES:
:Title: Example
:END:

* Node"""
    root = loads(content)
    root.properties = {"Title": "Updated"}
    assert "Title: Updated" in str(root)


def test_overwrite_repeated_tasks_in_logbook() -> None:
    content = """* Node
  :LOGBOOK:
  - State "DONE" from "TODO" [2005-09-01 Thu 16:10]
  - State "DONE" from "TODO" [2005-08-01 Mon 19:44]
  :END:
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = [
        OrgDateRepeatedTask((2005, 7, 1, 17, 27, 0), "TODO", "DONE"),
        OrgDateRepeatedTask((2005, 6, 1, 10, 0, 0), "TODO", "DONE"),
    ]
    lines = str(node).splitlines()
    assert "[2005-07-01 Fri 17:27]" in lines[2]
    assert "[2005-06-01 Wed 10:00]" in lines[3]


def test_add_repeated_tasks_without_logbook() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = [
        OrgDateRepeatedTask((2005, 9, 1, 16, 10, 0), "TODO", "DONE"),
    ]
    lines = str(node).splitlines()
    assert lines[:4] == [
        "* Node",
        "  :LOGBOOK:",
        "  - State \"DONE\" from \"TODO\" [2005-09-01 Thu 16:10]",
        "  :END:",
    ]
    assert lines[4] == "  Body"


def test_add_repeated_tasks_with_logbook() -> None:
    content = """* Node
  :LOGBOOK:
  CLOCK: [2012-10-26 Fri 16:01]
  :END:
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = [
        OrgDateRepeatedTask((2005, 9, 1, 16, 10, 0), "TODO", "DONE"),
    ]
    lines = str(node).splitlines()
    assert "  CLOCK: [2012-10-26 Fri 16:01]" in lines
    assert "  - State \"DONE\" from \"TODO\" [2005-09-01 Thu 16:10]" in lines


def test_remove_repeated_tasks_without_logbook() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = []
    assert str(node) == content


def test_remove_repeated_tasks_with_logbook() -> None:
    content = """* Node
  :LOGBOOK:
  - State "DONE" from "TODO" [2005-09-01 Thu 16:10]
  :END:
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = []
    lines = str(node).splitlines()
    assert lines == ["* Node", "  :LOGBOOK:", "  :END:", "  Body"]


def test_multiple_logbook_drawers_update_all() -> None:
    content = """* Node
  :LOGBOOK:
  - State "DONE" from "TODO" [2005-09-01 Thu 16:10]
  :END:
  :LOGBOOK:
  - State "DONE" from "TODO" [2005-08-01 Mon 19:44]
  :END:
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = [
        OrgDateRepeatedTask((2005, 7, 1, 17, 27, 0), "TODO", "DONE"),
        OrgDateRepeatedTask((2005, 6, 1, 10, 0, 0), "TODO", "DONE"),
    ]
    rendered = str(node)
    assert rendered.count("[2005-07-01 Fri 17:27]") == 1
    assert rendered.count("[2005-06-01 Wed 10:00]") == 1


def test_external_repeated_tasks_update() -> None:
    content = """* Node
  - State "DONE" from "TODO" [2005-09-01 Thu 16:10]
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = [OrgDateRepeatedTask((2005, 7, 1, 17, 27, 0), "TODO", "DONE")]
    lines = str(node).splitlines()
    assert lines[1] == "  - State \"DONE\" from \"TODO\" [2005-07-01 Fri 17:27]"
    assert lines[2] == "  Body"


def test_remove_generated_logbook_when_cleared() -> None:
    content = """* Node
  Body"""
    node = loads(content).children[0]
    node.repeated_tasks = [OrgDateRepeatedTask((2005, 9, 1, 16, 10, 0), "TODO", "DONE")]
    node.repeated_tasks = []
    assert str(node) == content


def test_body_setter_preserves_structure() -> None:
    content = """* Node
  SCHEDULED: <2020-01-01 Wed>
  :PROPERTIES:
  :Foo: bar
  :END:
  - State "DONE" from "TODO" [2020-01-02 Thu]
  Body line 1
  Body line 2
  CLOCK: [2020-01-03 Fri 10:00]--[2020-01-03 Fri 11:00] =>  1:00"""
    node = loads(content).children[0]
    assert str(node) == content

    node.body = "New body\nSecond line"

    expected = """* Node
  SCHEDULED: <2020-01-01 Wed>
  :PROPERTIES:
  :Foo: bar
  :END:
  - State "DONE" from "TODO" [2020-01-02 Thu]
New body
Second line
  CLOCK: [2020-01-03 Fri 10:00]--[2020-01-03 Fri 11:00] =>  1:00"""
    assert str(node) == expected


def test_body_setter_clears_body() -> None:
    content = """* Node
  Body line 1
  Body line 2"""
    node = loads(content).children[0]
    node.body = ""
    assert node.body == ""
    assert str(node) == "* Node"


def test_body_setter_updates_timestamps() -> None:
    content = """* Node
  Body with <2020-01-01 Wed> and [2020-01-02 Thu]"""
    node = loads(content).children[0]
    assert [str(date) for date in node.datelist] == ["<2020-01-01 Wed>", "[2020-01-02 Thu]"]

    node.body = "New <2020-02-03 Mon>"
    assert [str(date) for date in node.datelist] == ["<2020-02-03 Mon>"]
