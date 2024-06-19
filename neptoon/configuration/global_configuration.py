from platformdirs import PlatformDirs
from pathlib import Path


class GlobalConfig:
    """
    Configuration values that are not to be updated by the user.
    Should only be updated by developers when required
    """

    _dirs = PlatformDirs("neptoon", "CRNS")

    @staticmethod
    def get_cache_dir(create_if_missing=True):
        """
        Gets the cache directory on the users computer. Will
        automatically create it if not found by default.

        Parameters
        ----------
        create_if_missing : bool, optional
            Bool, by default True

        Returns
        -------
        Path
            Directory Path for cache files and logs
        """
        directory = Path(GlobalConfig._dirs.user_cache_dir)
        if directory.exists() and create_if_missing:
            GlobalConfig.create_cache_dir()
        return directory

    @staticmethod
    def create_cache_dir():
        """
        Creates the cache directory.
        """
        directory = GlobalConfig.get_cache_dir(create_if_missing=False)
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error making directory: {e}")
            raise
