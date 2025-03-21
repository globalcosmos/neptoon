import pytest
from pathlib import Path
import sys
import platform
import subprocess
from unittest.mock import patch, Mock

from neptoon.cli.launcher import find_streamlit_executable, main


def test_find_streamlit_windows(monkeypatch):
    """Test finding streamlit on Windows."""
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(Path, "exists", lambda _: True)
    result = find_streamlit_executable()
    expected_path = Path(sys.executable).parent / "Scripts" / "streamlit.exe"
    assert result == expected_path


def test_find_streamlit_unix(monkeypatch):
    """Test finding streamlit on Unix-like systems."""
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(Path, "exists", lambda _: True)
    result = find_streamlit_executable()
    expected_path = Path(sys.executable).parent / "streamlit"
    assert result == expected_path


def test_main_successful_launch(monkeypatch):
    """Test that main launches streamlit with correct parameters."""
    streamlit_path = Path("/mock/path/to/streamlit")
    monkeypatch.setattr(
        "neptoon.cli.launcher.find_streamlit_executable",
        lambda: streamlit_path,
    )
    test_file_path = Path("/mock/path/to/cli.py")
    expected_app_path = test_file_path.parent.parent / "interface" / "gui.py"
    with patch("neptoon.cli.launcher.__file__", test_file_path):
        mock_run = Mock()
        monkeypatch.setattr(subprocess, "run", mock_run)
        main()
        mock_run.assert_called_once_with(
            [
                str(streamlit_path),
                "run",
                str(expected_app_path),
            ]
        )


def test_main_streamlit_not_found(monkeypatch):
    """Test main behavior when streamlit is not found."""
    monkeypatch.setattr(
        "neptoon.cli.launcher.find_streamlit_executable", lambda: None
    )
    mock_run = Mock()
    monkeypatch.setattr(subprocess, "run", mock_run)
    with pytest.raises(ValueError):
        main()
    mock_run.assert_not_called()
