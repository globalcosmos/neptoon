import subprocess
from pathlib import Path
import typer
import platform
import sys
import shutil

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

    streamlit_in_path = shutil.which("streamlit")
    if streamlit_in_path:
        print(f"Found streamlit in PATH: {streamlit_in_path}")
        return Path(streamlit_in_path)

    print(f"Python executable: {sys.executable}")
    print(f"Looked in: {streamlit_path}")
    print("Searched PATH but couldn't find streamlit")

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
