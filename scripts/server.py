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
        MioServer.awaiting_handshake.append(self)

    def connection_lost(self, exc):
        for name in it.chain(MioServer.clients, MioServer.controller):
            if name in MioServer.clients and MioServer.clients[name] is self:
                del MioServer.keys[name]
                del MioServer.clients[name]
                MioServer.controller[name].transport.write(
                    machineio.network.mionet_assembler('notice', 'server', f'controller~{name}', 'linkfailure'))
                print(f'Client "{name}" was properly removed.')
                break
            elif name in MioServer.controller and MioServer.controller[name] is self:
                del MioServer.keys[name]
                del MioServer.controller[name]
                print(f'Client Controller "{name}" was properly removed.')
                break
        else:
            print('Client was not properly removed.')

    def data_received(self, data):
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
                elif from_name in MioServer.clients or from_name == 'server':
                    raise NameError('Client with this name already exists')
                else:
                    MioServer.clients[from_name] = self
                    MioServer.keys[from_name] = self.crypto
                    print(f'Client "{from_name}" is now verified.')
        else:
            data = self.crypto.decrypt(data)
            data_type, from_name, to_name, payload = machineio.network.parse(data)
            if to_name == 'controller':
                MioServer.controller[f'controller~{from_name}'].transport.write(
                    MioServer.keys[f'controller~{from_name}'].encrypt(data))
            elif to_name == 'server':
                pass
            else:
                data = MioServer.keys[to_name].encrypt(data)
                MioServer.clients[to_name].transport.write(data)

    def eof_received(self):
        pass


def start_server(loop, host, port):
    f = loop.create_server(MioServer, host, port)
    return loop.run_until_complete(f)

ARGS = argparse.ArgumentParser(description='Machine IO network server.')
ARGS.add_argument(
    '--host', action='store', dest='host',
    default = '127.0.0.1', help='Host name')
ARGS.add_argument(
    '--port', action='store', dest='port',
    default=20801, type=int, help='Port number')
ARGS.add_argument(
    '--iocp', action='store_true', dest='iocp',
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

    if not os.path.isfile('controller.key'):
        print('===== Generating the key files =====')
        machineio.network.Crypto.generate_keyfile('controller.key')
        clients = input('Input the names of your controllers (space separated): ').split(' ')
        for client in clients:
            machineio.network.Crypto.generate_keyfile(f'{client}.key')
        print('You may now exit, distribute the keys and restart the server.')
        print('You will have to connect the clients and then the controllers before issuing commands.')

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
