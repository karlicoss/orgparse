# Import README.rst using cog
# [[[cog
# from cog import out
# out('"""\n{0}\n"""'.format(open('../README.rst').read()))
# ]]]
"""
===========================================================
  orgparse - Python module for reading Emacs org-mode files
===========================================================


* `Documentation (Read the Docs) <https://orgparse.readthedocs.org>`_
* `Repository (at GitHub) <https://github.com/karlicoss/orgparse>`_
* `PyPI <https://pypi.python.org/pypi/orgparse>`_

Install
-------

  pip install orgparse


Usage
-----

There are pretty extensive doctests if you're interested in some specific method. Otherwise here are some example snippets:


Load org node
^^^^^^^^^^^^^
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


Accessing node attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

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

from io import IOBase
from pathlib import Path
from typing import Iterable, Union, Optional, TextIO


from .node import parse_lines, OrgEnv, OrgNode  # todo basenode??

__author__ = 'Takafumi Arakaki, Dmitrii Gerasimov'
__license__ = 'BSD License'
__all__ = ["load", "loads", "loadi"]


def load(path: Union[str, Path, TextIO], env: Optional[OrgEnv] = None) -> OrgNode:
    """
    Load org-mode document from a file.

    :type path: str or file-like
    :arg  path: Path to org file or file-like object of an org document.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    # Make sure it is a Path object.
    if isinstance(path, str):
        path = Path(path)

    # if it is a Path
    if isinstance(path, Path):
        # open that Path
        with path.open('r', encoding='utf8') as orgfile:
            # try again loading
            return load(orgfile, env)

    # We assume it is a file-like object (e.g. io.StringIO)
    all_lines = (line.rstrip('\n') for line in path)

    # get the filename
    filename = path.name if hasattr(path, 'name') else '<file-like>'

    return loadi(all_lines, filename=filename, env=env)


def loads(string: str, filename: str='<string>', env: Optional[OrgEnv]=None) -> OrgNode:
    """
    Load org-mode document from a string.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return loadi(string.splitlines(), filename=filename, env=env)


def loadi(lines: Iterable[str], filename: str='<lines>', env: Optional[OrgEnv]=None) -> OrgNode:
    """
    Load org-mode document from an iterative object.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return parse_lines(lines, filename=filename, env=env)
