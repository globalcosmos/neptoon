import pytest
import os
from pathlib import Path
from neptoon.data_audit import DataAuditLog


# Setup a fixture for the DataAuditLog instance
@pytest.fixture
def setup_audit_log(tmp_path):
    original_dir = Path.cwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_dir)
    try:
        DataAuditLog.delete_instance()
    except Exception as e:
        print(
            "No DataAuditLog to delete, possibly already "
            f"deleted during test: {e}"
        )


@pytest.mark.test_logging
def test_create_log_file(setup_audit_log):
    DataAuditLog.create()
    assert (
        Path.cwd() / "DataAuditLog.log"
    ).exists(), "Log file was not created"


@pytest.mark.test_logging
def test_log_entry_addition(setup_audit_log):
    log = DataAuditLog.create()
    log.add_step("dummy_function", {"param": "value"})
    with open("DataAuditLog.log", "r") as file:
        contents = file.readlines()
    assert (
        "dummy_function" in contents[-1]
    ), "Log entry was not added correctly"


@pytest.mark.test_logging
def test_instance_deletion(setup_audit_log):
    DataAuditLog.create()
    DataAuditLog.delete_instance()
    assert (
        DataAuditLog.get_instance() is None
    ), "DataAuditLog instance was not deleted properly"


@pytest.mark.test_logging
def test_no_instance_deletion_error(setup_audit_log):
    with pytest.raises(Exception) as exc_info:
        DataAuditLog.delete_instance()
    assert "No instance exists for deletion" in str(
        exc_info.value
    ), "Incorrect handling of no instance deletion"


@pytest.mark.test_logging
def test_log_closure(setup_audit_log):
    log = DataAuditLog.create()
    log.close_log()
    assert all(
        not handler for handler in log.logger.handlers
    ), "Log handlers were not properly closed"
