#!/usr/bin/env python

import os
from pathlib import Path

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.behaviors import TouchRippleButtonBehavior
from kivy.core.window import Window
from kivy.lang import Builder

from ui.volumesliderpopup import VolumeSliderPopup
from system.volumecontrol import VolumeControl
from system.configuration import Config
from spotify.spotifyconnectserver import SpotifyConnectServer
from spotify.spotifyerror import MQTTConnectionRefused as MQTTConnectionRefusedError
from spotify.spotifyerror import SpotifyApiError


class ImageButton(TouchRippleButtonBehavior, Image):
    """
    The class 'ImageButton' is a subclass of class kivy.uix.image.Image and
    kivy.uix.behaviors.TouchRippleButtonBehavior with associated actions that
    are triggered when the image is pressed (or released after a touch/click
    event). To configure the button, the same properties (source, size, etc.)
    are used as for the class kivy.uix.image.Image
    """
    def on_press(self):
        """
        The callback function for the on_press Event, this function should always bind.
        """
        pass


class BaseScreen(Screen):
    """
    The class 'BaseScreen' is a subclass of class 'kivy.screen'. Screen and
    is the parent class for all sub-screens (control screens, playlist screens etc.)
    used in the application.
    """
    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature. Call the __init__ function
        of his parent
        :param kwargs: empty at the moment
        """
        super(BaseScreen, self).__init__(**kwargs)


class SpotifyScreen(BaseScreen):
    """
    The class 'SpotifyScreen' is a subclass of 'BaseScreen'. It represents a screen that
    displays information like artist, album and title and if its available a cover
    image of the current streamed title over spotify connect protocol. All controls are
    defined and placed in the corresponding kv-file <THEME>/spotify-gui.kv.
    """
    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature. Call the __init__ function
        of his parent
        :param kwargs: empty at the moment
        """
        super(SpotifyScreen, self).__init__(**kwargs)


class JukeBoxKivyApp(App):
    screen_manager = ScreenManager()
    spotify_srv = SpotifyConnectServer()
    kv_file_dir = Config.DEFAULT_KV_DIR
    volume_slider_popup = None
    volume_control = None
    #Window.fullscreen = True

    def __init__(self, **kwargs):
        super(JukeBoxKivyApp, self).__init__()

    def init_volume_control(self):
        """
        Load the kv-file 'volume-control-slider.kv' and instantiate the volume_control and
        volume_slider_popup object.
        """
        Builder.load_file(os.path.join(self.kv_file_dir, "volume-slider-popup.kv"))
        self.volume_slider_popup = VolumeSliderPopup(screenmanager=self.screen_manager)
        self.volume_control = VolumeControl(screenmanager=self.screen_manager)

    def init_volume_control_button(self):
        """
        This function set the volume control button icon source to volume-low.png (0-33),
        volume-medium.png (34-66) or volume-high.png (67-100)
        """
        volume = self.volume_control.get_volume()
        if self.screen_manager is not None and 'volume_control_button' in self.screen_manager.current_screen.ids:
            volume_control_button = self.screen_manager.current_screen.ids.volume_control_button

            if 0 <= volume <= 33:
                volume_control_button.source = '{0}/default/48x48/volume-low.png'.format(self.kv_file_dir)
            elif 34 <= volume <= 66:
                volume_control_button.source = '{0}/default/48x48/volume-medium.png'.format(self.kv_file_dir)
            elif 67 <= volume <= 100:
                volume_control_button.source = '{0}/default/48x48/volume-high.png'.format(self.kv_file_dir)

    def init_spotify_screen(self):
        Builder.load_file(os.path.join(self.kv_file_dir, "spotify_screen.kv"))
        spotify_screen = SpotifyScreen()
        self.screen_manager.add_widget(spotify_screen)

        volume_control_button = self.screen_manager.get_screen('spotify').ids.volume_control_button
        volume_control_button.bind(on_press=self.volume_slider_popup.open)

    def init_spotify_server(self):
        try:
            self.spotify_srv.start()

        except MQTTConnectionRefusedError as err:
            system_message_label = self.screen_manager.get_screen('spotify').ids.system_message_label
            system_message_label.text = "Unable to connect to MQTT broker."
            print("ERR: {err}".format(err=err))

        except SpotifyApiError as err:
            system_message_label = self.screen_manager.get_screen('spotify').ids.system_message_label
            system_message_label.text = "Spotify server not started."
            print("ERR: {err}".format(err=err))

        except Exception as err:
            system_message_label = self.screen_manager.get_screen('spotify').ids.system_message_label
            system_message_label.text = "ERR: {err}".format(err=err)
            print("ERR: {err}".format(err=err))

    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        self.spotify_srv.bind(on_artist_changed=self.on_artist_changed)

        self.init_volume_control()
        self.init_spotify_screen()
        self.init_spotify_server()

        return self.screen_manager

    def on_request_close(self, *args):
        print("{appname} is closing....".format(appname=Config.DEFAULT_APPNAME))
        self.spotify_srv.stop()

    def on_artist_changed(self, *args):
        print("on artist changed: {args}".format(args=args))
