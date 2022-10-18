#!/usr/bin/env python3

import os
import sys
import configparser
import paho.mqtt.client as mqtt

from pathlib import Path

jukebox_sys_path = Path(os.path.abspath(os.path.dirname(__file__))).parent
sys.path.insert(0, "{path}".format(path=jukebox_sys_path))
from system.logger import Logger
from system.configuration import Config

"""
The spotifyeventgateway.py is the script that gets run when one of librespot's events is triggered.
It connect to a MQTT broker and publish the events.
MQTT topics:
    spotify/player_event: is published when librespot event PLAYER_EVENT occurred
    spotify/track_id:     is published when librespot publish the spotify track id
"""

name = os.path.basename(__file__)
player_event = os.environ.get('PLAYER_EVENT', None)
track_id = os.environ.get('TRACK_ID', None)
Logger().write(message="Player event: {event}".format(event=player_event), module=name, level=Logger.DEBUG)
Logger().write(message="Track event: {event}".format(event=track_id), module=name, level=Logger.DEBUG)

cfg = Config().parser
host = cfg.get('system', 'mqttHost')
port = cfg.getint('system', 'mqttPort')
keep_alive = cfg.getint('system', 'mqttKeepAlive')

try:
    client = mqtt.Client()
    client.connect(host, port=port, keepalive=keep_alive)
    if track_id is not None:
        client.publish("spotify/track_event", track_id)
    if player_event is not None:
        client.publish("spotify/player_event", player_event)
    client.disconnect()
    Logger().write(message="Message successfully sent to MQTT broker.",
                   module=name,
                   level=Logger.DEBUG)

except ConnectionRefusedError as err:
    Logger().write(message="Failed to connect to MQTT broker: {err}".format(err=err),
                   module=name,
                   level=Logger.ERROR)
