class MQTTConnectionRefused(Exception):
    def __init__(self, message="MQTTConnectionRefused: unable to connect to MQTT server."):
        self.message = message
        super().__init__(self.message)


class SpotifyApiError(Exception):
    def __init__(self, message="SpotifyApiError: somthing is wrong."):
        self.message = message
        super().__init__(self.message)
