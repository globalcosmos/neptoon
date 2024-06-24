import pandas as pd
import pytest
from neptoon.neutron_correction.neutron_correction import (
    Correction,
    CorrectionBuilder,
    CorrectNeutrons,
)


### Test Correction class
class WrongCorrection(Correction):
    """This should break"""

    pass


class MockCorrection(Correction):

    def apply(self, data_frame=pd.DataFrame):
        data_frame[self.correction_factor_column_name] = 1
        return data_frame


def test_incorrectly_applied_correction():
    """
    Test that abstract class prevents application without apply
    """

    with pytest.raises(TypeError):
        test = WrongCorrection("test")


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
        super().__init__(correction_type)
        self.factor = factor
        self.correction_factor_column_name = correction_factor_column_name

    def apply(self, data_frame: pd.DataFrame):
        data_frame[self.correction_factor_column_name] = self.factor
        return data_frame


def test_add_correction():
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
        {"epithermal_neutrons": [100, 200, 300], "other_data": [1, 2, 3]}
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


def test_add_correction(sample_df, correction_builder):
    """Test adding a single correction."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    new_correction = MockCorrection2("test3", 1.2)
    corrector.add_correction(new_correction)
    assert "test3" in corrector.correction_builder.corrections


def test_add_correction_builder(sample_df):
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
    assert "corrected_epithermal_neutron_count" in result_df.columns
    expected = sample_df["epithermal_neutrons"] * 1.5 * 2.0
    assert (result_df["corrected_epithermal_neutron_count"] == expected).all()


def test_correct_neutrons(sample_df, correction_builder):
    """Test the full neutron correction process."""
    corrector = CorrectNeutrons(sample_df, correction_builder)
    result_df = corrector.correct_neutrons()
    assert "corrected_epithermal_neutron_count" in result_df.columns
    expected = sample_df["epithermal_neutrons"] * 1.5 * 2.0
    assert (result_df["corrected_epithermal_neutron_count"] == expected).all()


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
