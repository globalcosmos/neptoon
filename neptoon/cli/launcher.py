import sys
import subprocess
from pathlib import Path
import typer

app = typer.Typer()


@app.command()
def main():
    """Launch the neptoon GUI application."""
    # Get path to the app.py relative to this launcher
    app_path = Path(__file__).parent.parent / "interface" / "gui.py"

    # Run streamlit with the app
    subprocess.run(
        [
            "streamlit",
            "run",
            str(app_path),
        ]
    )


if __name__ == "__main__":
    app(standalone_mode=False)
