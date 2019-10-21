from enum import Enum
from selectors import EVENT_READ

from mementos import memento_factory

from event_handlers import SocketAcceptorHandler, ChannelHandler
from loggers import EmptyLogger
from reactor import AsyncReactor
from readers import DefaultReader

ArgsMementoMetaclass = memento_factory("ArgsMementoMetaclass", lambda cls, args, kwargs: (cls,) + args)


class ChannelState(Enum):
    IDLE = 0
    READY = 1
    CLOSED = 2


class Channel(object):
    def __init__(self, reader=None, crucial=True, state_notifier=None, reactor=None, logger=None):
        super(Channel, self).__init__()
        self._state_notifier = state_notifier  # handler = handler or ChannelHandler(self)
        self._reactor = reactor or AsyncReactor()
        self._logger = logger or EmptyLogger()
        self._state = ChannelState.IDLE
        self._crucial = crucial
        if reader is not None:
            reader.set_channel(self)
        else:
            reader = DefaultReader(1, self)
        self._reader = reader
        self._buffered = ""

    def read(self, size):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()

    def buffered(self, data):
        self._buffered += data

    def close(self):
        raise NotImplementedError()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state
        if self._state_notifier is not None:
            self._state_notifier(self, new_state)

    @property
    def reader(self):
        return self._reader

    @property
    def key(self):
        raise NotImplementedError()


class FileChannel(Channel, metaclass=ArgsMementoMetaclass):
    def __init__(self, fpath, mode, **kwargs):
        super(FileChannel, self).__init__(**kwargs)
        self._fpath = fpath
        self._mode = mode
        self._fd = None
        self._open_channel()

    def _open_channel(self):
        self._fd = open(self._fpath, self._mode)
        if self._buffered:
            self._fd.write(self._buffered)
        self.state = ChannelState.READY

    def read(self, size):
        return self._fd.read(size)

    def write(self, data):
        self._fd.write(data)
        self._fd.flush()

    def close(self):
        self._fd.close()
        self.state = ChannelState.CLOSED

    @property
    def key(self):
        return self._fd


class SocketChannel(Channel, metaclass=ArgsMementoMetaclass):
    def __init__(self, host, port, **kwargs):
        super(SocketChannel, self).__init__(**kwargs)
        self._host, self._port = host, port
        self._conn = None
        SocketAcceptorHandler(host, port, self._handle_accept, logger=self._logger)

    def _handle_accept(self, conn):
        self._conn = conn
        if self._buffered:
            self._conn.write(self._buffered)
        self.state = ChannelState.READY
        # self._reactor.register(conn, EVENT_READ, self.handler)

    def read(self, size):
        try:
            return self._conn.recv(size)
        except ConnectionResetError:
            return None

    def write(self, data):
        # TODO: consider registering write to the reactor..?
        self._conn.send(data)

    def close(self):
        self._conn.close()
        self.state = ChannelState.CLOSED
        if self._crucial:
            self._reactor.stop()

    @property
    def key(self):
        return self._conn
