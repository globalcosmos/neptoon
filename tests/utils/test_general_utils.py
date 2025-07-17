import pytest
from pathlib import Path
from neptoon.utils.general_utils import (
    validate_and_convert_file_path,
    parse_resolution_to_timedelta,
)


def test_file_path_none():
    """Test None Path"""
    tmp = validate_and_convert_file_path(file_path=None)
    assert tmp == None


def test_file_path_str():
    """Test conversion to Path"""
    tmp = validate_and_convert_file_path(file_path="tmp/path")
    assert isinstance(tmp, Path)


def test_file_path_str():
    """Test conversion to Path with base"""
    base = "/base_path/"
    tmp = validate_and_convert_file_path(
        file_path="test/path",
        base=base,
    )
    assert isinstance(tmp, Path)
    assert "base_path" in tmp.parts
    expected = Path(base) / "test/path"
    assert tmp == expected.resolve()


def test_abs_file_path_and_base():
    """Tests AttributeError when a base and an absolute filepath are
    given"""
    base = "/base_path/"
    abs_path = "/abs/path/"
    with pytest.raises(AttributeError):
        tmp = validate_and_convert_file_path(
            file_path=abs_path,
            base=base,
        )


def test_parse_resolution_good():
    hours = parse_resolution_to_timedelta(resolution_str="1hour")
