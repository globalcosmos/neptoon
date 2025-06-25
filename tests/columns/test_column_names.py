from neptoon.columns.column_information import ColumnInfo
import pytest


@pytest.fixture(autouse=True)
def reset_column_info():
    """
    This function will be called before every test function here.
    Since the test functions will change the original Class,
    it is necessary to set the class labels back to default after the tests.
    """
    # Reset the labels (probably not necessary)
    # ColumnInfo.reset_labels()
    # Run the test function
    yield
    # Reset labels again to the default class
    ColumnInfo.reset_labels()


def test_import_and_use_strings():
    """
    Test that the way we import in code pulls the string correctly
    """
    test_val1 = str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)
    test_val2 = str(ColumnInfo.Name.SOIL_MOISTURE_VOL)
    assert isinstance(test_val1, str)
    assert isinstance(test_val2, str)


def test_change_column_name_in_pipeline():
    """
    Test relabeling works as expected
    """
    test_val1 = str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)
    assert isinstance(test_val1, str)
    ColumnInfo.relabel(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT, "new_name")
    assert str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT) == "new_name"


def test_reset_names():
    """
    Test resetting the labels to default
    """
    initial_value = str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)
    ColumnInfo.relabel(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT, "new_name")
    changed_value = str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)
    ColumnInfo.reset_labels()
    reset_value = str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT)

    assert changed_value == "new_name"
    assert reset_value != "new_name"
    assert reset_value == initial_value
