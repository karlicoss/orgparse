# orgparse — Python module for reading Emacs org-mode files


- [Documentation (Read the Docs)](https://orgparse.readthedocs.org)
- [Repository (GitHub)](https://github.com/karlicoss/orgparse)
- [PyPI](https://pypi.org/project/orgparse/)
- [conda-forge](https://anaconda.org/conda-forge/orgparse)

## Install

You can install `orgparse` via PyPI:

``` console
pip install orgparse
```

Or via conda-forge:

``` console
conda install orgparse -c conda-forge
```

## Usage

The API documentation includes extensive doctests for individual methods.
Here are some examples to get started.

### Load an org document

``` python
from orgparse import load, loads

load('PATH/TO/FILE.org')
load(file_like_object)

loads('''
* This is org-mode contents
  You can load org object from string.
** Second header
''')
```

See the [loading implementation](https://github.com/karlicoss/orgparse/blob/master/src/orgparse/__init__.py#L12-L39).

### Traverse an org tree

``` pycon
>>> from orgparse import loads
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
```

### Access node attributes

``` pycon
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
>>> bool(node.deadline)  # it is not specified
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
```

### Read named tables

Tables in `node.body_rich` expose their `#+NAME:` through `Table.name`.
The name is `None` for unnamed tables.

``` pycon
>>> from orgparse.extra import Table
>>> root = loads('''
... #+NAME: measurements
... | x | y |
... |---+---|
... | 1 | 2 |
... ''')
>>> [table] = [part for part in root.body_rich if isinstance(part, Table) and part.name == 'measurements']
>>> list(table.as_dicts)
[{'x': '1', 'y': '2'}]
```

### More examples

The tests show additional supported features:

- [Custom TODO keywords](https://github.com/karlicoss/orgparse/blob/master/src/orgparse/tests/test_misc.py#L72-L97)
- [File-level tags](https://github.com/karlicoss/orgparse/blob/master/src/orgparse/tests/test_misc.py#L155-L166)
- [Reading tables](https://github.com/karlicoss/orgparse/blob/master/src/orgparse/tests/test_rich.py#L11-L61)

## Development and documentation

Clone with `git clone --recurse-submodules https://github.com/karlicoss/orgparse.git` to include the test corpus.
For an existing checkout, run `git submodule update --init --recursive`.

Run the tests with `uv tool run --with tox-uv tox -e tests`.
This also checks the examples in this README.

Corpus tests parse upstream Org examples, Sacha Chua’s Emacs configuration, exobrain notes, and nvim-orgmode documents from `testdata/external`.
They check tree structure, source line ranges, and attribute access.

Edit `README.qmd`, then regenerate `README.md` with `uv tool run --with tox-uv tox -e quarto`.
Quarto computes links to source code and tests from their definitions, so line numbers are refreshed when rendering.
Commit both files together; CI checks that the generated README is current.

Build the documentation with `uv tool run --with tox-uv tox -e docs` and open `doc/_build/html/index.html`.
Sphinx combines the generated README with the API docstrings; it does not need Quarto to build the site.

Read the Docs uses `.readthedocs.yaml` to run the same `docs` environment.
The `latest` version follows `master`, and `stable` follows releases.
Automatic builds require the GitHub integration in the [Read the Docs project settings](https://app.readthedocs.org/projects/orgparse/).

## Project status

The project is maintained by [@karlicoss](https://github.com/karlicoss).

For my personal use, orgparse mostly has all features I need, so there hasn’t been much active development lately.

However, contributions are always welcome!
Please provide tests along with your contribution if you’re fixing bugs or adding new functionality.
