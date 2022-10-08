import os
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

from system.volumecontrol import VolumeControl
from system.configuration import Config


class VolumeSliderPopup(Popup):
    """
    The class 'VolumeSliderPopup' is a subclass of 'kivy.uix.popup.Popup'.
    It provides methods to open a modal popup with controls for the volume level.
    """
    def __init__(self, **kwargs):
        """
        Initialize self. See help(self) for accurate signature. Call the __init__ function
        of his parent
        :param kwargs:
            screenmanager: the ScreenManager instance of the app
        """
        self.screenmanager = kwargs.get('screenmanager', None)
        self.kv_file_dir = Config.DEFAULT_KV_DIR
        self.slider = ObjectProperty()
        self.mute_btn = ObjectProperty()
        self.volume_control = VolumeControl(screenmanager=self.screenmanager)

        super(VolumeSliderPopup, self).__init__()

        self.init_slider()
        self.init_mute_button()

    def init_slider(self):
        """
        This function initialize the slider to control the volume.
        """
        self.slider.min = 0
        self.slider.max = 100
        self.slider.value = self.volume_control.get_volume()
        self.slider.bind(value=self.on_value)

    def init_mute_button(self):
        """
        This function initialize the mute button. If system is muted, the button icon source is set to
        volume-medium.png, if system is unmuted the icon source is set to volume-mute.png. The on_press
        event of the button is bind to self.on_mute_toggle
        """
        if self.volume_control.is_mute() is True:
            self.mute_btn.source = '{0}/default/48x48/volume-medium.png'.format(self.kv_file_dir)
        else:
            self.mute_btn.source = '{0}/default/48x48/volume-mute.png'.format(self.kv_file_dir)

        self.mute_btn.bind(on_press=self.on_mute_toggle)

    def on_value(self, instance, value):
        """
        The callback function will be called if the slider value changed.
        :param instance: reference to the slider
        :param value: the current value as float
        """
        self.volume_control.set_volume(int(value))

    def on_mute_toggle(self, dt):
        """
        This function is the callback for the mute button and toggle the mute state of the system.
        The mute button icon is set to volume-mute.png if system is unmuted or volume-medium.png if
        system is muted. The volume control button icon source is set to volume-off.png or the previous.
        :param dt: the delta time object which is need to bind the on_press event
        :return: The delta time object
        """
        volume_control_button = self.screenmanager.current_screen.ids.volume_control_button
        if self.volume_control.is_mute() is True:
            self.volume_control.mute()
            self.mute_btn.source = '{0}/default/48x48/volume-medium.png'.format(self.kv_file_dir)
            volume_control_button.source = '{0}/default/48x48/volume-off.png'.format(self.kv_file_dir)
        else:
            self.volume_control.unmute()
            self.mute_btn.source = '{0}/default/48x48/volume-mute.png'.format(self.kv_file_dir)
            volume = self.volume_control.get_volume()
            if 0 <= volume <= 33:
                volume_control_button.source = '{0}/default/48x48/volume-low.png'.format(self.kv_file_dir)
            elif 34 <= volume <= 66:
                volume_control_button.source = '{0}/default/48x48/volume-medium.png'.format(self.kv_file_dir)
            elif 67 <= volume <= 100:
                volume_control_button.source = '{0}/default/48x48/volume-high.png'.format(self.kv_file_dir)

        self.dismiss()

        return dt
