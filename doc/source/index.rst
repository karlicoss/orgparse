.. orgparse documentation master file, created by
   sphinx-quickstart on Sun Mar  4 22:50:33 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. automodule:: orgparse
   :members:


Tree structure interface
========================

.. py:module:: orgparse.node

.. inheritance-diagram::
   orgparse.node.OrgBaseNode
   orgparse.node.OrgRootNode
   orgparse.node.OrgNode
   :parts: 1

.. autoclass:: OrgBaseNode
   :members:

   .. automethod:: __init__

.. autoclass:: OrgRootNode
   :members:

.. autoclass:: OrgNode
   :members:

.. autoclass:: OrgEnv
   :members:


Date interface
==============

.. py:module:: orgparse.date

.. inheritance-diagram::
   orgparse.date.OrgDate
   orgparse.date.OrgDateSDCBase
   orgparse.date.OrgDateScheduled
   orgparse.date.OrgDateDeadline
   orgparse.date.OrgDateClosed
   orgparse.date.OrgDateClock
   orgparse.date.OrgDateRpeatedTask
   :parts: 1

.. autoclass:: OrgDate
   :members:

   .. automethod:: __init__


Further resources
=================

.. toctree::

   dev

- `GitHub repository <https://github.com/tkf/orgparse>`_


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
