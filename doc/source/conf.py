import inspect
import os
import sys
from importlib.metadata import version as package_version
from pathlib import Path
from urllib.parse import quote

project = 'orgparse'
copyright = '2012, Takafumi Arakaki; orgparse contributors'  # noqa: A001
release = package_version(project)
version = release

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',
]
root_doc = 'index'
html_theme = 'alabaster'
html_baseurl = os.environ.get('READTHEDOCS_CANONICAL_URL', '')
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
autodoc_member_order = 'bysource'
autodoc_default_options = {'members': True}

repo_root = Path(__file__).resolve().parents[2]
source_ref = quote(os.environ.get('ORGPARSE_DOCS_REF', 'master'), safe='')


def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
    if domain != 'py' or not info['module'].startswith('orgparse'):
        return None

    obj = sys.modules[info['module']]
    for part in info['fullname'].split('.'):
        obj = inspect.getattr_static(obj, part, None)
        # Instance attributes can be documented without existing on the class.
        if obj is None:
            return None
    if isinstance(obj, property):
        obj = obj.fget
    if isinstance(obj, (classmethod, staticmethod)):
        obj = obj.__func__
    if not (inspect.isfunction(obj) or inspect.isclass(obj)):
        return None
    obj = inspect.unwrap(obj)

    filename = inspect.getsourcefile(obj)
    assert filename is not None, obj
    path = Path(filename).resolve()
    if not path.is_relative_to(repo_root):
        return None
    lines, start = inspect.getsourcelines(obj)
    relative_path = path.relative_to(repo_root).as_posix()
    return f'https://github.com/karlicoss/orgparse/blob/{source_ref}/{relative_path}#L{start}-L{start + len(lines) - 1}'
