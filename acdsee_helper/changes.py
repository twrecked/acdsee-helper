import threading

from watchdog.events import PatternMatchingEventHandler


files_ = set()
files_lock_ = threading.Lock()


class AnyFileHandler(PatternMatchingEventHandler):
    def __init__(self, config):
        super().__init__()
        self._config = config

    def is_match(self, event):
        return True

    def on_modified(self, event):
        if self.is_match(event):
            with files_lock_:
                global files_
                files_.add(event.src_path)

    def on_closed(self, event):
        if self.is_match(event):
            with files_lock_:
                global files_
                files_.add(event.src_path)


class ExifFileHandler(AnyFileHandler):
    def __init__(self, config):
        super().__init__(config)

    def is_match(self, event):
        return self._config.is_data_file(event.src_path)

