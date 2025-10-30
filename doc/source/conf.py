import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# -- General configuration ------------------------------------------------
extensions = [
    'sphinx.ext.todo',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
]
templates_path = []  # ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# TODO not sure I'm doing that right..
import orgparse

# General information about the project.
project = 'orgparse'
copyright = '2012, Takafumi Arakaki'  # noqa: A001

# The short X.Y version.
# TODO use setup.py for version
version = orgparse.__version__  # ty: ignore[unresolved-attribute]
# The full version, including alpha/beta/rc tags.
release = orgparse.__version__  # ty: ignore[unresolved-attribute]

exclude_patterns = []

pygments_style = 'sphinx'


# -- Options for HTML output ----------------------------------------------
html_theme = 'default'
html_static_path = []  # ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'orgparsedoc'


# -- Options for LaTeX output ---------------------------------------------
latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto/manual]).
latex_documents = [
    ('index', 'orgparse.tex', 'orgparse Documentation', 'Takafumi Arakaki', 'manual'),
]


# -- Options for manual page output ---------------------------------------
# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'orgparse', 'orgparse Documentation', ['Takafumi Arakaki'], 1),
]

# If true, show URL addresses after external links.
# man_show_urls = False


# -- Options for Texinfo output -------------------------------------------
# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        'index',
        'orgparse',
        'orgparse Documentation',
        'Takafumi Arakaki',
        'orgparse',
        'One line description of project.',
        'Miscellaneous',
    ),
]


# -- Options for extensions -----------------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/': None}

autodoc_member_order = 'bysource'
autodoc_default_flags = ['members']

inheritance_graph_attrs = {'rankdir': "TB"}
