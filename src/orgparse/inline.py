"""
Org-mode inline markup parser.
"""

import re


def to_plain_text(org_text):
    """
    Convert an org-mode text into a plain text.

    >>> to_plain_text('there is a [[link]] in text')
    'there is a link in text'
    >>> to_plain_text('some [[link][more complex link]] here')
    'some more complex link here'
    >>> print(to_plain_text('''It can handle
    ... [[link][multi
    ... line
    ... link]].
    ... See also: [[info:org#Link%20format][info:org#Link format]]'''))
    It can handle
    multi
    line
    link.
    See also: info:org#Link format

    """
    return RE_LINK.sub(
        lambda m: m.group('desc0') or m.group('desc1'),
        org_text)


RE_LINK = re.compile(
    r"""
    (?:
        \[ \[
            (?P<desc0> [^\]]+)
        \] \]
    ) |
    (?:
        \[ \[
            (?P<link1> [^\]]+)
        \] \[
            (?P<desc1> [^\]]+)
        \] \]
    )
    """,
    re.VERBOSE)
