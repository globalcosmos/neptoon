import pytest
from unittest.mock import patch
from neptoon.columns import ColumnInfo


@pytest.fixture(autouse=True)
def mock_logging(request):
    """
    Turn of logging for tests.
    """
    if "test_logging" in request.keywords:
        yield
    else:
        with patch("logging.Logger") as MockLogger:
            yield MockLogger


@pytest.fixture()
def reset_column_info(autouse=True):
    """
    Automatically resets ColumnInfo labels before runnning test.
    Important for tests related to ColumnInfo renaming.
    """
    ColumnInfo.reset_labels()
    yield
    ColumnInfo.reset_labels()


# Marker for tests that change ColumnInfo
pytest.mark.reset_columns = pytest.mark.usefixtures("reset_column_info")
