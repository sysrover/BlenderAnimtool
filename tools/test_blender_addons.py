from pathlib import Path

from blender_addons import file_hash, install_tree, tree_hash


def test_install_tree_copies_changes_and_verifies_hash(tmp_path: Path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "module.py").write_text("VALUE = 1\n", encoding="utf-8")

    first = install_tree(source, destination)
    assert first["copied"] == 1
    assert first["verified"] is True
    assert tree_hash(source) == tree_hash(destination)

    second = install_tree(source, destination)
    assert second["copied"] == 0

    (source / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
    third = install_tree(source, destination)
    assert third["copied"] == 1
    assert (destination / "module.py").read_text(encoding="utf-8") == "VALUE = 2\n"
    assert file_hash(source / "module.py") == file_hash(destination / "module.py")
