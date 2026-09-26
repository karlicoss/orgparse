.. include:: ../../README.md
   :parser: myst_parser.sphinx_


Loading documents
=================

.. automodule:: orgparse
   :members: load, loads, loadi


Tree structure interface
========================

.. py:module:: orgparse.node

.. autoclass:: OrgBaseNode

   .. automethod:: __init__

.. autoclass:: OrgRootNode

.. autoclass:: OrgNode

.. autoclass:: OrgEnv


Date interface
==============

.. py:module:: orgparse.date

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

- `GitHub repository <https://github.com/karlicoss/orgparse>`_


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
