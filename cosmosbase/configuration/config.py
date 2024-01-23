import os
import logging
from platformdirs import PlatformDirs


class COSMOSConfig:
    _dirs = PlatformDirs("cosmosbase", "CRNS")

    @staticmethod
    def get_cache_dir():
        return COSMOSConfig._dirs.user_cache_dir

    @staticmethod
    def create_cache_dir():
        directory = COSMOSConfig.get_cache_dir()
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logging.info(f"Directory created: {directory}")
            except OSError as error:
                logging.error(f"Error creating directory: {error}")
                raise
