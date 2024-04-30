import pytest
from unittest.mock import patch


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
