from pathlib import Path

import pytest

import rainbowterm.files as f
import rainbowterm.utils as u


@pytest.fixture
def paths(tmp_path: Path) -> f.Paths:
    return f.Paths(tmp_path, tmp_path)


@pytest.fixture
def filestore(paths: f.Paths) -> f.FileStore:
    return f.FileStore(paths)


def test_read_file(tmp_path: Path):
    path = tmp_path / "foo.txt"
    path.write_text(" stuff ")
    assert f.read_file(path) == "stuff"


def test_read_nonexistent_file(tmp_path: Path):
    path = tmp_path / "foo.txt"
    with pytest.raises(FileNotFoundError):
        f.read_file(path)


def test_write_file(tmp_path: Path):
    path = tmp_path / "foo.txt"
    f.write_file(path, " stuff ")
    assert path.read_text() == " stuff \n"


def test_paths_direct():
    paths = f.Paths(Path("/conf"), Path("/dat"))
    assert paths.config("foo") == Path("/conf/foo")
    assert paths.data("foo") == Path("/dat/foo")


def test_paths_xdg_explicit(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/conf")
    monkeypatch.setenv("XDG_DATA_HOME", "/dat")
    paths = f.Paths.xdg("sub")
    assert paths.config("foo") == Path("/conf/sub/foo")
    assert paths.data("foo") == Path("/dat/sub/foo")


def test_paths_xdg_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    paths = f.Paths.xdg("sub")
    assert paths.config("foo") == Path.home() / ".config/sub/foo"
    assert paths.data("foo") == Path.home() / ".local/share/sub/foo"


def test_config_default(tmp_path: Path):
    config = f.Config.load(f.Paths(tmp_path, tmp_path))
    assert config.get("animation", "frames") == "100"


def test_config_override(paths: f.Paths):
    with open(paths.config("config.ini"), "w") as file:
        print("[animation]\nframes=42", file=file)
    config = f.Config.load(paths)
    assert config.int("animation", "frames") == 42


def test_config_bad(paths: f.Paths):
    with open(paths.config("config.ini"), "w") as file:
        print("[", file=file)
    with pytest.raises(u.FatalError, match="config.ini"):
        f.Config.load(paths)


def test_config_bool(paths: f.Paths):
    with open(paths.config("config.ini"), "w") as file:
        print("[foo]\na=false\nb=true\nc=TrUe\nd=1", file=file)
    config = f.Config.load(paths)
    assert not config.bool("foo", "a")
    assert config.bool("foo", "b")
    assert config.bool("foo", "c")
    with pytest.raises(u.FatalError, match="foo.d"):
        config.bool("foo", "d")


def test_config_value(paths: f.Paths):
    config = f.Config.load(paths)
    assert config.int("animation", "frames", gt=99, lt=101) == 100
    with pytest.raises(u.FatalError, match="animation.frames"):
        config.int("animation", "frames", ne=100)


def test_filestore_favorites_no_file(filestore: f.FileStore):
    assert filestore.favorites == set()


def test_filestore_favorites_read(tmp_path: Path, filestore: f.FileStore):
    with open(tmp_path / "favorites", "w") as file:
        print("a\nb\nc", file=file)
    assert filestore.favorites == {"a", "b", "c"}


def test_filestore_favorites_write(tmp_path: Path, filestore: f.FileStore):
    filestore.favorites = {"a", "b", "c"}
    assert filestore.favorites == {"a", "b", "c"}
    with open(tmp_path / "favorites") as file:
        assert file.read() == "a\nb\nc\n"


def test_filestore_smart_history_no_file(filestore: f.FileStore):
    assert filestore.smart_history == []


def test_filestore_smart_history_read(tmp_path: Path, filestore: f.FileStore):
    with open(tmp_path / "smart_history", "w") as file:
        print("a\nb\nc", file=file)
    assert filestore.smart_history == ["a", "b", "c"]


def test_filestore_smart_history_write(tmp_path: Path, filestore: f.FileStore):
    filestore.smart_history = ["a", "b", "c"]
    assert filestore.smart_history == ["a", "b", "c"]
    with open(tmp_path / "smart_history") as file:
        assert file.read() == "a\nb\nc\n"


def test_filestore_smart_history_max(tmp_path: Path, filestore: f.FileStore):
    history = [str(i) for i in range(f.MAX_SMART_HISTORY + 1)]
    filestore.smart_history = history
    assert filestore.smart_history == history[1:]
