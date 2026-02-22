from __future__ import annotations

from pathlib import Path

from .. import dump, dumps, load, loads


def test_dump_roundtrip(tmp_path: Path) -> None:
    content = """* Node
  Body"""
    source = tmp_path / "source.org"
    target = tmp_path / "target.org"
    source.write_text(content, encoding="utf8")

    root = load(source)
    dump(root, target)

    assert target.read_text(encoding="utf8") == content


def test_dumps_iterable_nodes() -> None:
    root = loads("""* A
* B""")
    output = dumps(root.children)
    assert (
        output
        == """* A
* B"""
    )


def test_dump_reflects_updates() -> None:
    root = loads("""* Node
  Body""")
    node = root.children[0]
    node.heading = "Updated"
    node.body = "New body"

    assert (
        dumps(root)
        == """* Updated
New body"""
    )


def test_dump_multiple_nodes(tmp_path: Path) -> None:
    root = loads("""* A
* B""")
    target = tmp_path / "nodes.org"

    dump(root.children, target)

    assert (
        target.read_text(encoding="utf8")
        == """* A
* B"""
    )
