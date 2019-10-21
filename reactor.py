from selectors import SelectSelector
from threading import Thread

from loggers import EmptyLogger


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Important note: the select that we are using does not support files on windows
#   https://repolinux.wordpress.com/2012/10/09/non-blocking-read-from-stdin-in-python/
class BaseReactor(Thread):
    def __init__(self, *args, logger=None, **kwargs):
        super(BaseReactor, self).__init__()
        self._should_run = True
        self._logger = logger or EmptyLogger()

        self._selector = SelectSelector()
        self.register = self._selector.register
        self._logger.info("Initiating %s" % (type(self).__name__,))

    # def register(self, fileobj, events, data=None):
    #     self._selector.register(fileobj, events, data=data)

    def unregister(self, fileobj):
        self._selector.unregister(fileobj)
        if not self._selector.get_map():
            self.stop()

    def stop(self):
        self._should_run = False

    def run(self):
        while self._should_run:
            self._reactor_loop()
        self._logger.info("Bye Bye")
        self._close()

    def _reactor_loop(self):
        raise NotImplementedError()

    def _close(self):
        # Should not activate this function from outside - use stop instead
        mapping = self._selector.get_map()
        self._selector.close()
        for file_obj, key in mapping.items():
            event_obj = key.data
            event_obj.close()


class AsyncReactor(BaseReactor, metaclass=Singleton):
    def _reactor_loop(self):
        if not self._selector.get_map():
            return
        events = self._selector.select()
        for key, mask in events:
            event_obj = key.data
            event_obj.handle(mask)


class SyncReactor(BaseReactor, metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        super(SyncReactor, self).__init__(*args, **kwargs)
        # TODO: define locks

    def _reactor_loop(self):
        pass
