import os
import configparser

from pathlib import Path


class Config:
    """
    The class 'Config' try to load the configuration from one of the following files:
        1. $HOME/.config/jukebox/spotify.ini
        2. $HOME/.spotify.ini
        3. /etc/jukebox/spotify.ini
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

    PY_FILE = os.path.realpath(__file__)
    PY_DIR = os.path.dirname(PY_FILE)
    PY_DIR_PARENT = Path(PY_DIR).parent
    DEFAULT_KV_DIR = PY_DIR_PARENT.joinpath("ui", "kv")
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
            self.set_defaults()
        else:
            self.parser.read(self.config_file)

        if self.parser.getboolean("system", "kivylog") is True:
            os.environ["KIVY_NO_CONSOLELOG"] = "1"
        else:
            os.environ["KIVY_NO_CONSOLELOG"] = "0"

    def print(self):
        """
        This function print the configuration to stdout
        """
        for cfg_key, cfg_value in self.parser.items():
            print("\n{key}".format(key=cfg_key.center(60, "=")))
            for item_key, item_value in cfg_value.items():
                print("{key:<15}: {value}".format(key=item_key, value=item_value))

    def set_defaults(self):
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
            'logLevel': 'debug',  # error, info, debug
            'showcontrols': 'yes',
            'kivylog': 'no',
            'logFile': '/var/log/{app}.log'.format(app=self.DEFAULT_APPNAME)
        }

        self.parser['spotify'] = {
            'enable': 'yes',
            'name': str(self.DEFAULT_APPNAME),
            'bitrate': 320,
            'cache': str(spotify_cache),
            'initialvolume': 75,
            'devicetype': 'avr',
            'normalization': 'no',
            'clientid': '',
            'clientsecret': '',
            'eventgateway': '{cwd}/spotify/spotifyeventgateway.py'.format(cwd=os.getcwd())
        }

        if os.path.isdir(os.path.join(str(Path.home()), ".config", self.DEFAULT_APPNAME)) is False:
            os.mkdir(os.path.join(str(Path.home()), ".config", self.DEFAULT_APPNAME))
        self.config_file = os.path.join(str(Path.home()), self.DEFAULT_CONFIG_FILE)
        with open(self.config_file, "w") as fp_cfg_file:
            self.parser.write(fp_cfg_file)
