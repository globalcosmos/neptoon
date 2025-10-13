## Why Docker?

Docker provides a containerised environment for running neptoon, which offers:

- **No environment setup**: Skip Python installation and dependency management entirely
- **Stability**: Your processing workflows won't break when you update other software on your system
- **Reproducibility**: Run the exact same neptoon version across different machines or operating systems
- **Server deployment**: Easily run automated processing jobs on remote servers or in cloud environments
- **Quick updates**: Pull new neptoon versions without reinstalling dependencies

## Running with Docker

### Install Docker

There are a few ways to get docker running on your machine. The simplest solution is [docker desktop](https://docs.docker.com/desktop/). Alternative install solutions can be searched for online. 

### Prepare your configs

The Docker CLI still requires you to set up your config files. Set them up as shown in the documentation as normal. 

### Create your docker command

The docker command should be run from your terminal/powershell. As long as you have installed docker correctly, and it is currently running, it will automatically download the docker image and run it.

Here is an example of a working docker command:

```bash
docker run --rm \
    -v ./configs/process_configs/v1_processing_method.yaml:/workingdir/processconfig.yaml:ro \
    -v ./configs/sensor_configs/sensor_1.yaml:/workingdir/sensorconfig.yaml \
    -v ./data/unprocessed_data/sensor_1.zip/:/workingdir/inputs \
    -v ./data/processed_data/:/workingdir/outputs \
    -v ./data/calibration_data/:/workingdir/calibration \
    registry.hzdr.de/cosmos/neptoon/neptoon-cli:v0.13.6
```
The trailing `\` on each line is needed to make multi line commands.

Lets break down how to make this command:

#### docker run --rm

This is the main command to run the docker container. The --rm flag tells docker to close down the image once it has finished running, this prevents your computer/server having hanging images clogging up memory. 

#### Volume Mounts

Each `-v` line mounts a file or folder from your computer into the Docker container. The format is:

```
-v /your/local/path:/workingdir/container_path
```

!!! warning 
    **Do not change the paths after the `:` - these are fixed locations inside the Docker container.**

| Mount Point (in container) | What to Mount | Required | Notes |
|----------------------------|---------------|----------|-------|
| `/workingdir/processconfig.yaml` | Your processing configuration file | Yes | The `:ro` flag makes it read-only |
| `/workingdir/sensorconfig.yaml` | Your sensor configuration file | Yes |  |
| `/workingdir/inputs` | Folder containing your raw data or zip file | Yes | Can be a folder or a `.zip` archive |
| `/workingdir/outputs` | Folder where processed data will be saved | Yes | |
| `/workingdir/calibration` | Folder containing calibration data | Only if calibrating | Can be omitted if not calibrating |

**Example with your actual paths:**

```bash
docker run --rm \
    -v /home/user/configs/v1_processing.yaml:/workingdir/processconfig.yaml:ro \
    -v /home/user/configs/sensor_A101.yaml:/workingdir/sensorconfig.yaml \
    -v /home/user/data/raw/sensor_data.zip:/workingdir/inputs \
    -v /home/user/data/processed:/workingdir/outputs \
    -v /home/user/data/calibration:/workingdir/calibration \
    registry.hzdr.de/cosmos/neptoon/neptoon-cli:v0.13.6
```

#### Docker registry

The final line tells docker which image to use. If you don't have the image on your computer already it will automatically download them. Right now we save each docker container into the gitlab repository container registry. In the above case we are downloading neptoon docker image with neptoon v0.13.6

Fixing a specific neptoon version will make processing more stable and reproduceable, each processing uses **exactly** the same version of neptoon (down to it's dependencies and operating system).

It is also possible to select to always use the latest with `registry.hzdr.de/cosmos/neptoon/neptoon-cli:latest`, however be aware that changes might impact processing. 

You can see what versions are available [here](https://codebase.helmholtz.cloud/cosmos/neptoon/container_registry/23572).

