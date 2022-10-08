import alsaaudio

from kivy.event import EventDispatcher
from system.configuration import Config


class VolumeControl(EventDispatcher):
    """
    This class provides methods to control the volume via operating system
    mechanisms. It also provides a method to determine the current volume.
    """

    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature.
        :param kwargs:
            screenmanager: the Screenmanager instance of the app
        """
        self.kv_file_dir = Config.DEFAULT_KV_DIR
        self.screen_manager = kwargs.get('screenmanager', None)
        self.register_event_type('on_volume_changed')
        self.mixer = alsaaudio.Mixer(alsaaudio.mixers()[0])
        self.current_volume_level = self.get_volume()

        super(VolumeControl, self).__init__()

    def set_volume(self, volume):
        """
        This function set the volume to the given value and dispatch the event
        on_volume_changed.
        :param volume: Integer between 0 and 100
        """
        self.mixer.setvolume(int(volume), alsaaudio.MIXER_CHANNEL_ALL)
        self.current_volume_level = volume
        self.dispatch('on_volume_changed', self.get_volume())

    def get_volume(self):
        """
        This function returns the current volume
        :return: Integer tuple between 0 and 100
        """
        return self.mixer.getvolume()[0]

    def volume_up(self, step=1):
        """
        This function increase the volume by the given value
        :param step: Integer between 0 and 100
        """
        new_volume = self.get_volume() + step
        self.set_volume(new_volume)

    def volume_down(self, step=1):
        """
        This function lowers the volume by the given value
        :param step: Integer between 0 and 100
        :return:
        """
        new_volume = self.get_volume() - step
        self.set_volume(new_volume)

    def on_volume_changed(self, *args):
        """
        This function is the callback for the custom event
        'bytebrainmultiroom.system.volumecontrol.on_volume_changed'. Depending on the volume
        level, the volume control button source is set to volume-low.png (0-33), volume-medium.png (34-66)
        or volume-high.png (67-100)
        :param args: the current volume level as  tuple integer
        """
        volume = args[0]
        if self.screen_manager is not None:
            volume_control_button = self.screen_manager.current_screen.ids.volume_control_button
            if 0 <= volume <= 33:
                volume_control_button.source = '{0}/default/48x48/volume-low.png'.format(self.kv_file_dir)
            elif 34 <= volume <= 66:
                volume_control_button.source = '{0}/default/48x48/volume-medium.png'.format(self.kv_file_dir)
            elif 67 <= volume <= 100:
                volume_control_button.source = '{0}/default/48x48/volume-high.png'.format(self.kv_file_dir)

    def is_mute(self):
        """
        This function get the mute state and return it.
        :return: True if system is muted otherwise False
        """
        return True if self.mixer.getmute()[0] == 0 else False

    def mute(self):
        """
        This function mute the system sound
        """
        self.mixer.setmute(1)

    def unmute(self):
        """
        This function unmute the system sound
        """
        self.mixer.setmute(0)
