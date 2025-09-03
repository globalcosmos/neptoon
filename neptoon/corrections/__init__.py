_LAZY_IMPORTS = {
    # From theory.above_ground_biomass_corrections
    "above_ground_biomass_correction_baatz2015": (
        "neptoon.corrections.theory.above_ground_biomass_corrections",
        "above_ground_biomass_correction_baatz2015",
    ),
    "above_ground_biomass_correction_morris2024": (
        "neptoon.corrections.theory.above_ground_biomass_corrections",
        "above_ground_biomass_correction_morris2024",
    ),
    # From theory.air_humidity_corrections
    "humidity_correction_rosolem2013": (
        "neptoon.corrections.theory.air_humidity_corrections",
        "humidity_correction_rosolem2013",
    ),
    "calc_absolute_humidity": (
        "neptoon.corrections.theory.air_humidity_corrections",
        "calc_absolute_humidity",
    ),
    "calc_saturation_vapour_pressure": (
        "neptoon.corrections.theory.air_humidity_corrections",
        "calc_saturation_vapour_pressure",
    ),
    "calc_vapour_pressure_from_dewpoint_temp": (
        "neptoon.corrections.theory.air_humidity_corrections",
        "calc_vapour_pressure_from_dewpoint_temp",
    ),
    "calc_relative_humidity_from_dewpoint_temperature": (
        "neptoon.corrections.theory.air_humidity_corrections",
        "calc_relative_humidity_from_dewpoint_temperature",
    ),
    "calc_actual_vapour_pressure": (
        "neptoon.corrections.theory.air_humidity_corrections",
        "calc_actual_vapour_pressure",
    ),
    # From theory.calibration_functions
    "Schroen2017": (
        "neptoon.corrections.theory.calibration_functions",
        "Schroen2017",
    ),
    # From theory.incoming_intensity_corrections
    "incoming_intensity_correction": (
        "neptoon.corrections.theory.incoming_intensity_corrections",
        "incoming_intensity_correction",
    ),
    "rc_correction_hawdon": (
        "neptoon.corrections.theory.incoming_intensity_corrections",
        "rc_correction_hawdon",
    ),
    "McjannetDesilets2023": (
        "neptoon.corrections.theory.incoming_intensity_corrections",
        "McjannetDesilets2023",
    ),
    # From theory.neutrons_to_soil_moisture
    "neutrons_to_total_grav_soil_moisture_desilets_etal_2010": (
        "neptoon.corrections.theory.neutrons_to_soil_moisture",
        "neutrons_to_total_grav_soil_moisture_desilets_etal_2010",
    ),
    "neutrons_to_total_grav_soil_moisture_koehli_etal_2021": (
        "neptoon.corrections.theory.neutrons_to_soil_moisture",
        "neutrons_to_total_grav_soil_moisture_koehli_etal_2021",
    ),
    "reformulated_neutrons_to_grav_soil_moisture_desilets_2010": (
        "neptoon.corrections.theory.neutrons_to_soil_moisture",
        "reformulated_neutrons_to_grav_soil_moisture_desilets_2010",
    ),
    # From theory.pressure_corrections
    "calc_pressure_correction_beta_coeff": (
        "neptoon.corrections.theory.pressure_corrections",
        "calc_pressure_correction_beta_coeff",
    ),
    "calc_mean_pressure": (
        "neptoon.corrections.theory.pressure_corrections",
        "calc_mean_pressure",
    ),
    "calc_beta_coefficient": (
        "neptoon.corrections.theory.pressure_corrections",
        "calc_beta_coefficient",
    ),
    "dunai_2020": (
        "neptoon.corrections.theory.pressure_corrections",
        "dunai_2020",
    ),
    # From factory.build_corrections
    "CorrectionTheory": (
        "neptoon.corrections.factory.build_corrections",
        "CorrectionTheory",
    ),
    "CorrectionType": (
        "neptoon.corrections.factory.build_corrections",
        "CorrectionType",
    ),
    "Correction": (
        "neptoon.corrections.factory.build_corrections",
        "Correction",
    ),
    # From factory.correction_classes
    "IncomingIntensityCorrectionZreda2012": (
        "neptoon.corrections.factory.correction_classes",
        "IncomingIntensityCorrectionZreda2012",
    ),
    "IncomingIntensityCorrectionHawdon2014": (
        "neptoon.corrections.factory.correction_classes",
        "IncomingIntensityCorrectionHawdon2014",
    ),
    "HumidityCorrectionRosolem2013": (
        "neptoon.corrections.factory.correction_classes",
        "HumidityCorrectionRosolem2013",
    ),
    "PressureCorrectionZreda2012": (
        "neptoon.corrections.factory.correction_classes",
        "PressureCorrectionZreda2012",
    ),
}

_ATTR_CACHE = {}


def __getattr__(name: str):
    """Load functions and classes on-demand when first accessed."""

    # Check cache first
    if name in _ATTR_CACHE:
        return _ATTR_CACHE[name]

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]

        from importlib import import_module

        module = import_module(module_path)
        attr = getattr(module, attr_name)

        # Cache it for future access
        _ATTR_CACHE[name] = attr
        globals()[name] = attr

        return attr

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    """Show all available attributes including lazy ones."""
    regular_attrs = [
        name for name in globals().keys() if not name.startswith("_")
    ]
    lazy_attrs = list(_LAZY_IMPORTS.keys())
    return sorted(set(regular_attrs + lazy_attrs))


__all__ = list(_LAZY_IMPORTS.keys())
