import pandas as pd
import pytest
from neptoon.corrections.factory.neutron_correction import (
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
from neptoon.config.site_information import SiteInformation
from neptoon.columns.column_information import ColumnInfo
from neptoon.corrections.factory.neutron_correction import Correction


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
    site_information = SiteInformation(
        site_name="test",
        latitude=51.37,
        longitude=12.55,
        elevation=140,
        reference_incoming_neutron_value=150,
        dry_soil_bulk_density=1.4,
        lattice_water=0.01,
        soil_organic_carbon=0,
        site_cutoff_rigidity=2.94,
    )
    return site_information


def test_correction_factory_intensity(site_information):
    """
    Test correction factory selects the right correction in intensity
    """
    factory = CorrectionFactory(site_information=site_information)
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

    factory = CorrectionFactory(site_information=site_information)
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
    site_information,
    df_with_ref_monitor,
    df_without_ref_monitor,
):
    """Test hawdon method when ref given and not given"""

    factory = CorrectionFactory(site_information=site_information)
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.INCOMING_INTENSITY,
        correction_theory=CorrectionTheory.HAWDON_2014,
    )
    assert tmp_corr.correction_type is CorrectionType.INCOMING_INTENSITY
    assert tmp_corr.correction_factor_column_name is str(
        ColumnInfo.Name.INTENSITY_CORRECTION
    )
    df_with_ref_monitor_output = tmp_corr.apply(df_with_ref_monitor)
    df_without_ref_monitor_output = tmp_corr.apply(df_without_ref_monitor)
    with pytest.raises(AssertionError):
        pd.testing.assert_frame_equal(
            df_with_ref_monitor_output, df_without_ref_monitor_output
        )
    tmp_corr._check_if_ref_monitor_supplied


def test_check_if_ref_monitor_supplied(
    site_information,
    df_with_ref_monitor,
    df_without_ref_monitor,
):
    factory = CorrectionFactory(site_information=site_information)
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.INCOMING_INTENSITY,
        correction_theory=CorrectionTheory.HAWDON_2014,
    )
    tmp_corr._check_if_ref_monitor_supplied(df_without_ref_monitor)
    assert tmp_corr.ref_monitor_missing
    tmp_corr._check_if_ref_monitor_supplied(df_with_ref_monitor)
    with pytest.raises(AssertionError):
        assert tmp_corr.ref_monitor_missing


def test_correction_factory_pressure(site_information):
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

    factory = CorrectionFactory(site_information=site_information)
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


def test_correction_factory_humidity(site_information):
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

    factory = CorrectionFactory(site_information=site_information)
    tmp_corr = factory.create_correction(
        correction_type=CorrectionType.HUMIDITY
    )
    assert isinstance(
        tmp_corr,
        HumidityCorrectionRosolem2013,
    )

    df = tmp_corr.apply(df)

    assert str(ColumnInfo.Name.ACTUAL_VAPOUR_PRESSURE) in df.columns
    assert str(ColumnInfo.Name.ABSOLUTE_HUMIDITY) in df.columns
    assert str(ColumnInfo.Name.SATURATION_VAPOUR_PRESSURE) in df.columns
