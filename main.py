from functools import partial

from channels import SocketChannel, FileChannel
from data_handlers import EmptyEncoder, compose, DataAggregator, REncoder, DataHandler, DataLogger
from loggers import PrintLogger, EmptyLogger, FileLogger
from reactor import AsyncReactor, SyncReactor


def connect_interfaces(src, dst, duplex=False, encoder=None, decoder=None):
    encoder = encoder or EmptyEncoder
    src.handler.add_writer(encoder(dst))
    if duplex:
        decoder = decoder or EmptyEncoder
        dst.handler.add_writer(decoder(src))


def interface_a(cfg, logger=None):
    connect_interfaces(SocketChannel("localhost", 1234, logger=logger), SocketChannel("localhost", 5432, logger=logger),
                       duplex=True)

# CONN_TYPES = {
#     "file": FileChannel,
#     "socket": SocketChannel
# }
# src_conn = CONN_TYPES[cfg["src_type"]]


def interface_r(cfg, logger=None):
    connect_interfaces(
        SocketChannel(cfg["src_host"], cfg["src_port"], logger=logger),
        SocketChannel(cfg["dst_host"], cfg["dst_port"], logger=logger),
        encoder=compose(partial(DataAggregator, size=5), REncoder, partial(DataLogger, fpath="r_path")))


def test_read():
    import pdb; pdb.set_trace()


def interface_g(cfg, logger=None):
    connect_interfaces(
        FileChannel("g.bin", "rb", reader=TestReader, logger=logger),
        SocketChannel("localhost", 1234, logger=logger),
        encoder=TestParse)


def main():
    logger = PrintLogger("Test")
    # sync_reactor = SyncReactor(logger=logger)
    async_reactor = AsyncReactor(logger=logger)
    ifs = [
        interface_g({}, logger=logger),
        # InterfaceB(cfg.interface_b, logger=logger),
        # InterfaceC(cfg.interface_c, logger=logger),
    ]
    # SocketChannel("localhost", 1234, logger=logger)
    # connect_interfaces(SocketChannel("localhost", 1234, logger=logger), SocketChannel("localhost", 5432, logger=logger),
    #                    encoder=EmptyEncoder, duplex=True)
    # connect_interfaces(SocketChannel("localhost", 1234, logger=logger), SocketChannel("localhost", 5432, logger=logger),
    #                    encoder=EmptyEncoder)
    # connect_interfaces(SocketChannel("localhost", 1234, logger=logger), FileChannel("test.txt", "wb", logger=logger), encoder=None)
    # ProxyServer(SocketChannel("localhost", 1234), FileChannel("blabla.txt"), encoder=None)
    # ProxyServer(SocketChannel("localhost", 5432), FileChannel("blabla2.txt"), encoder=None)

    # sync_reactor.start()
    async_reactor.start()


if __name__ == "__main__":
    main()
    # TODO: consider caching entries? (file entries, socket entries)


###########################################################################################
# Trash!
###########################################################################################

# def fixed_socket_handler(read_size, **kwargs):
#     return partial(SocketHandler, read_size=read_size, **kwargs)


# class FileHandler(EventHandler):
#     def __init__(self, fpath, mode, **kwargs):
#         super(FileHandler, self).__init__(**kwargs)
#         self._fd = open(fpath, mode)
#         self._reactor.register(self._fd, self, EVENT_READ if "r" in mode else EVENT_WRITE)
#
#     def close(self):
#         self._fd.close()


# class FileReadHandler(FileHandler):
#     def __init__(self, fpath, **kwargs):
#         super(FileReadHandler, self).__init__(fpath, "rb", **kwargs)
#
#     def handle(self):
#         data = self._fd.read(10)
#         if self._fd.tell() == os.path.getsize(self._fd.name):
#             self._reactor.unregister(self._fd)
#             self.close()
