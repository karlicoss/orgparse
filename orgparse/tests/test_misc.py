from .. import load, loads
from ..node import OrgEnv


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
