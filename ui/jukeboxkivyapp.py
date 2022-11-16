#!/usr/bin/env python

import os
import glob
import spotipy
import tempfile
import urllib.request

from PIL import Image
from screeninfo import get_monitors
from spotipy.oauth2 import SpotifyClientCredentials
from kivy.app import App
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.screenmanager import FadeTransition
from kivy.uix.behaviors import TouchRippleButtonBehavior
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.clock import Clock

from ui.volumesliderpopup import VolumeSliderPopup
from system.volumecontrol import VolumeControl
from system.configuration import Config
from system.control import Control as SystemControl
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


class FullAsyncImage(AsyncImage):
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
    image of the current streamed title over spotify connect protocol. All element are
    defined and placed in the corresponding kv-file spotify.kv.
    """

    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature. Call the __init__ function
        of his parent
        :param kwargs: empty at the moment
        """
        super(SpotifyScreen, self).__init__(**kwargs)


class BlankScreen(BaseScreen):
    """
    The class 'BlankScreen' is a subclass of 'BaseScreen'. It represents a blank screen
    when no Spotify client is connected. All element are defined and placed in the
    corresponding kv-file blank.kv.
    """
    def __init__(self, **kwargs):
        super(BlankScreen, self).__init__(**kwargs)


class JukeBoxKivyApp(App):
    """
    The class 'JukeBoxKivyApp' is a subclass of 'kivy.app.App'. It is the main entry to the
    application and contains the kivy run loop.
    """
    screen_manager = ScreenManager()
    spotify_srv = SpotifyConnectServer()
    kv_file_dir = Config.DEFAULT_KV_DIR
    volume_slider_popup = None
    volume_control = None
    width = 1024
    height = 480
    log = Logger()
    mod_name = os.path.basename(__file__)
    client_id = '8217cc054f854c5a8a5c5b0bb7ff55bf'
    client_secret = 'd344812b4d874d1aaa60731a6ce567bb'
    current_screen = 'blank'

    _track_playing_event_ = None
    _current_track_id_ = None

    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature. Call the __init__ function
        of his parent. The global configuration is printed on stdout.
        param kwargs: empty at the moment
        """
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
        """
        Load the kv-file for the spotify and his settings screen. Bind the controls to
        his corresponding functions.
        :return:
        """
        Builder.load_file(os.path.join(self.kv_file_dir, "spotify.kv"))
        spotify_screen = SpotifyScreen()
        self.screen_manager.add_widget(spotify_screen)

        volume_control_button = self.screen_manager.get_screen('spotify').ids.volume_control_button
        volume_control_button.bind(on_press=self.volume_slider_popup.open)

    def init_blank_screen(self):
        """
        Load the kv-file for the blank screen.
        :return:
        """
        Builder.load_file(os.path.join(self.kv_file_dir, "blank.kv"))
        blank_screen = BlankScreen()
        self.screen_manager.add_widget(blank_screen)

    def init_window(self):
        """
        find the current monitor size and set this as application size. The application
        window is set to a borderless window.
        """
        for monitor in get_monitors():
            if monitor.is_primary is True:
                self.width = monitor.width
                self.height = monitor.height

        Window.size = (self.width, self.height)
        Window.borderless = True
        Window.show_cursor = False

    def init_spotify_server(self):
        """
        The spotify connect client librespot and the MQTT client is start.
        """
        try:
            self.spotify_srv.start()

        except MQTTConnectionRefusedError as err:
            system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
            system_message_label.text = "Unable to connect to MQTT broker."
            self.log.write(message="{err}".format(err=err), module=self.mod_name, level=Logger.ERROR)

        except SpotifyApiError as err:
            system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
            system_message_label.text = "Spotify server not started."
            self.log.write(message="{err}".format(err=err), module=self.mod_name, level=Logger.ERROR)

        except Exception as err:
            system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
            system_message_label.text = "ERR: {err}".format(err=err)
            self.log.write(message="{err}".format(err=err), module=self.mod_name, level=Logger.ERROR)

    def build(self):
        """
        Initializes the application; it will be called only once. If this method returns a widget (tree), it will be
        used as the root widget and added to the window.
        :return: ScreenManager Instance as the root widget of the application
        """
        Window.bind(on_request_close=self.on_request_close)
        Window.bind(on_keyboard=self.on_keyboard)

        self.spotify_srv.bind(on_track_event=self.on_track_event)
        self.spotify_srv.bind(on_player_event=self.on_player_event)

        self.init_window()
        self.init_blank_screen()
        self.init_volume_control()
        self.init_spotify_screen()
        self.init_spotify_server()

        self.set_background_image(None)
        self.screen_manager.transition = FadeTransition()
        self.screen_manager.current = 'blank'

        return self.screen_manager

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        """
        This function is called when a key on the keyboard is pressed.
        """
        if modifier == ['ctrl']:
            if codepoint == 'q':
                self.on_request_close()
                self.stop()

            elif codepoint == 's':
                self.log.write(message="restart librespot ....",
                               module=self.mod_name,
                               level=Logger.INFO)
                system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
                system_message_label.text = "Restart Spotify client"
                self.spotify_srv.stop()
                self.init_spotify_server()

            elif codepoint == 'r':
                self.log.write(message="reboot the system ...",
                               module=self.mod_name,
                               level=Logger.INFO)
                system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
                system_message_label.text = "Reboot the System"
                SystemControl().reboot()

            elif codepoint == 'p':
                self.log.write(message="power off the system ...",
                               module=self.mod_name,
                               level=Logger.INFO)
                system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
                system_message_label.text = "Power off the System"
                SystemControl().poweroff()

            elif codepoint == 'm':
                self.log.write(message="restart the MQTT broker ...",
                               module=self.mod_name,
                               level=Logger.INFO)
                system_message_label = self.screen_manager.get_screen(self.current_screen).ids.system_message_label
                system_message_label.text = "Restart the MQTT broker"
                SystemControl().restart_mqtt()

    def on_request_close(self, *args):
        """
        This function stop the spotify connect client and the MQTT listener.
        """
        self.log.write(message="{appname} is closing....".format(appname=Config.DEFAULT_APPNAME),
                       module=self.mod_name,
                       level=Logger.INFO)
        self.spotify_srv.stop()

    def on_track_event(self, *args):
        """
        This function is called when a 'track_event' event is received. If the
        track_id is uneven to the last played track_id, the functions to get information
        from Spotify API called. The result of this function sis used to display artist,
        album, track, artist image and album image.
        """
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
                if img.get('height') == 640:  # 640, 300 or 64 possible
                    self.screen_manager.get_screen('spotify').ids.album_art.source = img.get('url')
                    break

        self.log.write("{args}".format(args=args), module=self.mod_name, level=Logger.DEBUG)

    def on_player_event(self, *args):
        """
        This function is called when a 'track_event' event is received. If the event is
        'started' the spotify screen is shown. If the event is stopped, the blank screen
        is shown.
        """
        self.log.write("{args}".format(args=args), module=self.mod_name, level=Logger.DEBUG)

        event = args[1]
        if event == 'started':
            Clock.schedule_once(self.set_spotify_screen)
        elif event == 'stopped':
            Clock.schedule_once(self.set_blank_screen)
        else:
            print("player event: {ev}".format(ev=event))

    def get_artist_information(self, spotify_artist_ids):
        """
        This funktion get the information about currently played artist from Spotify API.
        param spotify_artist_ids:, a Spotify track ID
        :return: Array of all artists.
        """
        if len(spotify_artist_ids) > 0:
            _artist_ = []
            for artist_id in spotify_artist_ids:
                try:
                    _spotify_ = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                        client_id=self.client_id,
                        client_secret=self.client_secret
                    ))
                    _artist_.append(_spotify_.artist(artist_id))
                    return _artist_

                except Exception as error:
                    self.log.write(message="{error}".format(error=error),
                                   module=self.mod_name,
                                   level=Logger.ERROR)
                    raise SpotifyApiError

    def get_audio_features(self, spotify_track_id):
        """
        This function get the audio features of the currently played track from Spotify API.
        param spotify_track_id: a Spotify track ID
        :return: Array with audio features
        """
        if spotify_track_id:
            try:
                _spotify_ = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                ))
                _audio_features_ = _spotify_.audio_features(spotify_track_id)
                self.log.write(message="{0}".format(_audio_features_),
                               module=self.mod_name,
                               level=Logger.DEBUG)
                return _audio_features_
            except Exception as err:
                self.log.write("Unable to get audio features from Spotify: {err}".format(err=err))
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
                    client_id=self.client_id,
                    client_secret=self.client_secret
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
        """
        This function change the background image. The biggest image is downloadet and modified
        to fit the application size.
        param images: an array of images. Each image is a dict get from Spotify API
        """
        file_list = glob.glob("/tmp/*_{appname}.png".format(appname=Config.DEFAULT_APPNAME))
        for tmp_file in file_list:
            os.remove(tmp_file)

        if images is None:
            artist_art = self.screen_manager.get_screen('spotify').ids.artist_art
            artist_art.source = "{0}/default/wallpapers/one_pixel.png".format(self.kv_file_dir)
            return

        bg_image = tempfile.mktemp(suffix="_{appname}.png".format(appname=Config.DEFAULT_APPNAME))

        image = None
        for img in images:
            if image is None or image.get('width') < img.get('width'):
                image = img

        self.log.write(message="Use Artist background image {image}".format(image=image),
                       module=self.mod_name,
                       level=Logger.DEBUG)

        if image is not None:
            try:
                urllib.request.urlretrieve(image.get('url'), bg_image)
            except Exception as err:
                self.log.write(message="{err}".format(err=err))
                return

            img = Image.open(bg_image)
            img = img.resize((self.width, self.width), Image.BOX)
            img = img.crop((0, 0, self.width, self.height))
            img.save(bg_image)

            artist_art = self.screen_manager.get_screen('spotify').ids.artist_art
            artist_art.source = bg_image

    def set_spotify_screen(self, dt):
        """
        This function set the current screen to the spotify screen.
        """
        self.current_screen = 'spotify'
        self.screen_manager.current = self.current_screen

    def set_blank_screen(self, dt):
        """
        This function set the current screen to the blank screen.
        """
        self.current_screen = 'blank'
        self.screen_manager.current = self.current_screen
