import subprocess
from pathlib import Path
import typer
import platform
import sys

app = typer.Typer()


def find_streamlit_executable():
    """Find streamlit executable in the current Python environment."""
    is_windows = platform.system() == "Windows"

    if is_windows:
        streamlit_path = (
            Path(sys.executable).parent / "Scripts" / "streamlit.exe"
        )
    else:
        streamlit_path = Path(sys.executable).parent / "streamlit"

    if streamlit_path.exists():
        return streamlit_path

    return None


@app.command()
def main():
    """Launch the neptoon GUI application."""
    app_path = Path(__file__).parent.parent / "interface" / "gui.py"

    streamlit_path = find_streamlit_executable()

    if streamlit_path is None:
        raise ValueError(
            "Streamlit executable not found. "
            "Please ensure streamlit is installed in your environment."
        )

    subprocess.run(
        [
            str(streamlit_path),
            "run",
            str(app_path),
        ]
    )


if __name__ == "__main__":
    app(standalone_mode=False)
