import os
import configparser
import subprocess

from pathlib import Path


class Config:
    """
    The class 'Config' try to load the configuration from one of the following files:
        1. $HOME/.config/bytebrain/gui.ini
        2. $HOME/.bytebrain.ini
        3. /etc/bytebrain/gui.ini
    The first file which is found being used. All the following are ignored. The
    user-specific settings / config files have priority.
    To get access to the configuration, the member parser must be used. This is an instance
    of configparser.ConfigParser.
    """

    DEFAULT_APPNAME = "jukebox"
    """The name of the application"""

    DEFAULT_CFG_NAME = "spotify.cfg"

    DEFAULT_CONFIG_FILE = os.path.join(".config", DEFAULT_APPNAME, DEFAULT_CFG_NAME)
    """ The preferred location of the configuration file """

    DEFAULT_KV_DIR = (Path.cwd().absolute()).joinpath("ui", "kv")
    """ The default location for kv, icons and images used ba user interface. """

    def __init__(self):
        """
        Initialize self. See help(self) for accurate signature.
        Test if one of the config files exists and set the path of them to self.config_path.
        In case that no file exist, set the value of self.config_file to None, set the mandatory
        parameters default values and write it to $HOME/.config/jukebox/gui.ini.
        """

        if os.path.isfile(os.path.join(str(Path.home()), self.DEFAULT_CONFIG_FILE)):
            self.config_file = os.path.join(str(Path.home()), self.DEFAULT_CONFIG_FILE)
        elif os.path.isfile(os.path.join(str(Path.home()), ".{appname}.ini".format(appname=self.DEFAULT_APPNAME))):
            self.config_file = os.path.join(str(Path.home()), ".{appname}.ini".format(appname=self.DEFAULT_APPNAME))
        elif os.path.isfile(os.path.join("etc", self.DEFAULT_APPNAME, self.DEFAULT_CFG_NAME)):
            os.path.join("etc", self.DEFAULT_APPNAME, "gui.ini")
        else:
            self.config_file = None

        self.parser = configparser.ConfigParser()

        # Load defaults if no configuration is found
        if self.config_file is None:
            # create default configuration if no config file can be found and set
            # all mandatory parameters

            home = Path.home()

            spotify_cache = Path('.cache/{appname}/spotify_cache'.format(appname=self.DEFAULT_APPNAME))
            spotify_cache = home.joinpath(spotify_cache)
            spotify_cache.mkdir(parents=True, exist_ok=True)

            self.parser['system'] = {
                'fullscreen': 'yes',
                'mqttHost': 'localhost',
                'mqttPort': 1883,
                'mqttKeepAlive': 60,
                'logLevel': 'debug'     # error, info, debug
            }

            self.parser['spotify'] = {
                'enable': 'yes',
                'name': str(self.DEFAULT_APPNAME),
                'bitrate': 320,
                'cache': str(spotify_cache),
                'initialvolume': 75,
                'devicetype': 'avr',
                'normalization': 'no',
                'eventgateway': '{cwd}/spotify/spotifyeventgateway.py'.format(cwd=os.getcwd())
            }

            if os.path.isdir(os.path.join(str(Path.home()), ".config", self.DEFAULT_APPNAME)) is False:
                os.mkdir(os.path.join(str(Path.home()), ".config", self.DEFAULT_APPNAME))
            self.config_file = os.path.join(str(Path.home()), self.DEFAULT_CONFIG_FILE)
            with open(self.config_file, "w") as fp_cfg_file:
                self.parser.write(fp_cfg_file)
        else:
            self.parser.read(self.config_file)

    def print_config(self):
        """
        This function print the configuration to stdout
        """
        for cfg_key, cfg_value in self.parser.items():
            print("\n{key}".format(key=cfg_key.center(60, "=")))
            for item_key, item_value in cfg_value.items():
                print("{key:<15}: {value}".format(key=item_key, value=item_value))