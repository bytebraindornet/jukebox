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
| Parameter     | Description                                                                                                                                                                                                               |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| fullscreen    | start the application in full screen, yes and no possible                                                                                                                                                                 |
| mgtthost      | IP address or hostname of the MQTT broker                                                                                                                                                                                 |
| mqttport      | The port on which the MQTT broker listen                                                                                                                                                                                  |
| mqttkeepalive | Maximum period in seconds between communications with the broker.                                                                                                                                                         |
| loglevel      | The level of detail of messages in the log file                                                                                                                                                                           |
| showcontrols  | If it is set to yes the keyboard shortcut are displayed on the home screen.                                                                                                                                               |
| kivylog       | If it set to yes, the kivy console log is activate                                                                                                                                                                        |
| logfile       | The path to the application logfile                                                                                                                                                                                       |
| name          | The name that appears in Spotify when you try to connect to the device                                                                                                                                                    |
| bitrate       | The bitrate (kbps, 96, 120, 320 possible.                                                                                                                                                                                 |
| cache         | Path to a directory where files will be cached.                                                                                                                                                                           |
| initialvolume | Initial volume in % from 0-100.                                                                                                                                                                                           |
| devicetype    | Displayed device type: computer, tablet, smartphone, speaker, tv, avr (Audio/Video Receiver), stb (Set-Top Box), audiodongle, gameconsole, castaudio, castvideo, automobile, smartwatch, chromebook, carthing, homething. |
| normalization | Enables volume normalisation for librespot                                                                                                                                                                                |
| clientid      | The Spotify API client ID                                                                                                                                                                                                 |
| clientsecret  | The Spotify API client secret                                                                                                                                                                                             |
| eventgateway  | The path to a script that gets run when one of librespot's events is triggered.                                                                                                                                           |
