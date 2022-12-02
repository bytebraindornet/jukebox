from datetime import datetime
from system.configuration import Config


class Logger:
    ERROR = 0
    INFO = 1
    DEBUG = 3

    def __init__(self):
        self.cfg = Config().parser
        self._log_file_ = self.cfg.get('system', 'logFile')
        _log_level_ = self.cfg.get('system', 'logLevel')
        if _log_level_ == 'debug':
            self._level_ = self.DEBUG
        elif _log_level_ == 'info':
            self._level_ = self.INFO
        elif _log_level_ == 'error':
            self._level_ = self.ERROR
        else:
            self._level_ = self.ERROR

    def write(self, message=None, module=None, level=0):
        if level == self.ERROR:
            log_level = "ERROR"
        elif level == self.INFO:
            log_level = "INFO"
        elif level == self.DEBUG:
            log_level = "DEBUG"
        else:
            log_level = "{level}".format(level=level)

        if message is not None and module is not None and level <= self._level_:
            with open(self._log_file_, "a") as fp:
                fp.write("{ts} {level} {module} {message}\n".format(ts=datetime.now(),
                                                                    level=log_level,
                                                                    module=module,
                                                                    message=message))
