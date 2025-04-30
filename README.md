# neptoon

[![PyPI version](https://img.shields.io/pypi/v/neptoon.svg)](https://pypi.org/project/neptoon/)
[![Python Version](https://img.shields.io/pypi/pyversions/neptoon.svg)](https://pypi.org/project/neptoon/)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://www.neptoon.org)
[![License](https://img.shields.io/pypi/l/neptoon.svg)](https://codebase.helmholtz.cloud/cosmos/neptoon/-/blob/main/LICENSE)
[![PyPI Downloads](https://static.pepy.tech/badge/neptoon)](https://pepy.tech/projects/neptoon)

neptoon is a Python package for processing Cosmic-Ray Neutron Sensor (CRNS) data to produce field-scale soil moisture estimates. 

## Key Features

- **Modular Correction Pipeline**: Apply multiple correction methods for pressure, incoming intensity, humidity, and biomass
- **Quality Assessment**: Built-in data quality checks integrated with [SaQC](https://rdm-software.pages.ufz.de/saqc/index.html)
- **Sensor Calibration**: Tools for N0 calibration using soil sampling data
- **External Data Integration**: Automatic integration with NMDB.eu for incoming neutron corrections
- **Multiple Interfaces**: Use via Python API, configuration files, or GUI
- **Published Science**: Implementations based on peer-reviewed methodologies
- **Reproducibility**: Built-in reporting, reproduceable workflows, and comprehensive documentation

## Installation

### Basic Installation

```bash
pip install neptoon
```

### GUI Installation

```bash
pipx install "neptoon[gui]"
```

### Recommended Installation (Isolated Environment)

```bash
# Create a new environment with Python 3.10
conda create -n neptoon python=3.10 ipykernel
conda activate neptoon
pip install neptoon
```

For more detailed installation instructions, see the [installation documentation](https://www.neptoon.org/en/latest/user-guide/installation/).

## Quick Start

```python
from neptoon.io.read import DataHubFromConfig
from neptoon.workflow.process_with_yaml import ProcessWithConfig
from neptoon.config import ConfigurationManager

# Load configurations
config = ConfigurationManager()
config.load_configuration(file_path="path/to/sensor_config.yaml")
config.load_configuration(file_path="path/to/processing_config.yaml")

# Process data
yaml_processor = ProcessWithConfig(configuration_object=config)
yaml_processor.run_full_process()
```

Ready-to-use examples with sample data are available in the [neptoon_examples repository](https://codebase.helmholtz.cloud/cosmos/neptoon_examples).

## Documentation

Comprehensive documentation is available at:
- [www.neptoon.org](https://www.neptoon.org) - Main documentation
- [User Guide](https://www.neptoon.org/en/latest/user-guide/workflow-description/) - Detailed workflow description
- [Examples](https://www.neptoon.org/en/latest/user-guide/neptoon-examples/) - Practical examples and tutorials

## Project Status

neptoon is currently in active development. Version 1.0, focusing on stability and robustness, is expected soon. Future plans include:

- Roving CRNS processing capabilities
- Server/Docker versions for automated processing

## Support and Contribution

- **Issues**: Report bugs or request features through [GitLab issues](https://codebase.helmholtz.cloud/cosmos/neptoon/-/issues)
- **Contact**: Email us at [neptoon-contact@ufz.de](mailto:neptoon-contact@ufz.de)
- **Contributing**: See the [contribution guidelines](https://www.neptoon.org/en/latest/contribution/overview-contribution/) for details on how to contribute

## Authors and Acknowledgments

**Lead Developers:**
- Daniel Power (daniel.power@ufz.de)
- Martin Schrön (martin.schroen@ufz.de)

**Additional Contributors:**
- Fredo Erxleben
- Steffen Zacharias
- Rafael Rosolem

## License

neptoon is licensed under the MIT License. See the [LICENSE](https://codebase.helmholtz.cloud/cosmos/neptoon/-/blob/main/LICENSE) file for details.

## Citation

If you use neptoon in your research, please cite:

```
Power, D., Erxleben, F., Zacharias, S., Rosolem, R., & Schrön, M. (2025). neptoon (v0.8.2). Helmholtz Zentrum für Umweltforschung. https://doi.org/10.5281/zenodo.15181751
```