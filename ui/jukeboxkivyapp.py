#!/usr/bin/env python

import os
import glob
import spotipy
import tempfile
import urllib.request

from PIL import Image, ImageFilter
from screeninfo import get_monitors
from spotipy.oauth2 import SpotifyClientCredentials
from kivy.app import App
from kivy.uix.image import Image as KivyImage
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.behaviors import TouchRippleButtonBehavior
from kivy.core.window import Window
from kivy.lang import Builder

from ui.volumesliderpopup import VolumeSliderPopup
from system.volumecontrol import VolumeControl
from system.configuration import Config
from system.logger import Logger
from spotify.spotifyconnectserver import SpotifyConnectServer
from spotify.spotifyerror import MQTTConnectionRefused as MQTTConnectionRefusedError
from spotify.spotifyerror import SpotifyApiError


class ImageButton(TouchRippleButtonBehavior, AsyncImage):
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
    width = 1024
    height = 480
    log = Logger()
    mod_name = os.path.basename(__file__)

    _current_track_id_ = None

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
        Builder.load_file(os.path.join(self.kv_file_dir, "spotify.kv"))
        spotify_screen = SpotifyScreen()
        self.screen_manager.add_widget(spotify_screen)

        volume_control_button = self.screen_manager.get_screen('spotify').ids.volume_control_button
        volume_control_button.bind(on_press=self.volume_slider_popup.open)

    def init_window(self):
        for monitor in get_monitors():
            if monitor.is_primary is True:
                self.width = monitor.width
                self.height = monitor.height

        Window.size = (self.width, self.height)
        Window.borderless = True

    def init_spotify_server(self):
        try:
            self.spotify_srv.start()

        except MQTTConnectionRefusedError as err:
            system_message_label = self.screen_manager.get_screen('spotify').ids.system_message_label
            system_message_label.text = "Unable to connect to MQTT broker."
            self.log.write(message="{err}".format(err=err), module=self.mod_name, level=Logger.ERROR)

        except SpotifyApiError as err:
            system_message_label = self.screen_manager.get_screen('spotify').ids.system_message_label
            system_message_label.text = "Spotify server not started."
            self.log.write(message="{err}".format(err=err), module=self.mod_name, level=Logger.ERROR)

        except Exception as err:
            system_message_label = self.screen_manager.get_screen('spotify').ids.system_message_label
            system_message_label.text = "ERR: {err}".format(err=err)
            self.log.write(message="{err}".format(err=err), module=self.mod_name, level=Logger.ERROR)

    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        Window.bind(on_keyboard=self.on_keyboard)

        self.spotify_srv.bind(on_track_event=self.on_track_event)
        self.spotify_srv.bind(on_player_event=self.on_player_event)

        self.init_window()
        self.init_volume_control()
        self.init_spotify_screen()
        self.init_spotify_server()

        self.set_background_image(None)

        return self.screen_manager

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if modifier == ['ctrl'] and codepoint == 'q':
            self.on_request_close()
            self.stop()

    def on_request_close(self, *args):
        print("{appname} is closing....".format(appname=Config.DEFAULT_APPNAME))
        self.log.write(message="{appname} is closing....".format(appname=Config.DEFAULT_APPNAME),
                       module=self.mod_name,
                       level=Logger.INFO)
        self.spotify_srv.stop()

    def on_track_event(self, *args):
        track_id = args[1]
        if self._current_track_id_ != track_id:
            self._current_track_id_ = track_id
            self.log.write(message="New track id: {trackid}".format(trackid=track_id),
                           module=self.mod_name,
                           level=Logger.INFO)
            _track_ = self.get_track_information(track_id)

            artist = _track_['artist']
            self.log.write(message="New Artist: {artist}".format(artist=artist),
                           module=self.mod_name,
                           level=Logger.INFO)
            artist_names = []
            artist_ids = []
            for item in artist:
                artist_names.append(item.get('name'))
                artist_ids.append(item.get('id'))
            artist_label = self.screen_manager.get_screen('spotify').ids.artist_label
            artist_label.text = " ".join(artist_names)
            artists = self.get_artist_information(artist_ids)
            self.set_background_image(artists[0].get('images'))

            album = _track_['album']
            self.log.write(message="New Album: {album}".format(album=album),
                           module=self.mod_name,
                           level=Logger.INFO)
            album_label = self.screen_manager.get_screen('spotify').ids.album_label
            album_label.text = album['name']

            title = _track_['track']
            title_label = self.screen_manager.get_screen('spotify').ids.title_label
            title_label.text = title

            for img in _track_['image']:
                if img.get('height') == 640: # 640, 300 or 64 possible
                    self.screen_manager.get_screen('spotify').ids.album_art.source = img.get('url')
                    break

        self.log.write("{args}".format(args=args), module=self.mod_name, level=Logger.DEBUG)

    def on_player_event(self, *args):
        self.log.write("{args}".format(args=args), module=self.mod_name, level=Logger.DEBUG)

        event = args[1]
        if event == 'playing':
            btn = self.screen_manager.get_screen('spotify').ids.play_pause_btn
            btn.source = '{0}/default/128x128/pause-circle-outline.png'.format(self.kv_file_dir)
        elif event == 'paused':
            btn = self.screen_manager.get_screen('spotify').ids.play_pause_btn
            btn.source = '{0}/default/128x128/play-circle-outline.png'.format(self.kv_file_dir)

    def get_artist_information(self, spotify_artist_ids):
        if len(spotify_artist_ids) > 0:
            _artist_ = []
            for artist_id in spotify_artist_ids:
                try:
                    _spotify_ = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                        client_id='8217cc054f854c5a8a5c5b0bb7ff55bf',
                        client_secret='d344812b4d874d1aaa60731a6ce567bb'
                    ))
                    _artist_.append(_spotify_.artist(artist_id))

                    return _artist_

                except Exception as error:
                    self.log.write(message="{error}".format(error=error),
                                   module=self.mod_name,
                                   level=Logger.ERROR)
                    raise SpotifyApiError

    def get_track_information(self, spotify_track_id):
        """
        This function get information about the current track by using the trackid and publish
        via MQTT message with topic spotify/track_information.
        """
        self.log.write(message="Track ID: {trackid}".format(trackid=spotify_track_id),
                       module=self.name,
                       level=Logger.DEBUG)
        if spotify_track_id:
            try:
                _spotify_ = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                    client_id='8217cc054f854c5a8a5c5b0bb7ff55bf',
                    client_secret='d344812b4d874d1aaa60731a6ce567bb'
                ))

                _track_ = _spotify_.track('spotify:track:{trackid}'.format(trackid=spotify_track_id))
                track = {
                    'artist': _track_.get('artists', None),
                    'album': _track_.get('album', None),
                    'track': _track_.get('name', spotify_track_id),
                    'image': _track_.get('album', None).get('images', None)
                }
                self.log.write(message="Track information received from Spotify.",
                               module=self.name,
                               level=Logger.INFO)
                self.log.write(message="{track}".format(track=track),
                               module=self.name,
                               level=Logger.DEBUG)
                return track

            except Exception as err:
                self.log.write(message="Unable to get information from Spotify: {err}".format(err=err),
                               module=self.name,
                               level=Logger.ERROR)
                raise SpotifyApiError

    def set_background_image(self, images):
        # delete old tmp background images
        file_list = glob.glob("/tmp/*_{appname}.png".format(appname=Config.DEFAULT_APPNAME))
        for tmp_file in file_list:
            os.remove(tmp_file)

        if images is None:
            print("reset background")
            artist_art = self.screen_manager.get_screen('spotify').ids.artist_art
            artist_art.source = "{0}/default/wallpapers/one_pixel.png".format(self.kv_file_dir)
            return

        image = None
        bg_image = tempfile.mktemp(suffix="_{appname}.png".format(appname=Config.DEFAULT_APPNAME))

        # find the biggest image
        for img in images:
            if image is None or image.get('width') < img.get('width'):
                image = img

        self.log.write(message="Use Artist background image {image}".format(image=image),
                       module=self.mod_name,
                       level=Logger.DEBUG)

        if image is not None:
            # download the image
            try:
                urllib.request.urlretrieve(image.get('url'), bg_image)
            except Exception as err:
                self.log.write(message="{err}".format(err=err))
                return

            # resize and crop
            img = Image.open(bg_image)
            img = img.resize((self.width, self.width), Image.BOX)
            img = img.crop((10, 10, self.width, self.height))
            img.save(bg_image)

            # set the background
            artist_art = self.screen_manager.get_screen('spotify').ids.artist_art
            artist_art.source = bg_image
