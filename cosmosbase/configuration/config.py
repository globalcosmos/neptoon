from platformdirs import PlatformDirs
import os


class COSMOSConfig:
    _dirs = PlatformDirs("cosmosbase", "CRNS")

    @staticmethod
    def get_cache_dir():
        return COSMOSConfig._dirs.user_cache_dir

    @staticmethod
    def check_and_create_cache():
        directory = COSMOSConfig.get_cache_dir()
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Directory created: {directory}")
            except OSError as error:
                print(f"Error creating directory: {error}")
        else:
            pass
