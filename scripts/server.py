import sys, os, argparse
import asyncio
import itertools as it
# for a reason as to why imports of siblings is so ugly
# see https://mail.python.org/pipermail/python-3000/2007-April/006793.html
sys.path.insert(0, os.path.abspath('..'))
import machineio

try:
    import signal
except ImportError:
    signal = None


class MioServer(asyncio.Protocol):

    keys = {}
    clients = {}
    controller = {}
    awaiting_handshake = []

    def __init__(self):
        self.transport = None
        self.crypto = None

    def connection_made(self, transport):
        print('=====================')
        print('Client has connected.')
        self.transport = transport
        self.crypto = machineio.network.Crypto()
        self.send = lambda ty, fo, to, pl: self.transport.write(
            machineio.network.pack(
                self.keys[to].encrypt(
                    machineio.network.assemble(ty, fo, to, pl))))

        MioServer.awaiting_handshake.append(self)

    def connection_lost(self, exc):
        print('---------------------')
        for name in it.chain(MioServer.clients, MioServer.controller):
            if name in MioServer.clients and MioServer.clients[name] is self:
                del MioServer.keys[name]
                del MioServer.clients[name]
                try:
                    MioServer.controller[name].send('notice', 'server', f'controller~{name}',
                                                    {'reason': 'link_failure', 'info': name})
                except KeyError:
                    print('Client had no connected controller.')
                print(f'Client "{name}" was properly removed.')
                break
            elif name in MioServer.controller and MioServer.controller[name] is self:
                del MioServer.keys[name]
                del MioServer.controller[name]
                if len(MioServer.controller) == 0:
                    for client in MioServer.clients:
                        MioServer.clients[client].send('notice', 'server', client, {'reason': 'halt'})
                else:
                    for ctrl in MioServer.controller:
                        MioServer.controller[ctrl].send('notice', 'server', ctrl,
                                                        {'reason': 'controller_link_failure', 'info': name})
                print(f'Client Controller "{name}" was properly removed.')
                break
        else:
            print('Client was not properly removed.')

    def data_received(self, data):
        # print('RAW DATA', data)
        socket_data = machineio.network.unpack(data)
        # print('SOCKET DATA', socket_data)
        for data in socket_data:
            self.process_data(data)

    def process_data(self, data):
        if self in MioServer.awaiting_handshake:
            MioServer.awaiting_handshake.remove(self)
            data = self.crypto.handshake_server(data)
            data_type, from_name, to_name, payload = machineio.network.parse(data)
            if data_type == 'add':
                if from_name == 'controller':
                    from_name = f'controller~{payload}'
                    MioServer.controller[from_name] = self
                    MioServer.keys[from_name] = self.crypto
                    print(f'Client "{from_name}" is verified as controller.')
                    MioServer.clients[payload].transport.write(machineio.network.pack(MioServer.keys[payload].encrypt(
                        machineio.network.assemble('notice', 'server', payload, {'reason': 'reset'})
                    )))
                    print(f'Client "{payload}" was reset.')
                elif from_name in MioServer.clients or from_name == 'server':
                    raise NameError('Client with this name already exists')
                else:
                    MioServer.clients[from_name] = self
                    MioServer.keys[from_name] = self.crypto
                    print(f'Client "{from_name}" is now verified.')
        elif data == b'OK':
            self.transport.write(machineio.network.pack(b'OK'))
        else:
            data = self.crypto.decrypt(data)
            data_type, from_name, to_name, payload = machineio.network.parse(data)
            # print(f'Data Type: {data_type}, From:{from_name} To:{to_name} Payload:{payload}')
            if to_name == 'controller':
                MioServer.controller[f'controller~{from_name}'].transport.write(machineio.network.pack(
                    MioServer.keys[f'controller~{from_name}'].encrypt(data)))
            elif to_name == 'server':
                pass
            else:
                data = MioServer.keys[to_name].encrypt(data)
                MioServer.clients[to_name].transport.write(machineio.network.pack(data))

    def eof_received(self):
        pass


def start_server(loop, host, port):
    f = loop.create_server(MioServer, host, port)
    return loop.run_until_complete(f)

ARGS = argparse.ArgumentParser(description='Machine IO network server.')
ARGS.add_argument(
    '-host', action='store', dest='host',
    default = '127.0.0.1', help='Host name')
ARGS.add_argument(
    '-port', action='store', dest='port',
    default=20801, type=int, help='Port number')
ARGS.add_argument(
    '-iocp', action='store_true', dest='iocp',
    default=False, help='Use IOCP event loop')


if __name__ == '__main__':
    args = ARGS.parse_args()

    if ':' in args.host:
        args.host, port = args.host.split(':', 1)
        args.port = int(port)

    if args.iocp:
        from asyncio import windows_events
        loop = windows_events.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    print(f'Using backend: {loop.__class__.__name__}')

    if signal is not None and sys.platform != 'win32':
        loop.add_signal_handler(signal.SIGINT, loop.stop)

    server = start_server(loop, args.host, args.port)

    print(f'Starting Machine IO server on {args.host} port {args.port}')

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
