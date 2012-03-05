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
>>> for node in root.traverse(include_self=False):
...     print node
* Heading 1
** Heading 2
*** Heading 3
>>> h1 = root.get_children()[0]
>>> h2 = h1.get_children()[0]
>>> h3 = h2.get_children()[0]
>>> print h1
* Heading 1
>>> print h2
** Heading 2
>>> print h3
*** Heading 3
>>> print h2.get_parent()
* Heading 1
>>> print h3.get_parent(max_level=1)
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
>>> node = root.get_children()[0]
>>> node.get_heading()
'Heading'
>>> node.get_scheduled()
OrgDateScheduled((2012, 2, 26))
>>> node.get_closed()
OrgDateClosed((2012, 2, 26, 21, 15, 0))
>>> node.get_clock()
[OrgDateClock((2012, 2, 26, 21, 10, 0), (2012, 2, 26, 21, 15, 0))]
>>> bool(node.get_deadline())   # it is not specified
False
>>> node.get_tags()
set(['TAG'])
>>> node.get_property('Effort')
60
>>> node.get_property('UndefinedProperty')  # returns None
>>> node.get_property('OtherProperty')
'some text'
>>> node.get_body()
'  Body texts...'

"""
# [[[end]]]


from orgparse.node import OrgEnv, lines_to_chunks

__all__ = ["load", "loads", "loadi"]


def load(path):
    """
    Load org-mode document from a file.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    if isinstance(path, basestring):
        orgfile = file(path)
    else:
        orgfile = path
    return loadi(l.rstrip('\n') for l in orgfile.readlines())


def loads(string):
    """
    Load org-mode document from a string.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return loadi(string.splitlines())


def loadi(lines):
    """
    Load org-mode document from an iterative object.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    env = OrgEnv()
    # parse into node of list (environment will be parsed)
    nodelist = list(env.from_chunks(lines_to_chunks(lines)))
    # parse headings (level, TODO, TAGs, and heading)
    for node in nodelist[1:]:   # nodes except root node
        node._parse_pre()
    # set the node tree structure
    for (n1, n2) in zip(nodelist[:-1], nodelist[1:]):
        level_n1 = n1.get_level()
        level_n2 = n2.get_level()
        if level_n1 == level_n2:
            n2.set_parent(n1.get_parent())
            n2.set_previous(n1)
        elif level_n1 < level_n2:
            n2.set_parent(n1)
        else:
            np = n1.get_parent(max_level=level_n2)
            if np.get_level() == level_n2:
                # * np    level=1
                # ** n1   level=2
                # * n2    level=1
                n2.set_parent(np.get_parent())
                n2.set_previous(np)
            else:  # np.get_level() < level_n2
                # * np    level=1
                # *** n1  level=3
                # ** n2   level=2
                n2.set_parent(np)
    return nodelist[0]  # root
