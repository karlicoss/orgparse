"""Regression tests for loading documents with an explicit environment."""

from pathlib import Path

import pytest

from .. import OrgEnv, load


@pytest.mark.parametrize('path_type', [str, Path])
@pytest.mark.parametrize('filename_type', [str, Path])
def test_load_with_env(
    *, tmp_path: Path, path_type: type[str] | type[Path], filename_type: type[str] | type[Path]
) -> None:
    """Accept matching Path/string filenames and preserve the environment's custom TODO states."""
    path = tmp_path / 'notes.org'
    path.write_text('* NEXT Task\n', encoding='utf-8')
    env = OrgEnv(filename=filename_type(path), todos=['NEXT'])

    root = load(path_type(path), env=env)

    assert root.env is env
    assert root.env.filename == str(path)
    [node] = root.children
    assert node.env is env
    assert node.todo == 'NEXT'
    assert node.heading == 'Task'


@pytest.mark.parametrize('filename_type', [str, Path])
def test_load_with_mismatched_env(*, tmp_path: Path, filename_type: type[str] | type[Path]) -> None:
    """Reject different source filenames, even when the basename matches."""
    path = tmp_path / 'notes.org'
    path.write_text('* Task\n', encoding='utf-8')
    env = OrgEnv(filename=filename_type(tmp_path / 'other' / 'notes.org'))

    with pytest.raises(ValueError, match='If env is specified, filename must match'):
        load(path, env=env)
