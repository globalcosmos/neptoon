from platformdirs import PlatformDirs
import os

class AppConfig:
    _dirs = PlatformDirs("cosmos-base", "CRNS")

    @staticmethod
    def get_cache_dir():
        return AppConfig._dirs.user_cache_dir
    
    @staticmethod
    def check_and_create_cache():
        directory = AppConfig.get_cache_dir()
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Directory created: {directory}")
            except OSError as error:
                print(f"Error creating directory: {error}")
        else:
            pass
