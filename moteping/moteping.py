"""moteping.py: Ping application for TinyOS motes."""
from __future__ import print_function

import Queue
import datetime
import threading
import signal
import time
import sys
import os

from moteconnection.connection import Connection
from moteconnection.message import MessageDispatcher, Message, AM_BROADCAST_ADDR

from .packets import PingPacket
from .packets import PongPacket
from .util import print_std, print_red, print_green, configure_colors

import logging
import logging.config
log = logging.getLogger(__name__)


__author__ = "Raido Pahtma"
__license__ = "MIT"


AMID_TOSPINGPONG_PING = 0xFA
AMID_TOSPINGPONG_PONG = 0xFB


def setup_logging(default_path="", default_level=logging.INFO, env_key='LOG_CFG'):
    path = os.getenv(env_key, None)
    if path is None:
        path = default_path

    if len(path) > 0:
        config = None
        if os.path.exists(path):
            if path.endswith("yaml"):
                with open(path, 'rt') as f:
                    import yaml
                    config = yaml.load(f.read())
            elif path.endswith("json"):
                with open(path, 'rt') as f:
                    import json
                    config = json.load(f)

        if config is not None and len(config) > 0:
            logging.config.dictConfig(config)
            print_std("Configured logging with settings from from {}".format(path))
        else:
            raise Exception("Unable to load specified logging configuration file {}".format(path))
    else:
        console = logging.StreamHandler()
        console.setLevel(default_level)
        console.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        logging.getLogger("").addHandler(console)  # add the handler to the root logger


class PingSender(threading.Thread):

    def __init__(self, connection, args):
        super(PingSender, self).__init__()

        self.replies = 0

        self._address = args.address
        self._destination = args.destination
        self._count = args.count
        self._interval = args.interval
        self._pongs = args.pongs
        self._delay = args.delay

        self._ping_size = args.ping_size
        min_size = len(PingPacket().serialize())  # TODO change once serdepa supports size as a class method
        if self._ping_size < min_size:
            self._ping_size = min_size

        self._pong_size = args.pong_size
        min_size = len(PongPacket().serialize())   # TODO change once serdepa supports size as a class method
        if self._pong_size < min_size:
            self._pong_size = min_size

        self._pingnum = 0

        self._ping_start = 0
        self._last_pongs = {}

        self._incoming = Queue.Queue()
        self._dispatcher = MessageDispatcher(args.address, args.group)
        self._dispatcher.register_receiver(AMID_TOSPINGPONG_PONG, self._incoming)

        assert isinstance(connection, Connection)
        self._connection = connection
        self._connection.register_dispatcher(self._dispatcher)

        self._alive = threading.Event()
        self._alive.set()

    def _ts_now(self):
        now = datetime.datetime.utcnow()
        s = now.strftime("%Y-%m-%d %H:%M:%S")
        return s + ".%03uZ" % (now.microsecond / 1000)

    def run(self):
        pingdone = False
        while self._alive.is_set():
            passed = time.time() - self._ping_start
            if not pingdone and passed >= self._interval:
                if self._connection.connected():
                    if self._count == 0 or self._pingnum < self._count:
                        self._pingnum += 1
                        self._ping_start = time.time()
                        self._last_pongs = {}

                        p = PingPacket()
                        p.pingnum = self._pingnum
                        p.pongs = self._pongs
                        p.delay_ms = self._delay
                        p.ping_size = self._ping_size
                        p.pong_size = self._pong_size

                        out = "{} ping {:>2} 0/{} {:04X}->{:04X}[{:02X}] ({:>3}/{:>3}/???)".format(
                            self._ts_now(), self._pingnum, self._pongs,
                            self._address, self._destination, AMID_TOSPINGPONG_PING,
                            self._ping_size, self._pong_size)
                            # TODO pong_size_max should be read from connection

                        print_green(out)

                        try:
                            self._connection.send(Message(AMID_TOSPINGPONG_PING, destination=self._destination,
                                                          payload=p.serialize()))
                        except IOError:
                            print_std("{} send failed".format(self._ts_now()))

                    else:
                        if not pingdone:
                            print_std("{} all pings sent".format(self._ts_now()))
                            pingdone = True
                else:
                    time.sleep(0.1)
            else:
                try:
                    p = self._incoming.get(timeout=0.1)
                    self.receive(p)
                except Queue.Empty:
                    pass

    def join(self, timeout=None):
        self._alive.clear()
        super(PingSender, self).join(timeout)

    def receive(self, packet):
        log.debug("RCV: {}".format(packet))
        try:
            p = PongPacket()
            p.deserialize(packet.payload)

            pformat = "{} pong {:>2} {}/{} {:04X}->{:04X}[{:02X}]"

            if p.pingnum == self._pingnum:
                if packet.source not in self._last_pongs:
                    self._last_pongs[packet.source] = 0

                if p.pong > self._last_pongs[packet.source] + 1:
                    for i in xrange(self._last_pongs[packet.source] + 1, p.pong):
                        pout = pformat.format(self._ts_now(), p.pingnum, i, p.pongs, packet.source, packet.destination, packet.type)
                        out = "{} LOST".format(pout)
                        print_red(out)

                self._last_pongs[packet.source] = p.pong
                delay = p.tx_time_ms - p.rx_time_ms
                rtt = (time.time() - self._ping_start) * 1000 - delay
            else:
                delay = 0
                rtt = 0

            pout = pformat.format(self._ts_now(), p.pingnum, p.pong, p.pongs, packet.source, packet.destination, packet.type)
            out = "{} ({:>3}/{:>3}/{:>3}) time={:>4.0f}ms delay={:>4.0f}ms uptime={:d}s {:s}".format(
                pout,
                p.ping_size, p.pong_size, p.pong_size_max,
                rtt, delay, p.uptime_s, str(p.padding.serialize()).encode("hex").upper())

            if packet.source != self._destination and self._destination != AM_BROADCAST_ADDR:
                log.debug(out)
            else:
                self.replies += 1
                print_std(out)

        except ValueError as e:
            print_red("{} pong {}".format(self._ts_now(), e.message))


def main():

    import argparse
    from argconfparse.argconfparse import arg_hex2int

    parser = argparse.ArgumentParser("MotePing", description="MotePing arguments",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("destination", default=1, type=arg_hex2int, help="Ping destination")

    parser.add_argument("--count", default=0, type=int, help="Ping count, 0 for unlimited")
    parser.add_argument("--interval", default=10.0, type=float, help="Ping interval (seconds, float)")

    parser.add_argument("--timeout", default=0, type=float, help="Ping process timeout (seconds, float)")

    parser.add_argument("--pongs", default=1, type=int, help="Pong count, >= 1")
    parser.add_argument("--delay", default=100, type=int, help="Subsequent pong delay")

    parser.add_argument("--nocolor", default=None, action="store_true", help="Disable colors")

    parser.add_argument("--oneshot", default=False, action="store_true", help="Exit with success after the first pong.")

    parser.add_argument("--ping-size", default=len(PingPacket().serialize()), type=int, help="Ping size >= default")
    parser.add_argument("--pong-size", default=len(PongPacket().serialize()), type=int, help="Pong size >= default")

    parser.add_argument("--connection", default="sf@localhost:9002")
    parser.add_argument("--address", default=0xFFFE, type=arg_hex2int, help="Local address")
    parser.add_argument("--group", default=0x22, type=arg_hex2int, help="Local group")

    # parser.add_argument("--channel", default=None, type=int, help="Radio channel")

    started = time.time()

    args = parser.parse_args()

    configure_colors(args.nocolor)

    setup_logging(default_level=logging.WARNING)

    interrupted = threading.Event()

    def kbi_handler(sig, frm):
        del sig, frm
        interrupted.set()

    signal.signal(signal.SIGINT, kbi_handler)

    con = Connection()
    con.connect(args.connection, reconnect=5.0)

    pinger = PingSender(con, args)
    pinger.start()

    while not interrupted.is_set():
        if args.oneshot and pinger.replies > 0:
            interrupted.set()
        if args.timeout > 0:
            if time.time() - started >= args.timeout or 0 < args.count <= pinger.replies:
                interrupted.set()
        time.sleep(1)

    con.disconnect()
    con.join()

    if pinger.replies > 0:
        return 0

    return 1

if __name__ == '__main__':
    sys.exit(main())
