[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://www.neptoon.org)


## **What is neptoon?**

neptoon is a Python package for processing Cosmic-Ray Neutron Sensor (CRNS) data. CRNS technology provides field-scale soil moisture estimates by measuring fast neutron counts, which are inversely proportional to hydrogen content in the soil.


The package handles the full workflow for CRNS data processing, including:

- Data ingestion and preprocessing from various formats
- Quality control and data validation
- Correction for environmental factors (pressure, humidity, incoming neutron intensity, biomass)
- Calibration procedures
- Soil moisture estimation with uncertainty quantification
- Visualization and data export

neptoon offers both simple workflows for standard processing needs and advanced capabilities for researchers who want to experiment with new correction algorithms and calibration approaches.

## **Key Features**

- **Modular Architecture**: Process data through customizable pipelines
- **Graphical User Interface**: No code processing
- **Process with Configuration files**: Easily define and share processing workflows
- **Quality Control**: Built-in data validation with configurable quality assessment
- **Correction Methods**: Correct using published correction theories
- **Visualization Tools**: Create standardized plots
- **Extensibility**: Create and test new correction methods without changing core code
- **External Data Integration**: Direct access to external datasets when processing data

## Documentation

Comprehensive documentation is available at [https://neptoon-docs.readthedocs.io/](https://neptoon-docs.readthedocs.io/)

## Installation

### Using pip

```bash
pip install neptoon
```
### More installation options

Read the [installation docs](https://www.neptoon.org/en/latest/user-guide/installation/)

## Usage

Read the [examples docs](https://www.neptoon.org/en/latest/user-guide/neptoon-examples/)

## Architecture

neptoon is built around several key components:

- **CRNSDataHub**: Central class managing the time series data
- **Corrections**: Modular framework for different correction methods
- **Quality Control**: Data validation and flagging mechanisms using [SaQC]
- **Configuration**: Object models for standardized parameter validation
- **Workflow**: High-level processing pipelines
- **Visualization**: Standardized plotting capabilities

## Support

For questions and support, please contact:

- neptoon-users@ufz.de

For bug reports or feature requests, please use the GitLab issue tracker.

## Contributing

We gladly accept contributions. More information on how to contribute [contribution docs](https://www.neptoon.org/en/latest/contribution/overview-contribution/)

## Authors

**Core Developers**
Daniel Power, Martin Schrön

**Code Contributors**
Fredo Erxleben, Till Francke

## Acknowledgments

neptoon is being actively developed and maintained by the CRNS research group at Helmholtz-Zentrum für Umweltforschung (UFZ) and the University of Bristol.



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

