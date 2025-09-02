# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Depreceated

### Removed

### Fixed

### Security


## [0.13.0] 15/08/2025

### Added
- bespoke ways to calibrate data - such as finding only weights or equal weighting
- spike detection using simple offset rule


### Changed

- changed attribute naming from `koehlie_method_form` to `koehlie_parameters` throughout
- Refactored calibration routines back end
- default `koehlie_parameters` changed from `Mar21_uranos_drf` to `Mar21_mcnp_drf`

### Depreceated

### Removed

### Fixed

- broken links in documentation homepage (with thanks to Louis Trinkle)
- Fix Time Step calculation of `_calc_timestep_diff()`
    - now possible to load also daily data
- Add Parameters to `AboveGroundBiomassCorrectionBaatz2015()`
    - fixed parameter error for Biomass Correction
- Fixed issue where pressure units were not converted
- Magazine cleared after saving pdf - preventing problem with bad reports

### Security


## [0.12.1] - 12/08/2025

### Fix

- Fix bug when calling biomass functions

## [0.12.0] - 01/08/2025


### Added

- `find_temporal_resolution()` added to general utils
- `CRNSDataHub` - added functions to aggregate and align data directly to the CRNSDataHub
- new column name for raw neutron uncertainty added to ColumnInfo.Name
- Depreceation warning if temporal section is found in sensor config when loaded
- Docker builds for cli and gui interface

### Changed

- aggregation no longer happens on data import, aggregation now occurs after neutron correction to match the COSMOS standard and improve uncertainty quantification
- *config* - moved temporal sub-section out of sensor config and into process config
- moved `validate_df()` to general utils
- corrected neutron count uncertainty created in correct_neutron stage of data hub
- neutron uncertainty bounds created in estimate_sm module just before being used (allows for changes due to aggregation)
- when aggregating data, the data needs to be aligned prior to aggregation to account for missing rows
- renamed humidity correction `omega` in process config file to `coefficient` (breaking)
- pressure correction now uses fixed reference of `1013.25` hPa (based on upcoming cosmos standard)
- renamed `koehli_method_form` to `koehli_etal_2021_parameterset` in process config (breaking)

### Depreceated

- `temporal` section in sensor config is depreceated - moved into process config as `temporal_aggregation` section

### Removed

- utils module in quality control removed
- NeutronUncertaintyCalculator class removed
- removed function in CRNSDataHub and ProcessWithConfig to produce uncertainty (integrated to other parts) e.g., `data_hub.create_neutron_uncertainty_bounds()` 
- polyorder setting in process config - reintroduce when it can be used in SG filter

### Fixed

- updated NMDB data fetching to use new URL
- update minimum version for pandera
- attribute issue in ColumnInfo and NeutronsToSM

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

