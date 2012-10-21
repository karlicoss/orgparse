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
...     print(node)
* Heading 1
** Heading 2
*** Heading 3
>>> h1 = root.get_children()[0]
>>> h2 = h1.get_children()[0]
>>> h3 = h2.get_children()[0]
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
