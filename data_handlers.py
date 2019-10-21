from construct import Struct
from functools import partial, reduce


class DataHandler(object):
    def __init__(self, channel):
        super(DataHandler, self).__init__()
        self._channel = channel

    def __getattr__(self, item):
        return getattr(self._channel, item)


class DataAggregator(DataHandler):
    def __init__(self, channel, size):
        super(DataAggregator, self).__init__(channel)
        self._size = size
        self._consumable = True
        self._data = ""

    def write(self, data):
        self._data += data
        while len(self._data) >= self._size:
            cur_data = self._data[:self._size]
            self._data = self._data[self._size:]
            self._channel.write(cur_data)
            if not self._consumable:
                break


class DataLogger(DataHandler):
    def __init__(self, channel, fpath):
        super(DataLogger, self).__init__(channel)
        self._fpath = fpath

    def write(self, data):
        open(self._fpath, "ab").write(data)
        self._channel.write(data)


class BaseProtocol(DataHandler):
    def __init__(self, channel, strct):
        super(BaseProtocol, self).__init__(channel)
        self._struct = strct

    def write(self, data):
        self._channel.write(self._struct.build(data))


class REncoder(BaseProtocol):
    PARSER = Struct("REncoder")

    def __init__(self, channel):
        super(REncoder, self).__init__(channel, self.PARSER)


EmptyEncoder = DataHandler


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)
