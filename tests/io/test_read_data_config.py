import pytest
from unittest import mock

from neptoon.io.read.config import _get_config_section
from neptoon.config.configuration_input import ConfigurationManager, BaseConfig


@pytest.fixture
def config_object_simple(monkeypatch):
    configs_dict = {
        "sensor": "sensor",
        "process": "process",
    }
    config = ConfigurationManager()
    config._config = configs_dict
    return config


def test_get_config_section_bad(config_object_simple):
    """
    Raises error when unsupported config is asked for.
    i.e., neither `sensor` or `process`
    """
    with pytest.raises(ValueError):
        tmp_config = config_object_simple
        _ = _get_config_section(tmp_config, wanted_config="name")


def test_get_config_section(monkeypatch):
    """Test config sections is collected"""
    configs_dict = {
        "sensor": "sensor",
        "process": "process",
    }
    config = ConfigurationManager()
    monkeypatch.setattr(config, "_configs", configs_dict)

    config_sensor = _get_config_section(config, wanted_config="sensor")
    config_process = _get_config_section(config, wanted_config="process")
    assert config_process == "process"
    assert config_sensor == "sensor"
