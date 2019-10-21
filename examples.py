

def interface_a(cfg, logger=None):
    connect_interfaces(SocketChannel("localhost", 1234, logger=logger), SocketChannel("localhost", 5432, logger=logger), duplex=True)


class TEncoder(DataHandler):
    def write(self, data):
        parse data
        self._channel.write(whatever)

def interface_t(cfg, logger=None):
    connect_interfaces(SocketChannel("localhost", 1234, logger=logger), SocketChannel("localhost", 1234, logger=logger), encoder=Aggragator(REncoder(Base)))

def interface_g(cfg, logger=None):
    connect_interfaces(FileChannel("g.bin", logger=logger), SocketChannel("localhost", 1234, logger=logger), encoder=GDataHandler)
