"""packets.py: MotePing packets."""
from serdepa import SerdepaPacket, List, nx_uint8, nx_uint32

__author__ = "Raido Pahtma"
__license__ = "MIT"


class PingPacket(SerdepaPacket):
    TOSPINGPONG_PING = 0x00
    # typedef nx_struct {
    # 	nx_uint8_t header;
    # 	nx_uint32_t pingnum;
    # 	nx_uint32_t pongs;
    # 	nx_uint32_t delay_ms;
    # 	nx_uint8_t ping_size; // How much was sent in PING
    # 	nx_uint8_t pong_size; // How much should be sent in PONG
    # 	nx_uint8_t padding[]; // 01 02 03 04 ...
    # } TosPingPongPing_t;
    _fields_ = [
        ("header", nx_uint8),
        ("pingnum", nx_uint32),
        ("pongs", nx_uint32),
        ("delay_ms", nx_uint32),
        ("ping_size", nx_uint8),
        ("pong_size", nx_uint8),
        ("padding", List(nx_uint8))
    ]

    def __init__(self, **kwargs):
        super(PingPacket, self).__init__(**kwargs)
        self.header = self.TOSPINGPONG_PING
        self.pingnum = 0
        self.pongs = 0
        self.delay_ms = 0
        self.ping_size = 0
        self.pong_size = 0


class PongPacket(SerdepaPacket):
    TOSPINGPONG_PONG = 0x01
    # typedef nx_struct {
    #     nx_uint8_t header;
    #     nx_uint32_t pingnum;
    #     nx_uint32_t pongs;
    #     nx_uint32_t pong;
    #     nx_uint8_t ping_size; // How much was actually received in PING
    #     nx_uint8_t pong_size; // How much was sent in PONG
    #     nx_uint8_t pong_size_max;
    #     nx_uint32_t rx_time_ms;
    #     nx_uint32_t tx_time_ms;
    #     nx_uint32_t uptime_s;
    #     nx_uint8_t padding[]; // 01 02 03 04 ...
    # } TosPingPongPong_t;
    _fields_ = [
        ("header", nx_uint8),
        ("pingnum", nx_uint32),
        ("pongs", nx_uint32),
        ("pong", nx_uint32),
        ("ping_size", nx_uint8),
        ("pong_size", nx_uint8),
        ("pong_size_max", nx_uint8),
        ("rx_time_ms", nx_uint32),
        ("tx_time_ms", nx_uint32),
        ("uptime_s", nx_uint32),
        ("padding", List(nx_uint8))
    ]

    def __init__(self, **kwargs):
        super(PongPacket, self).__init__(**kwargs)
        self.pingnum = 0
        self.pongs = 0
        self.pong = 0
        self.ping_size = 0
        self.pong_size = 0
        self.pong_size_max = 0
        self.rx_time_ms = 0
        self.tx_time_ms = 0
        self.uptime_s = 0

    def __str__(self):
        return "%u %u/%u %u/%u/%u %u>>%u %u %s" % (self.pingnum, self.pong, self.pongs,
                                                   self.ping_size, self.pong_size, self.pong_size_max,
                                                   self.rx_time_ms, self.tx_time_ms, self.uptime_s,
                                                   self.padding.serialize().encode("hex").upper())
