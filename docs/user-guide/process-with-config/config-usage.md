
## Processing from the command line

You can process data from the command line using your config files. Firstly make sure you have installed neptoon using `pipx`. This means you will have access to the CLI commands in your terminal. See [here](installation.md#cli-installation-guide) for more on installation steps.

To run:

```bash
neptoon -p /path/to/process.yaml -s /path/to/sensor.yaml
```

## Processing in your Python IDE

You need to import the configuration files with the `ConfigurationManager`. 


### Complete script

You can use this code block as a starting point for your own, make sure to change the paths to your configs. It's usually better to use absolute paths if you know where your data is.

=== "Using path strings"
    ```python
    from pathlib import Path
    from neptoon.workflow.process_with_yaml import (
        ProcessWithYaml,
    )
    from neptoon.config import ConfigurationManager

    # Instantiate a ConfigurationManager to handle config files
    config = ConfigurationManager()

    # Create paths to, and load, the configuration files.
    sensor_config_path = Path("home/path/to/configuration_files/A101_station.yaml")
    processing_config_path = Path("home/path/to/configuration_files/v1_processing_method.yaml")

    # Load the configs
    config.load_configuration(
        file_path=sensor_config_path,
    )
    config.load_configuration(
        file_path=processing_config_path,
    )

    # Add config manager to the ProcessWithYaml class ready for processing.
    yaml_processor = ProcessWithYaml(configuration_object=config)

    # Run
    yaml_processor.run_full_process()
    ```
=== "Using pathlib.Path"
    ```python
    from pathlib import Path
    from neptoon.workflow.process_with_yaml import (
        ProcessWithYaml,
    )
    from neptoon.config import ConfigurationManager

    # Instantiate a ConfigurationManager to handle config files
    config = ConfigurationManager()

    # Create paths to, and load, the configuration files.
    sensor_config_path = Path.cwd().parent / "configuration_files" / "A101_station.yaml"
    processing_config_path = (
        Path.cwd().parent / "configuration_files" / "v1_processing_method.yaml"
    )

    # Load the configs
    config.load_configuration(
        file_path=sensor_config_path,
    )
    config.load_configuration(
        file_path=processing_config_path,
    )

    # Add config manager to the ProcessWithYaml class ready for processing.
    yaml_processor = ProcessWithYaml(configuration_object=config)

    # Run
    yaml_processor.run_full_process()
    ```

