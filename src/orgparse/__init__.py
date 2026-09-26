"""Read Emacs org-mode files as trees of Python objects."""

from collections.abc import Iterable
from pathlib import Path
from typing import TextIO

from .node import OrgEnv, OrgNode, parse_lines  # todo basenode??

__all__ = ["load", "loadi", "loads"]


def load(path: str | Path | TextIO, env: OrgEnv | None = None) -> OrgNode:
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


def loads(string: str, filename: str = '<string>', env: OrgEnv | None = None) -> OrgNode:
    """
    Load org-mode document from a string.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return loadi(string.splitlines(), filename=filename, env=env)


def loadi(lines: Iterable[str], filename: str = '<lines>', env: OrgEnv | None = None) -> OrgNode:
    """
    Load org-mode document from an iterative object.

    :rtype: :class:`orgparse.node.OrgRootNode`

    """
    return parse_lines(lines, filename=filename, env=env)
