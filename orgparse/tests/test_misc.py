from .. import load, loads
from ..node import OrgEnv
from orgparse.date import OrgDate


def test_empty_heading() -> None:
    root = loads('''
* TODO :sometag:
  has no heading but still a todo?
  it's a bit unclear, but seems to be highligted by emacs..
''')
    [h] = root.children
    assert h.todo == 'TODO'
    assert h.heading == ''
    assert h.tags == {'sometag'}


def test_root() -> None:
    root = loads('''
#+STARTUP: hidestars
Whatever
# comment
* heading 1
    '''.strip())
    assert len(root.children) == 1
    # todo not sure if should strip special comments??
    assert root.body.endswith('Whatever\n# comment')
    assert root.heading == ''


def test_stars():
    # https://github.com/karlicoss/orgparse/issues/7#issuecomment-533732660
    root = loads("""
* Heading with text (A)

The following line is not a heading, because it begins with a
star but has no spaces afterward, just a newline:

*

** Subheading with text (A1)

*this_is_just*

 *some_bold_text*

This subheading is a child of (A).

The next heading has no text, but it does have a space after
the star, so it's a heading:

* 

This text is under the "anonymous" heading above, which would be (B).

** Subheading with text (B1)

This subheading is a child of the "anonymous" heading (B), not of heading (A).
    """)
    [h1, h2] = root.children
    assert h1.heading == 'Heading with text (A)'
    assert h2.heading == ''


def test_parse_custom_todo_keys():
    todo_keys = ['TODO', 'CUSTOM1', 'ANOTHER_KEYWORD']
    done_keys = ['DONE', 'A']
    filename = '<string>'  # default for loads
    content = """
* TODO Heading with a default todo keyword

* DONE Heading with a default done keyword

* CUSTOM1 Heading with a custom todo keyword

* ANOTHER_KEYWORD Heading with a long custom todo keyword

* A Heading with a short custom done keyword
    """

    env = OrgEnv(todos=todo_keys, dones=done_keys, filename=filename)
    root = loads(content, env=env)

    assert root.env.all_todo_keys == ['TODO', 'CUSTOM1',
                                      'ANOTHER_KEYWORD', 'DONE', 'A']
    assert len(root.children) == 5
    assert root.children[0].todo == 'TODO'
    assert root.children[1].todo == 'DONE'
    assert root.children[2].todo == 'CUSTOM1'
    assert root.children[3].todo == 'ANOTHER_KEYWORD'
    assert root.children[4].todo == 'A'


def test_add_custom_todo_keys():
    todo_keys = ['CUSTOM_TODO']
    done_keys = ['CUSTOM_DONE']
    filename = '<string>'  # default for loads
    content = """#+TODO: COMMENT_TODO | COMMENT_DONE 
    """

    env = OrgEnv(filename=filename)
    env.add_todo_keys(todos=todo_keys, dones=done_keys)

    # check that only the custom keys are know before parsing
    assert env.all_todo_keys == ['CUSTOM_TODO', 'CUSTOM_DONE']

    # after parsing, all keys are set
    root = loads(content, filename, env)
    assert root.env.all_todo_keys == ['CUSTOM_TODO', 'COMMENT_TODO',
                                      'CUSTOM_DONE', 'COMMENT_DONE']

def test_get_file_property() -> None:
     content = """#+TITLE:   Test: title
     * Node 1
     test 1
     * Node 2
     test 2
     """

     # after parsing, all keys are set
     root = loads(content)
     assert root.get_file_property('Nosuchproperty') is None
     assert root.get_file_property_list('TITLE') == ['Test: title']
     # also it's case insensitive
     assert root.get_file_property('title') == 'Test: title'
     assert root.get_file_property_list('Nosuchproperty') == []


def test_get_file_property_multivalued() -> None:
     content = """ #+TITLE: Test
     #+OTHER: Test title
     #+title: alternate title

     * Node 1
     test 1
     * Node 2
     test 2
     """

     # after parsing, all keys are set
     root = loads(content)
     import pytest

     assert root.get_file_property_list('TITLE') == ['Test', 'alternate title']
     with pytest.raises(RuntimeError):
         # raises because there are multiple of them
         root.get_file_property('TITLE')


def test_filetags_are_tags() -> None:
    content = '''
#+FILETAGS: :f1:f2:

* heading :h1:
** child :f2:
    '''.strip()
    root = loads(content)
    # breakpoint()
    assert root.tags == {'f1', 'f2'}
    child = root.children[0].children[0]
    assert child.tags == {'f1', 'f2', 'h1'}


def test_load_filelike() -> None:
    import io
    stream = io.StringIO('''
* heading1
* heading 2
''')
    root = load(stream)
    assert len(root.children) == 2
    assert root.env.filename == '<file-like>'


def test_level_0_properties() -> None:
    content = '''
foo bar

:PROPERTIES:
:PROP-FOO: Bar
:PROP-BAR: Bar bar
:END:

* heading :h1:
:PROPERTIES:
:HEADING-PROP: foo
:END:
** child :f2:
    '''.strip()
    root = loads(content)
    assert root.get_property('PROP-FOO') == 'Bar'
    assert root.get_property('PROP-BAR') == 'Bar bar'
    assert root.get_property('PROP-INVALID') is None
    assert root.get_property('HEADING-PROP') is None
    assert root.children[0].get_property('HEADING-PROP') == 'foo'


def test_level_0_timestamps() -> None:
    content = '''
foo bar

  - <2010-08-16 Mon> DateList
  - <2010-08-07 Sat>--<2010-08-08 Sun>
  - <2010-08-09 Mon 00:30>--<2010-08-10 Tue 13:20> RangeList
  - <2019-08-10 Sat 16:30-17:30> TimeRange"

* heading :h1:
** child :f2:
    '''.strip()
    root = loads(content)
    assert root.datelist == [OrgDate((2010, 8, 16))]
    assert root.rangelist == [
        OrgDate((2010, 8, 7), (2010, 8, 8)),
        OrgDate((2010, 8, 9, 0, 30), (2010, 8, 10, 13, 20)),
        OrgDate((2019, 8, 10, 16, 30, 0), (2019, 8, 10, 17, 30, 0)),
    ]

def test_date_with_cookies() -> None:
    testcases = [
        ('<2010-06-21 Mon +1y>',
         "OrgDate((2010, 6, 21), None, True, ('+', 1, 'y'))"),
        ('<2005-10-01 Sat +1m>',
         "OrgDate((2005, 10, 1), None, True, ('+', 1, 'm'))"),
        ('<2005-10-01 Sat +1m -3d>',
         "OrgDate((2005, 10, 1), None, True, ('+', 1, 'm'), ('-', 3, 'd'))"),
        ('<2005-10-01 Sat -3d>',
         "OrgDate((2005, 10, 1), None, True, None, ('-', 3, 'd'))"),
        ('<2008-02-10 Sun ++1w>',
         "OrgDate((2008, 2, 10), None, True, ('++', 1, 'w'))"),
        ('<2008-02-08 Fri 20:00 ++1d>',
         "OrgDate((2008, 2, 8, 20, 0, 0), None, True, ('++', 1, 'd'))"),
        ('<2019-04-05 Fri 08:00 .+1h>',
         "OrgDate((2019, 4, 5, 8, 0, 0), None, True, ('.+', 1, 'h'))"),
        ('[2019-04-05 Fri 08:00 .+1h]',
         "OrgDate((2019, 4, 5, 8, 0, 0), None, False, ('.+', 1, 'h'))"),
        ('<2007-05-16 Wed 12:30 +1w>',
         "OrgDate((2007, 5, 16, 12, 30, 0), None, True, ('+', 1, 'w'))"),
    ]
    for (input, expected) in testcases:
        root = loads(input)
        output = root[0].datelist[0]
        assert str(output) == input
        assert repr(output) == expected
    testcases = [
        ('<2006-11-02 Thu 20:00-22:00 +1w>',
         "OrgDate((2006, 11, 2, 20, 0, 0), (2006, 11, 2, 22, 0, 0), True, ('+', 1, 'w'))"),
        ('<2006-11-02 Thu 20:00--22:00 +1w>',
         "OrgDate((2006, 11, 2, 20, 0, 0), (2006, 11, 2, 22, 0, 0), True, ('+', 1, 'w'))"),
    ]
    for (input, expected) in testcases:
        root = loads(input)
        output = root[0].rangelist[0]
        assert str(output) == "<2006-11-02 Thu 20:00--22:00 +1w>"
        assert repr(output) == expected
    # DEADLINE and SCHEDULED
    testcases2 = [
        ('* TODO Pay the rent\nDEADLINE: <2005-10-01 Sat +1m>',
         "<2005-10-01 Sat +1m>",
         "OrgDateDeadline((2005, 10, 1), None, True, ('+', 1, 'm'))"),
        ('* TODO Pay the rent\nDEADLINE: <2005-10-01 Sat +1m -3d>',
         "<2005-10-01 Sat +1m -3d>",
         "OrgDateDeadline((2005, 10, 1), None, True, ('+', 1, 'm'), ('-', 3, 'd'))"),
        ('* TODO Pay the rent\nDEADLINE: <2005-10-01 Sat -3d>',
         "<2005-10-01 Sat -3d>",
         "OrgDateDeadline((2005, 10, 1), None, True, None, ('-', 3, 'd'))"),
        ('* TODO Pay the rent\nDEADLINE: <2005-10-01 Sat ++1m>',
         "<2005-10-01 Sat ++1m>",
         "OrgDateDeadline((2005, 10, 1), None, True, ('++', 1, 'm'))"),
        ('* TODO Pay the rent\nDEADLINE: <2005-10-01 Sat .+1m>',
         "<2005-10-01 Sat .+1m>",
         "OrgDateDeadline((2005, 10, 1), None, True, ('.+', 1, 'm'))"),
    ]
    for (input, expected_str, expected_repr) in testcases2:
        root = loads(input)
        output = root[1].deadline
        assert str(output) == expected_str
        assert repr(output) == expected_repr
    testcases2 = [
        ('* TODO Pay the rent\nSCHEDULED: <2005-10-01 Sat +1m>',
         "<2005-10-01 Sat +1m>",
         "OrgDateScheduled((2005, 10, 1), None, True, ('+', 1, 'm'))"),
        ('* TODO Pay the rent\nSCHEDULED: <2005-10-01 Sat +1m -3d>',
         "<2005-10-01 Sat +1m -3d>",
         "OrgDateScheduled((2005, 10, 1), None, True, ('+', 1, 'm'), ('-', 3, 'd'))"),
        ('* TODO Pay the rent\nSCHEDULED: <2005-10-01 Sat -3d>',
         "<2005-10-01 Sat -3d>",
         "OrgDateScheduled((2005, 10, 1), None, True, None, ('-', 3, 'd'))"),
        ('* TODO Pay the rent\nSCHEDULED: <2005-10-01 Sat ++1m>',
         "<2005-10-01 Sat ++1m>",
         "OrgDateScheduled((2005, 10, 1), None, True, ('++', 1, 'm'))"),
        ('* TODO Pay the rent\nSCHEDULED: <2005-10-01 Sat .+1m>',
         "<2005-10-01 Sat .+1m>",
         "OrgDateScheduled((2005, 10, 1), None, True, ('.+', 1, 'm'))"),
    ]
    for (input, expected_str, expected_repr) in testcases2:
        root = loads(input)
        output = root[1].scheduled
        assert str(output) == expected_str
        assert repr(output) == expected_repr
