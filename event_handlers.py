import socket
from selectors import EVENT_READ
from threading import Lock

from channels import ChannelState
from loggers import EmptyLogger
from reactor import AsyncReactor


class EventHandler(object):
    def __init__(self, reactor_cls=None, logger=None):
        reactor_cls = reactor_cls or AsyncReactor
        self._reactor = reactor_cls()
        self._logger = logger or EmptyLogger()

    def handle(self, mask):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class SocketAcceptorHandler(EventHandler):
    def __init__(self, host, port, handle_socket, num_connections=1, **kwargs):
        super(SocketAcceptorHandler, self).__init__(**kwargs)
        self._handle_socket = handle_socket
        self._num_conns = num_connections
        self._init_socket(host, port)
        self._reactor.register(self._sock, EVENT_READ, self)

    def _init_socket(self, host, port):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((host, port))
        self._sock.listen()

    def handle(self, mask):
        conn, addr = self._sock.accept()
        self._logger.info('Connection accepted from: %s' % (addr,))
        conn.setblocking(False)
        self._handle_socket(conn)

        self._num_conns -= 1
        if self._num_conns <= 0:
            # don't need to accept any more connections
            self._reactor.unregister(self._sock)
            self.close()

    def close(self):
        self._sock.close()


class ChannelHandler(EventHandler):
    def __init__(self, channel, **kwargs):
        super(ChannelHandler, self).__init__(**kwargs)
        self._channel = channel
        self._channel.handler = self
        self._lock = Lock()
        self._writers = []

    def add_writer(self, writer):
        with self._lock:
            self._writers.append(writer)

    def _notify_data(self, data):
        writers = self._writers[:]
        for writer in writers:
            if writer.state == ChannelState.IDLE:
                writer.buffered(data)
            elif writer.state == ChannelState.READY:
                writer.write(data)
            elif writer.state == ChannelState.CLOSED:
                with self._lock:
                    self._writers.remove(writer)

    def _handle_read(self):
        data = self._channel.reader.read()
        if data is None:
            self._reactor.unregister(self._channel.key)
            self.close()
            return
        self._notify_data(data)

    def handle(self, mask):
        if mask & EVENT_READ:
            self._handle_read()

    def close(self):
        self._channel.close()
