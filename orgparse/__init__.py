# Import README.rst using cog
# [[[cog
# from cog import out
# out('"""\n{0}\n"""'.format(file('../README.rst').read()))
# ]]]
"""
===========================================================
  orgparse - Pyton module for reading Emacs org-mode file
===========================================================

Usage
-----

Loading org object
^^^^^^^^^^^^^^^^^^
::

    from orgparse import load, loads

    load('PATH/TO/FILE.org')
    load(file_like_object)

    loads('''
    * This is org-mode contents
      You can load org object from string.
    ** Second header
    ''')


Traverse org tree
^^^^^^^^^^^^^^^^^

>>> root = loads('''
... * Heading 1
... ** Heading 2
... *** Heading 3
... ''')
>>> for node in root[1:]:  # [1:] for skipping root itself
...     print(node)
* Heading 1
** Heading 2
*** Heading 3
>>> h1 = root.children[0]
>>> h2 = h1.children[0]
>>> h3 = h2.children[0]
>>> print(h1)
* Heading 1
>>> print(h2)
** Heading 2
>>> print(h3)
*** Heading 3
>>> print(h2.get_parent())
* Heading 1
>>> print(h3.get_parent(max_level=1))
* Heading 1


Accessing to node attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> root = loads('''
... * DONE Heading          :TAG:
...   CLOSED: [2012-02-26 Sun 21:15] SCHEDULED: <2012-02-26 Sun>
...   CLOCK: [2012-02-26 Sun 21:10]--[2012-02-26 Sun 21:15] =>  0:05
...   :PROPERTIES:
...   :Effort:   1:00
...   :OtherProperty:   some text
...   :END:
...   Body texts...
... ''')
>>> node = root.children[0]
>>> node.heading
'Heading'
>>> node.scheduled
OrgDateScheduled((2012, 2, 26))
>>> node.closed
OrgDateClosed((2012, 2, 26, 21, 15, 0))
>>> node.clock
[OrgDateClock((2012, 2, 26, 21, 10, 0), (2012, 2, 26, 21, 15, 0))]
>>> bool(node.deadline)   # it is not specified
False
>>> node.tags == set(['TAG'])
True
>>> node.get_property('Effort')
60
>>> node.get_property('UndefinedProperty')  # returns None
>>> node.get_property('OtherProperty')
'some text'
>>> node.body
'  Body texts...'

"""
# [[[end]]]

import codecs

from orgparse.node import parse_lines
from orgparse.py3compat import basestring

__version__ = '0.0.1.dev0'
__author__ = 'Takafumi Arakaki'
__license__ = 'BSD License'
__all__ = ["load", "loads", "loadi"]


def load(path):
    """
    Load org-mode document from a file.

    :type path: str or file-like
    :arg  path: Path to org file or file-like object of a org document.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    if isinstance(path, basestring):
        orgfile = codecs.open(path, encoding='utf8')
        filename = path
    else:
        orgfile = path
        filename = path.name if hasattr(path, 'name') else '<file-like>'
    return loadi((l.rstrip('\n') for l in orgfile.readlines()),
                 filename=filename)


def loads(string, filename='<string>'):
    """
    Load org-mode document from a string.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return loadi(string.splitlines(), filename=filename)


def loadi(lines, filename='<lines>'):
    """
    Load org-mode document from an iterative object.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return parse_lines(lines, filename=filename)
