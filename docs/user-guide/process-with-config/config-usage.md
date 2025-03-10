
## How to import the YAML file

Once you have your config files you need to import them with the `ConfigurationManager`. We recommend to use pathlib.Paths as its more stable, especially if there's a change you'll swap operating systems. 


### Complete script

You can use this code block as a starting point for your own, make sure to change the paths to your configs. It's usually better to use absolute paths if you know where your data is.

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

## How to run

At this stage we will presume some things:

- You have installed neptoon on your machine in it's own virtual environment called `neptoon` ([more info](/user-guide/installation/))
- You have created your configuration files for processing and sensor, called `process_crns_1.yaml` and `sensor_1.yaml`
- You have created a `.py` file using the above template, called `run_my_sensor_1.py` and it's inside a folder `/home/crns_data/`

The final stage is to open up terminal/powershell, change into the folder with your .py file, activate your envrionment and run it. After this you will have your data processed.

```bash
cd /home/crns_data/
mamba activate neptoon
python3 run_my_sensor.py
```
