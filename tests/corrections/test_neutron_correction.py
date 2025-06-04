import pandas as pd
import pytest
from neptoon.corrections.factory.build_corrections import (
    CorrectionBuilder,
    CorrectNeutrons,
    CorrectionFactory,
    CorrectionTheory,
    CorrectionType,
)
from neptoon.corrections import (
    IncomingIntensityCorrectionZreda2012,
    IncomingIntensityCorrectionHawdon2014,
    HumidityCorrectionRosolem2013,
)
from neptoon.config.configuration_input import SensorInfo
from neptoon.columns.column_information import ColumnInfo
from neptoon.corrections.factory.build_corrections import Correction


### Test Correction class
class WrongCorrection(Correction):
    """This should break"""

    pass


class MockCorrection(Correction):

    def __init__(
        self, correction_type: str, correction_factor_column_name: str
    ):
        super().__init__(correction_type, correction_factor_column_name)

    def apply(self, data_frame=pd.DataFrame):
        data_frame[self.correction_factor_column_name] = 1
        return data_frame


def test_incorrectly_applied_correction():
    """
    Test that abstract class prevents application without apply
    """

    with pytest.raises(TypeError):
        WrongCorrection("test")


def test_get_correction_factor_column_name():
    """
    Test abstract creation
    """

    correction = MockCorrection(
        correction_type="test_type",
        correction_factor_column_name="test_col_name",
    )

    assert correction.correction_type == "test_type"
    assert correction.get_correction_factor_column_name() == "test_col_name"


def test_apply_method():
    """
    Test apply method writes to the correct column
    """
    correction = MockCorrection(
        correction_type="test_type",
        correction_factor_column_name="test_col_name",
    )
    df = pd.DataFrame({"data": [1, 2, 3]})
    result_df = correction.apply(df)

    assert "test_col_name" in str(result_df.columns)


def test_abstract_class_instantiation():
    """
    Test cannot create Correction class directly
    """
    with pytest.raises(TypeError):
        Correction("test_type")


### Test CorrectionBuilder


class MockCorrection2(Correction):
    def __init__(
        self,
        correction_type: str,
        factor: float,
        correction_factor_column_name: str = "empty",
    ):
        super().__init__(correction_type, correction_factor_column_name)
        self.factor = factor

    def apply(self, data_frame: pd.DataFrame):
        data_frame[self.correction_factor_column_name] = self.factor
        return data_frame


def test_add_correction_to_builder():
    """Test adding a correction to the builder."""
    builder = CorrectionBuilder()
    correction = MockCorrection2("test", 1.5)
    builder.add_correction(correction)
    assert "test" in builder.corrections
    assert builder.corrections["test"] == correction


def test_add_invalid_correction():
    builder = CorrectionBuilder()
    builder.add_correction("not_a_correction")
    assert len(builder.corrections) == 0


def remove_correction_by_type():
    builder = CorrectionBuilder()
    correction = MockCorrection2("to_remove", 1.5)
    builder.add_correction(correction)
    assert "to_remove" in builder.corrections
    builder.remove_correction_by_type("to_remove")
    assert "to_remove" not in builder.corrections


def test_get_corrections_stored_in_builder():
    builder = CorrectionBuilder()
    correction1 = MockCorrection2("a_correction", 1.5)
    correction2 = MockCorrection2("another_correction", 2.0)
    builder.add_correction(correction1)
    builder.add_correction(correction2)
    corrections = list(builder.get_corrections())
    assert len(corrections) == 2
    assert correction1 in corrections
    assert correction2 in corrections


### Test CorrectNeutrons


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH): [100, 200, 300],
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW): [100, 200, 300],
        }
    )


@pytest.fixture
def correction_builder():
    builder = CorrectionBuilder()
    builder.add_correction(MockCorrection2("test1", 1.5, "correction_1"))
    builder.add_correction(MockCorrection2("test2", 2.0, "correction_2"))
    return builder


def test_init(sample_df, correction_builder):
    """Test initialization of CorrectNeutrons."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    assert corrector.crns_data_frame.equals(sample_df)
    assert corrector.correction_builder == correction_builder
    assert corrector.correction_columns == []


def test_add_correction_to_corrector(sample_df, correction_builder):
    """Test adding a single correction."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    new_correction = MockCorrection2("test3", 1.2)
    corrector.add_correction(new_correction)
    assert "test3" in corrector.correction_builder.corrections


def test_add_complete_correction_builder(sample_df):
    """Test adding a whole new correction builder."""
    corrector = CorrectNeutrons(sample_df, CorrectionBuilder())
    new_builder = CorrectionBuilder()
    new_builder.add_correction(MockCorrection("new", 1.1))
    corrector.add_correction_builder(new_builder)
    assert corrector.correction_builder == new_builder


def test_create_correction_factors(sample_df, correction_builder):
    """Test creating correction factors."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    result_df = corrector.create_correction_factors(sample_df)
    assert "correction_1" in result_df.columns
    assert "correction_2" in result_df.columns
    assert (result_df["correction_1"] == 1.5).all()
    assert (result_df["correction_2"] == 2.0).all()


def test_create_corrected_neutron_column(sample_df, correction_builder):
    """Test creating the corrected neutron column."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    df_with_factors = corrector.create_correction_factors(sample_df)
    result_df = corrector.create_corrected_neutron_column(df_with_factors)
    assert (
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT) in result_df.columns
    )
    expected = (
        sample_df[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)] * 1.5 * 2.0
    )
    assert (
        result_df[str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)] == expected
    ).all()


def test_correct_neutrons(sample_df, correction_builder):
    """Test the full neutron correction process."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    result_df = corrector.correct_neutrons()
    assert (
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT) in result_df.columns
    )
    expected = (
        sample_df[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)] * 1.5 * 2.0
    )
    assert (
        result_df[str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)] == expected
    ).all()


def test_property_setters(sample_df, correction_builder):
    """Test property setters for crns_data_frame and
    correction_builder."""
    corrector = CorrectNeutrons(sample_df, correction_builder)

    new_df = pd.DataFrame({"new": [1, 2, 3]})
    corrector.crns_data_frame = new_df
    assert corrector.crns_data_frame.equals(new_df)

    new_builder = CorrectionBuilder()
    corrector.correction_builder = new_builder
    assert corrector.correction_builder == new_builder

    with pytest.raises(AttributeError):
        corrector.correction_builder = "not a builder"


@pytest.fixture
def site_information():
    site_information = SensorInfo(
        name="test",
        country="DEU",
        identifier="101",
        install_date=pd.to_datetime("14-01-2011", dayfirst=True),
        latitude=51.37,
        longitude=12.55,
        elevation=140,
        time_zone=1,
        reference_incoming_neutron_value=150,
        avg_dry_soil_bulk_density=1.4,
        avg_lattice_water=0.01,
        avg_soil_organic_carbon=0,
        site_cutoff_rigidity=2.94,
    )
    return site_information


def test_correction_factory_intensity():
    """
    Test correction factory selects the right correction in intensity
    """
    factory = CorrectionFactory()
    tmp_corr = factory.create_correction(
        CorrectionType.INCOMING_INTENSITY, CorrectionTheory.ZREDA_2012
    )

    assert isinstance(
        tmp_corr,
        IncomingIntensityCorrectionZreda2012,
    )
    assert tmp_corr.correction_factor_column_name is str(
        ColumnInfo.Name.INTENSITY_CORRECTION
    )
    assert tmp_corr.correction_type is CorrectionType.INCOMING_INTENSITY

    factory = CorrectionFactory()
    tmp_corr2 = factory.create_correction(
        CorrectionType.INCOMING_INTENSITY, CorrectionTheory.HAWDON_2014
    )
    assert isinstance(
        tmp_corr2,
        IncomingIntensityCorrectionHawdon2014,
    )


@pytest.fixture
def df_with_ref_monitor():
    df_with_ref_monitor = pd.DataFrame(
        {
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE): [
                500,
                500,
                500,
                500,
                500,
            ],
            str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY): [
                4.2,
                4.2,
                4.2,
                4.2,
                4.2,
            ],
            str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY): [
                555,
                546,
                515,
                496,
                500,
            ],
            str(ColumnInfo.Name.REFERENCE_MONITOR_CUTOFF_RIGIDITY): [
                2.4,
                2.4,
                2.4,
                2.4,
                2.4,
            ],
        }
    )
    return df_with_ref_monitor


@pytest.fixture
def df_without_ref_monitor():
    df_without_ref_monitor = pd.DataFrame(
        {
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE): [
                500,
                500,
                500,
                500,
                500,
            ],
            str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY): [
                4.2,
                4.2,
                4.2,
                4.2,
                4.2,
            ],
            str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY): [
                555,
                546,
                515,
                496,
                500,
            ],
        }
    )
    return df_without_ref_monitor


def test_correction_factory_intensity_hawdon(
    df_with_ref_monitor,
    df_without_ref_monitor,
):
    """Test hawdon method when ref given and not given"""

    factory = CorrectionFactory()
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.INCOMING_INTENSITY,
        correction_theory=CorrectionTheory.HAWDON_2014,
    )
    assert tmp_corr.correction_type is CorrectionType.INCOMING_INTENSITY
    assert tmp_corr.correction_factor_column_name is str(
        ColumnInfo.Name.INTENSITY_CORRECTION
    )


@pytest.fixture
def df_lat_and_elevation():
    df_lat_and_elevation = pd.DataFrame(
        {
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE): [
                500,
                500,
                500,
                500,
                500,
            ],
            str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY): [
                4.2,
                4.2,
                4.2,
                4.2,
                4.2,
            ],
            str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY): [
                555,
                546,
                515,
                496,
                500,
            ],
            str(ColumnInfo.Name.LATITUDE): [
                21,
                21,
                21,
                21,
                21,
            ],
            str(ColumnInfo.Name.ELEVATION): [
                600,
                600,
                600,
                600,
                600,
            ],
            str(ColumnInfo.Name.NMDB_REFERENCE_STATION): [
                "JUNG",
                "JUNG",
                "JUNG",
                "JUNG",
                "JUNG",
            ],
        }
    )
    return df_lat_and_elevation


def test_correction_factory_intensity_mcjannet_desilets(
    df_lat_and_elevation,
):
    """Test McJannetDesilets method"""

    factory = CorrectionFactory()
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.INCOMING_INTENSITY,
        correction_theory=CorrectionTheory.MCJANNET_DESILETS_2023,
    )
    assert tmp_corr.correction_type is CorrectionType.INCOMING_INTENSITY
    assert tmp_corr.correction_factor_column_name is str(
        ColumnInfo.Name.INTENSITY_CORRECTION
    )
    df_lat_and_elevation_output = tmp_corr.apply(df_lat_and_elevation)
    assert (
        str(ColumnInfo.Name.INTENSITY_CORRECTION)
        in df_lat_and_elevation_output.columns
    )
    assert (
        str(ColumnInfo.Name.RC_CORRECTION_FACTOR)
        in df_lat_and_elevation_output.columns
    )


def test_correction_factory_intensity_mcjannet_desilets_error(
    df_with_ref_monitor,
):
    """Test McJannetDesilets method error (wrong inputs)"""

    factory = CorrectionFactory()
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.INCOMING_INTENSITY,
        correction_theory=CorrectionTheory.MCJANNET_DESILETS_2023,
    )
    assert tmp_corr.correction_type is CorrectionType.INCOMING_INTENSITY
    assert tmp_corr.correction_factor_column_name is str(
        ColumnInfo.Name.INTENSITY_CORRECTION
    )
    with pytest.raises(ValueError):
        df = tmp_corr.apply(df_with_ref_monitor)
        return df


def test_correction_factory_pressure():
    """
    Test correction factory selects the right correction humidity.
    """
    df = pd.DataFrame(
        {
            str(ColumnInfo.Name.AIR_PRESSURE): [1000, 990, 1010, 1001, 999],
            str(ColumnInfo.Name.MEAN_PRESSURE): [1000, 1000, 1000, 1000, 1000],
            str(ColumnInfo.Name.LATITUDE): [34, 34, 34, 34, 34],
            str(ColumnInfo.Name.ELEVATION): [100, 100, 100, 100, 100],
            str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY): [
                2.3,
                2.3,
                2.3,
                2.3,
                2.3,
            ],
        }
    )

    factory = CorrectionFactory()
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.PRESSURE
    )
    assert tmp_corr.correction_type is CorrectionType.PRESSURE
    assert tmp_corr.correction_factor_column_name is str(
        ColumnInfo.Name.PRESSURE_CORRECTION
    )
    assert str(ColumnInfo.Name.PRESSURE_CORRECTION) not in df.columns
    df = tmp_corr.apply(df)
    assert str(ColumnInfo.Name.PRESSURE_CORRECTION) in df.columns


def test_correction_factory_humidity():
    """
    Test correction factory selects the right correction for humidity

    Parameters
    ----------
    site_information : _type_
        _description_
    """
    df = pd.DataFrame(
        {
            str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY): [67, 70, 78, 76, 55],
            str(ColumnInfo.Name.AIR_TEMPERATURE): [
                21,
                24,
                22,
                21,
                22,
            ],
        }
    )

    factory = CorrectionFactory()
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.HUMIDITY
    )
    assert isinstance(
        tmp_corr,
        HumidityCorrectionRosolem2013,
    )

    df = tmp_corr.apply(df.copy())

    actual_vp_col = str(ColumnInfo.Name.ACTUAL_VAPOUR_PRESSURE)
    sat_vp_col = str(ColumnInfo.Name.SATURATION_VAPOUR_PRESSURE)
    abs_hum_col = str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)
    corr_col = str(ColumnInfo.Name.HUMIDITY_CORRECTION)

    for col in (actual_vp_col, sat_vp_col, abs_hum_col):
        assert col in df.columns, f"Expected column '{col}' in output"

    assert corr_col in df.columns
    for col in (actual_vp_col, sat_vp_col, abs_hum_col, corr_col):
        assert df[col].notna().any(), f"Column '{col}' is all NaNs"
    assert pd.api.types.is_float_dtype(df[corr_col])


def test_humidity_correction_uniform_input_gives_constant_factor():
    """
    If you feed the same (RH, T) in every row, the resulting humidity‐correction
    factor should be identical (i.e. one unique value).
    """
    n = 5
    df = pd.DataFrame(
        {
            str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY): [60] * n,
            str(ColumnInfo.Name.AIR_TEMPERATURE): [22] * n,
        }
    )

    tmp_corr = HumidityCorrectionRosolem2013(
        reference_absolute_humidity_value=0.0
    )
    df_out = tmp_corr.apply(df.copy())

    corr_col = str(ColumnInfo.Name.HUMIDITY_CORRECTION)
    assert df_out[corr_col].nunique() == 1


def test_direct_humidity_correction_with_existing_abs_humidity(monkeypatch):
    """
    If a DataFrame already has 'absolute_humidity', then apply(…) should
    skip recomputing absolute humidity and just run humidity_correction_rosolem2013
    once per row. Monkey patching the internal humidity_correction_rosolem2013
    function will confirm it is called with exactly (abs_hum, reference_val).
    """
    df = pd.DataFrame(
        {
            str(ColumnInfo.Name.ABSOLUTE_HUMIDITY): [5.0, 10.0, 20.0],
            str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY): [0, 0, 0],
            str(ColumnInfo.Name.AIR_TEMPERATURE): [0, 0, 0],
        }
    )

    # Step 2: instantiate with a non‐zero reference, so we can check args:
    reference_val = 3.0
    hc = HumidityCorrectionRosolem2013(
        reference_absolute_humidity_value=reference_val
    )

    calls = []

    def fake_hum_corr(abs_hum, ref_val):
        calls.append((abs_hum, ref_val))
        return abs_hum * 0.1  # return something deterministic

    module_path = hc.__class__.__module__
    monkeypatch.setattr(
        f"{module_path}.humidity_correction_rosolem2013", fake_hum_corr
    )
    df_out = hc.apply(df.copy())

    assert list(df_out[str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)]) == [
        5.0,
        10.0,
        20.0,
    ]

    corr_col = str(ColumnInfo.Name.HUMIDITY_CORRECTION)
    assert corr_col in df_out.columns
    assert calls == [
        (5.0, reference_val),
        (10.0, reference_val),
        (20.0, reference_val),
    ], print(calls)

    expected = [5.0 * 0.1, 10.0 * 0.1, 20.0 * 0.1]
    assert list(df_out[corr_col]) == expected
