# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `find_temporal_resolution()` to general utils


### Changed

- *config* - moved temporal sub-section out of sensor config and into process config
- moved `validate_df()` to general utils

### Depreceated

### Removed

- utils module in quality control removed

### Fixed

### Security


## [0.11.0] - 08/07/2025

### Added

- estimates of measurement radius are included in the final output
- *CI/CD* - version bumps are automated via the tagging system for package publication
- introduced dataframe validataion using pandera schemas in estimate_sm module
- generic `_validate_df()` function in quality_control>utils.py to check data against pandera schemas

### Changed

- clarifyed in neutrons_to_soil_moisture - attributed named air_humidity renamed to abs_air_humidity
- CICD python package publishing is now done using uv instead of poetry


### Fixed

- fixed data ingest routine issue preventing reading files from a folder directory (with thanks to Till Francke)

