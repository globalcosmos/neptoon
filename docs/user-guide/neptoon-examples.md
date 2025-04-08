
Sometimes it is better to simply work through examples and see how it works in practice. We provide a repository were you can download examples including data, configuration files and notebooks. 
Below we also include a brief description of what you can find in there so you can direct yourself to whatever is most useful.

https://codebase.helmholtz.cloud/cosmos/neptoon_examples 

!!! example "Quick Start"
    If you want to try out the neptoon examples without setting things up locally, try out the MyBinder link below!


# Setting Up Neptoon Examples

Here we'll explain how to set your environment up to work with the neptoon examples. 

## Quick Start

Here we show how to set up using the terminal. First, clone the examples repository and change into the downloaded repository with the following terminal command:

```bash
git clone https://codebase.helmholtz.cloud/cosmos/neptoon_examples.git
cd neptoon_examples
```

This will download the example data and scripts.

Next you want to create a python environment on your system to use neptoon. Below are some commands that will do just that for you, using the requirements.txt you've just downloaded from the examples repository.

=== "pip + venv (Windows)"
    Create and activate a virtual environment using Python's built-in venv:
    ```powershell
    python -m venv neptoon-env
    # Activate the environment:
    neptoon-env\Scripts\activate     # Windows
    
    # Install dependencies
    pip install -r requirements.txt
    
    ```
=== "pip + venv (Linux/macOS)"
    Create and activate a virtual environment using Python's built-in venv:
    ```bash
    python -m venv neptoon-env
    # Activate the environment:
    source neptoon-env/bin/activate  # Linux/macOS
    
    # Install dependencies
    pip install -r requirements.txt
    
    ```

=== "conda"
    Create and activate a Conda environment:
    ```bash
    conda create -n neptoon_examples python=3.10
    conda activate neptoon_examples
    
    # Install dependencies
    conda install --file requirements.txt
    
    ```

=== "mamba"
    Create and activate a Mamba environment (faster than conda):
    ```bash
    mamba create -n neptoon_examples python=3.10
    mamba activate neptoon_examples
    
    # Install dependencies
    mamba install --file requirements.txt
    
    ```

## Development Environments

### VS Code Setup

Whilst your terminal is still in the example repository - launch VSCode

1. Open project in VS Code:
    ```bash
    code .
    ```

2. Install essential VS Code extensions:
    - Python (ms-python.python)
    - Jupyter (ms-toolsai.jupyter)

3. Configure Python interpreter:

=== "pip + venv"
    ```
    1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
    2. Type "Python: Select Interpreter"
    3. Choose `./venv/bin/python` from the list
    ```

=== "conda/mamba"
    ```
    1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
    2. Type "Python: Select Interpreter"
    3. Look for `conda env:neptoon_examples` in the list
    ```

!!! tip "Environment Detection"
    If VS Code doesn't automatically detect your conda/mamba environment, try:
    1. Closing and reopening VS Code
    2. Running `conda init` in your terminal
    3. Ensuring the Python extension is properly installed


4. Working with notebooks:
    - Open `.ipynb` files directly in VS Code
    - Select your configured kernel (neptoon_examples)

### Jupyter Lab (Optional)

If installed, launch Jupyter Lab:

```bash
jupyter lab
```
Features:

- Browser-based interface at `http://localhost:8888`
- Multiple notebook support
- Integrated file browser

### MyBinder (No Installation)

For quick exploration without local setup:

  1. Visit [Neptoon Examples on MyBinder](https://mybinder.org/v2/git/https%3A%2F%2Fcodebase.helmholtz.cloud%2Fcosmos%2Fneptoon_examples/HEAD)
  2. Wait for environment to build - it could be a minute or two if no one has been on in a while
  3. Access notebooks directly in browser

!!! warning "Temporary"
    MyBinder sessions are temporary. All changes are lost after inactivity.

