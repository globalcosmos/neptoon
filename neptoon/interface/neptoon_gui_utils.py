import io
from pathlib import Path
import tempfile
import streamlit as st


def cleanup(temp_file: Path):
    """Remove temporary file if it exists"""
    if isinstance(temp_file, Path) and temp_file.exists():
        temp_file.unlink(missing_ok=True)


def save_uploaded_file(uploaded_file: io.BytesIO):
    """
    Save uploaded file to a temporary location.

    Parameters
    ----------
    uploaded_file : StreamlitUploadedFile
        The uploaded file from Streamlit

    Returns
    -------
    Path
        Path to the saved temporary file
    """
    if uploaded_file is None:
        return None

    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return Path(tmp_file.name)


# Function to process uploaded file (cached)
@st.cache_data
def read_file(file):
    if file is not None:
        file = open(file, "r")
        return file.read()  # Read file content
    return None
