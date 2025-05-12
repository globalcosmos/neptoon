from pathlib import Path
import typer

from neptoon.workflow import ProcessWithConfig
from neptoon.config import ConfigurationManager

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(
    processing_config: str = typer.Option(
        None, "--processing", "-p", 
        help="Path to the processing configuration YAML file"
    ),
    sensor_config: str = typer.Option(
        None, "--sensor", "-s", 
        help="Path to the sensor configuration YAML file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", 
        help="Enable verbose output"
    ),
):
    """
    Process CRNS data using configuration files.

    
    Example

    -------
    
    neptoon -p /path/to/process.yaml -s /path/to/sensor.yaml
    """
    if processing_config and sensor_config:
        typer.secho("Processing the sensor data...", fg=typer.colors.GREEN, bold=True)
        process_data(processing_config, sensor_config, verbose)
    elif processing_config or sensor_config:
        typer.echo(typer.style("Error:",fg=typer.colors.RED, bold=True) +" Both processing and station configs are required")
        raise typer.Exit(code=1)
    else:
        typer.echo("Type " + typer.style("neptoon --help", fg=typer.colors.CYAN, bold=True) + " for help.")


def process_data(processing_config: str, sensor_config: str, verbose: bool):
    """
    Process the data using the supplied config file locations.
    """
    processing_config_path = Path(processing_config)
    sensor_config_path = Path(sensor_config)
    
    if not processing_config_path.exists():
        typer.echo(f"Error: Processing configuration file not found: {processing_config_path}")
        raise typer.Exit(code=1)
    
    if not sensor_config_path.exists():
        typer.echo(f"Error: Station configuration file not found: {sensor_config_path}")
        raise typer.Exit(code=1)
    
    config = ConfigurationManager()
    
    try:
        config.load_configuration(file_path=sensor_config_path)
        config.load_configuration(file_path=processing_config_path)
        config_processor = ProcessWithConfig(configuration_object=config)
        config_processor.run_full_process() # Add verbose into run full process later TODO
        if verbose:
            typer.echo("Processing completed successfully.")
    except Exception as e:
        typer.echo(f"Error during processing: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()