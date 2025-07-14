import pytest
from unittest import mock

from neptoon.io.read.config import _get_config_section
from neptoon.config.configuration_input import ConfigurationManager, BaseConfig


@pytest.fixture
def good_config_object(monkeypatch):
    configs_dict = {
        "sensor": "sensor",
        "process": "process",
    }
    # allow creating the class attribute
    monkeypatch.setattr(
        ConfigurationManager,
        "_configs",
        configs_dict,
        raising=False,
    )
    return ConfigurationManager()


# def test_get_config_section(good_config_object):
#     tmp_config = good_config_object
#     config_sensor = _get_config_section(tmp_config, wanted_config="sensor")
#     config_process = _get_config_section(tmp_config, wanted_config="process")
#     assert config_process == "process"
#     assert config_sensor == "sensor"


def test_get_config_section_bad(good_config_object):
    """
    Raises error when unsupported config is asked for.
    i.e., neither `sensor` or `process`
    """
    with pytest.raises(ValueError):
        tmp_config = good_config_object
        _ = _get_config_section(tmp_config, wanted_config="name")
