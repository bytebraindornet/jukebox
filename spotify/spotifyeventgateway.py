#!/usr/bin/env python3

import os
import configparser
import paho.mqtt.client as mqtt
from pathlib import Path

"""
The spotifyeventgateway.py is the script that gets run when one of librespot's events is triggered.
It connect to a MQTT broker and publish the events.
MQTT topics:
    spotify/player_event: is published when librespot event PLAYER_EVENT occurred
    spotify/track_id:     is published when librespot publish the spotify track id
"""


def read_config():
    """
    This function read the host, port and keep alive parameters from one of the following
    files to connect to the MQTT broker
        1. $HOME/.config/bytebrain/gui.ini
        2. $HOME/.bytebrain.ini
        3. /etc/bytebrain/gui.ini
    The first file which is found been used.
    """
    default_config_file = os.path.join(".config", "bytebrain", "gui.ini")
    config_file = None

    if os.path.isfile(os.path.join(str(Path.home()), default_config_file)):
        config_file = os.path.join(str(Path.home()), default_config_file)
    elif os.path.isfile(os.path.join(str(Path.home()), ".bytebrain.ini")):
        config_file = os.path.join(str(Path.home()), ".bytebrain.ini")
    elif os.path.isfile(os.path.join("etc", "bytebrain", "gui.ini")):
        os.path.join("etc", "bytebrain", "gui.ini")

    if config_file is not None:
        cfg_parser = configparser.ConfigParser()
        cfg_parser.read(config_file)
        mqtt_host = cfg_parser.get('system', 'mqttHost')
        mqtt_port = cfg_parser.getint('system', 'mqttPort')
        mqtt_keep_alive = cfg_parser.getint('system', 'mqttKeepAlive')
    else:
        mqtt_host = 'localhost'
        mqtt_port = 1883
        mqtt_keep_alive = 60

    return {
        'mqtt_host': mqtt_host,
        'mqtt_port': mqtt_port,
        'mqtt_keep_alive': mqtt_keep_alive
    }


player_event = os.environ.get('PLAYER_EVENT', None)
track_id = os.environ.get('TRACK_ID', None)

print(track_id, player_event)

cfg = read_config()
host = cfg['mqtt_host']
port = cfg['mqtt_port']
keep_alive = cfg['mqtt_keep_alive']

client = mqtt.Client()
client.connect(host, port=port, keepalive=keep_alive)
client.publish("spotify/player_event", player_event)
client.publish("spotify/track_id", track_id)
client.disconnect()
