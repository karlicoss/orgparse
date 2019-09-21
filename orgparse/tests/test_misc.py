from .. import load, loads

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

