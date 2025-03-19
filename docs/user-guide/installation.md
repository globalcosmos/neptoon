## Quick Install

For users familiar with Python, neptoon can be installed directly using pip:

```
pip install neptoon
```
## Recommended Installation
We strongly recommend installing neptoon in a dedicated environment to ensure reproducibility and prevent package conflicts.
Here some example scripts to do this using mamba or conda:

=== "Mamba"
    ```bash
    # Create a new environment with Python 3.10
    mamba create -n neptoon python=3.10 ipykernel
    # Activate the environment
    mamba activate neptoon
    # Install neptoon
    pip install neptoon
    ```
=== "Conda"
    ```bash
    # Create a new environment with Python 3.10
    conda create -n neptoon python=3.10 ipykernel
    # Activate the environment
    conda activate neptoon
    # Install neptoon
    pip install neptoon
    ```

!!! tip "Jupyter Integration"
    The ipykernel package is included to enable using neptoon in Jupyter notebooks, which is particularly useful for interactive data analysis and visualization. For example when working through the [examples](neptoon-examples.md). Leave this out if you don't need it.


## GUI Installation Guide

!!! info "**Work in Progress**"
    The GUI is now available in v0.6.0 to be installed locally. This is still a work in progress, and should be considered in a beta phase. Updates coming in the future.


Neptoon provides a graphical user interface (GUI) that enables researchers and practitioners to process Cosmic-Ray Neutron Sensor data without requiring Python programming expertise. This guide walks you through the installation and initial setup process for those users who expect to only need the GUI.

### 1. Install pipx

First, we'll install `pipx`, a specialized tool that manages Python applications in isolated environments. This ensures neptoon won't interfere with other Python applications on your system.

=== "Windows"
    ```powershell
    # Install pipx
    python -m pip install --user pipx
    python -m pipx ensurepath
    ```

=== "Unix/macOS"
    ```bash
    # Install pipx
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    ```

!!! note "Important"
    After installation, you'll need to restart your terminal for the changes to take effect.

### 2. Install neptoon

Once pipx is installed and your terminal has been restarted, install neptoon using:

```bash
pipx install "neptoon[gui]"
```

This command will:

- Downloads the latest stable version of neptoon
- Creates an isolated environment for the application
- Installs all necessary dependencies

### 3. Launch the GUI

```bash
neptoon-gui
```
When you execute this command:

- A local server will start automatically
- The launcher should automatically start in a browser window
- Your terminal will also display a URL (typically http://localhost:8501)
- You can copy this URL and open it in your web browser

### Uninstallation
 
If you need to remove neptoon from your system:

```bash
pipx uninstall neptoon
```

## Development Version Installation

If you want to install the latests features (before they have been fully tested and integrated) you might want to install the development version of neptoon using:

```
pip install git+https://codebase.helmholtz.cloud/cosmos/neptoon.git@development
```

!!! warning "Warning"
    We provide this as an option but would not recommend this for production ready data processing. The development branch is always in flux and so bugs might be present!
