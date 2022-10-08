import subprocess
import spotipy
import paho.mqtt.client as mqtt

from spotipy.oauth2 import SpotifyClientCredentials
from kivy.event import EventDispatcher
from system.configuration import Config
from spotify.spotifyerror import MQTTConnectionRefused as MQTTConnectionRefusedError
from spotify.spotifyerror import SpotifyApiError


class SpotifyConnectServer(EventDispatcher):
    """
    The class 'SpotifyObserver' updates the interface of the SpotifyGui screen. To access the elements of
    the screen, the dictionary 'ids' of the MpdGui screen must be specified during instantiation.
    """

    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature.
        """
        self.cfg = Config().parser
        self.repeat = False
        self.random = False
        self._event_ = None
        self._process_ = None
        self._spotify_ = None
        self._mqtt_client_ = None
        self.spotify_track_id = ""
        self.running = False

        try:
            self._spotify_ = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
                client_id='8217cc054f854c5a8a5c5b0bb7ff55bf',
                client_secret='d344812b4d874d1aaa60731a6ce567bb'
            ))
        except Exception as err:
            print("unable to instantiate spotipy: {}".format(err))

        self.register_event_type('on_track_changed')
        super(SpotifyConnectServer, self).__init__(**kwargs)

    def start(self):
        """
        This function start librespot and a MQTT client which is listen to the configured
        broker for inter process communication.
        """
        spotify_bitrate = self.cfg.getint('spotify', 'bitrate')
        spotify_name = self.cfg.get('spotify', 'name')
        spotify_cache = self.cfg.get('spotify', 'cache')
        spotify_initial_volume = self.cfg.get('spotify', 'initialvolume')
        spotify_device_type = self.cfg.get('spotify', 'devicetype')
        spotify_event_gateway = self.cfg.get('spotify', 'eventGateway')
        volume_normalization = self.cfg.getboolean('spotify', 'normalization')

        _mqtt_is_running_ = False
        _librespot_is_running_ = False

        cmd = ['/usr/bin/librespot',
               '-n \'{name}\''.format(name=spotify_name),
               '-b', str(spotify_bitrate),
               '-c', spotify_cache,
               '--initial-volume', str(spotify_initial_volume),
               '--device-type', spotify_device_type,
               '--onevent', spotify_event_gateway]

        if volume_normalization is True:
            cmd.append('--enable-volume-normalisation')
        self._process_ = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _librespot_is_running_ = self._process_.poll() is None

        try:
            self._mqtt_client_ = mqtt.Client()
            self._mqtt_client_.on_connect = self.on_connect
            self._mqtt_client_.on_message = self.on_message
            self._mqtt_client_.connect(self.cfg.get('system', 'mqttHost'), port=self.cfg.getint('system', 'mqttPort'))
            self._mqtt_client_.loop_start()
            _mqtt_is_running_ = True

        except ConnectionRefusedError as err:
            self._process_.kill()
            raise MQTTConnectionRefusedError

        self.running = _mqtt_is_running_ and _librespot_is_running_

    def stop(self):
        """
        This function call the cancel() function of self._event_ (instance of class 'kivy.clock.Clock'
        to unschedule the calling of self.observer() and set the value of self.running to False.
        """
        self._process_.kill()
        self._mqtt_client_.loop_stop()
        self.running = False

    def restart(self):
        """
        This function restart the librespot daemon and MQTT client. The functions stop() and start()
        is using for.
        :return:
        """
        self.stop()
        self.start()

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        """
        This function is called by mqtt client if receives a CONACK.
        :param client: the mqtt client as instance of paho.mqtt.client.Client()
        :param userdata: the private user data as set in Client() or user_data_set()
        :param flags: response flags sent by the broker
        :param rc: the result code,
            0: Connection successful
            1: Connection refused - incorrect protocol version
            2: Connection refused - invalid client identifier
            3: Connection refused - server unavailable
            4: Connection refused - bad username or password
            5: Connection refused - not authorised
            6-255: Currently unused.
        """
        if rc == 0:
            client.subscribe("spotify/#")

    def on_message(self, client, userdata, msg):
        """
        Called when a message has been received on a topic that the client subscribes to and the
        message does not match an existing topic filter callback.
        :param client: the mqtt client as instance of paho.mqtt.client.Client()
        :param userdata: the private user data as set in Client() or user_data_set()
        :param msg: an instance of MQTTMessage. This is a class with members topic, payload, qos, retain.
        """
        if msg.topic == "spotify/track_id":
            self.get_information(msg.payload.decode("utf-8"))

        else:
            print("Message topic: {topic}".format(topic=msg.topic))

    def get_information(self, spotify_track_id):
        """
        This function get information about the current track by using the trackid and publish
        via MQTT message with topic spotify/track_information.
        """
        try:
            _track_ = self._spotify_.track('spotify:track:{trackid}'.format(trackid=spotify_track_id))

            track = {
                'artist': _track_.get('artists', None),
                'album': _track_.get('album', None),
                'track': _track_.get('name', self.spotify_track_id),
                'image': _track_.get('album', None).get('images', None)
            }
            print(track)

            return track

        except Exception as err:
            print("Error occurred: {err}".format(err=err))
            raise SpotifyApiError

    def on_track_changed(self, *args):
        print("I'm dispatched", args)
