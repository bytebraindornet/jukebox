import subprocess

from system.logger import Logger


class Control:
    """
    The class 'Control' is used to conztrol the operating system.
    """
    def __init__(self):
        """
        Initialize self. See help(self) for accurate signature. Call the __init__ function
        of his parent. A instance of Logger is instantiated.
        """
        self.log = Logger()
        self.mod_name = "system.Control"

    def _do_command_(self, cmd):
        """
        This function execute a command with Pythons subprocess class
        cmd array: the command as array of strings.
        """
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stdout:
            self.log.write(message="{stdout}".format(stdout=stdout),
                           module=self.mod_name,
                           level=Logger.INFO)
        if stderr:
            self.log.write(message="{stderr}".format(stderr=stderr),
                           module=self.mod_name,
                           level=Logger.ERROR)

    def reboot(self):
        """
        This function execute the sudo reboot command.
        """
        cmd = ['sudo', 'reboot']
        self._do_command_(cmd)

    def poweroff(self):
        """
        This function execute the sudo poweroff command.
        """
        cmd = ['sudo', 'poweroff']
        self._do_command_(cmd)

    def restart_mqtt(self):
        """
        This command restart the mosquitto.service systemd service
        """
        cmd = ['sudo', 'systemctl', 'restart', 'mosquitto.service']
        self._do_command_(cmd)
