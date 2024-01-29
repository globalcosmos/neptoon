import os
import logging
from platformdirs import PlatformDirs


class GlobalConfig:
    """Configuration values that are not to be updated by the user.
    Should only be updated by developers when required
    """

    _dirs = PlatformDirs("cosmosbase", "CRNS")

    @staticmethod
    def get_cache_dir():
        return GlobalConfig._dirs.user_cache_dir

    @staticmethod
    def create_cache_dir():
        directory = GlobalConfig.get_cache_dir()
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logging.info(f"Directory created: {directory}")
            except OSError as error:
                logging.error(f"Error creating directory: {error}")
                raise
