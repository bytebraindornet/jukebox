# jukebox - a Spotify Connect Client
 
Jukebox is a Spotify client that displays information about the currently playing track or show on a monitor. 
To play the track librespot is used. 

## Install
### required packages 
#### Manjaro / ArchLinux
- mosquitto
- librespot

#### PIP
- pyalsaaudio
- screeninfo
- spotipy
- paho-mqtt
- Kivy
- Pillow

## Configure
The configuration is done by $HOME/.config/jukebox/spotify.conf.
If this file does not exist it will be created with default values.
```
[system]
fullscreen = yes
mqtthost = localhost
mqttport = 1883
mqttkeepalive = 60
loglevel = debug
showcontrols = no
kivylog = no
logfile = /var/log/jukebox.log

[spotify]
name = jukebox
bitrate = 320
cache = /home/jukebox/.cache/jukebox/spotify_cache
initialvolume = 75
devicetype = avr
normalization = no
clientid = Spotify API client ID 
clientsecret = Spotify API client secret
eventgateway = /home/jukebox/app/jukebox/spotify/spotifyeventgateway.py
```