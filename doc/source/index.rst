.. orgparse documentation master file, created by
   sphinx-quickstart on Sun Mar  4 22:50:33 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. automodule:: orgparse


Tree structure interface
========================

.. py:module:: orgparse.node

.. inheritance-diagram::
   orgparse.node.OrgBaseNode
   orgparse.node.OrgRootNode
   orgparse.node.OrgNode
   :parts: 1

.. autoclass:: OrgBaseNode

   .. automethod:: __init__

.. autoclass:: OrgRootNode

.. autoclass:: OrgNode

.. autoclass:: OrgEnv


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
   orgparse.date.OrgDateRepeatedTask
   :parts: 1

.. autoclass:: OrgDate

   .. automethod:: __init__

.. autoclass:: OrgDateScheduled
.. autoclass:: OrgDateDeadline
.. autoclass:: OrgDateClosed
.. autoclass:: OrgDateClock
.. autoclass:: OrgDateRepeatedTask


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
