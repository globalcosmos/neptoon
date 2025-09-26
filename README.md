# neptoon

[![PyPI version](https://img.shields.io/pypi/v/neptoon.svg)](https://pypi.org/project/neptoon/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17209375.svg)](https://doi.org/10.5281/zenodo.17209375)
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

```bash
pip install neptoon
```

Isolated Environment with **uv** (recommended):
```bash
uv init --python 3.10
uv add neptoon
```

Isolated Environment with **conda**:
```bash
conda create -n neptoon python=3.10 ipykernel
conda activate neptoon
pip install neptoon
```

For more detailed instructions, see the [installation documentation](https://www.neptoon.org/en/latest/user-guide/installation/).

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

Neptoon is currently in active development. Version 1.0, focusing on stability and robustness, is expected soon. Future plans include:

- Roving CRNS processing capabilities
- Server/Docker versions for automated processing

## Support and Contribution

- **Contact**: Email us at [contact@neptoon.org](mailto:contact@neptoon.org)
- **Issues**: Report bugs or request features through [GitLab issues](https://codebase.helmholtz.cloud/cosmos/neptoon/-/issues)
- **Contributing**: See the [contribution guidelines](https://www.neptoon.org/en/latest/contribution/overview-contribution/) for details on how to contribute

## Authors and Acknowledgments

**Lead Developers:**
- Daniel Power (daniel.power@ufz.de)
- Martin Schrön (martin.schroen@ufz.de)

**Additional Contributors:**
- Fredo Erxleben
- Steffen Zacharias
- Rafael Rosolem
- Louis Trinkle
- Daniel Rasche
- Markus Köhli

## License

Neptoon is licensed under the MIT License. See the [LICENSE](https://codebase.helmholtz.cloud/cosmos/neptoon/-/blob/main/LICENSE) file for details.

## Citation

> Power, D., Schrön, M., Erxleben, F., Rosolem, R., & Zacharias, S. (2025). "Neptoon". Zenodo. doi:[10.5281/zenodo.17209375](https://doi.org/10.5281/zenodo.17209375)

<details>
<summary>BibTex</summary>

```bibtex
@software{Neptoon,
  author       = {Power, Daniel and Schrön, Martin and Erxleben, Fredo and Rosolem, Rafael and Zacharias, Steffen},
  title        = {Neptoon},
  month        = sep,
  year         = 2025,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.17209375},
  url          = {https://doi.org/10.5281/zenodo.17209375},
}
```
</details>