

class Reader(object):
    def __init__(self, size=1, channel=None):
        super(Reader, self).__init__()
        self._channel = channel
        self._size = size

    def set_channel(self, chan):
        self._channel = chan

    def read(self):
        return self._channel.read(self._size)


DefaultReader = Reader
