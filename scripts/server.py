import sys, os, argparse
import asyncio

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

    def connection_made(self, transport):
        print('Client has connected.')
        self.transport = self.transport
        self.crypto = machineio.network.Crypto()

    def connection_lost(self, exc):
        for key in MioServer.clients:
            if MioServer.clients[key] is self:
                print('Client was properly removed.')
                MioServer.controller[key].transport.write(
                    machineio.network.mionet_assembler('notice', 'server', 'controller', 'linkfailure'))
                del MioServer.clients[key]
                break
        else:
            print('Client was not properly removed.')
        print('Client has disconnected.')

    def data_received(self, data):
        data = self.crypto.decrypt(data)
        data_type, from_name, to_name, payload = machineio.network.mionet_parser(data)
        if data_type == 'add':
            if from_name == 'controller':
                MioServer.controller[payload.split('~')[1]] = self
            else:
                if from_name in MioServer.clients or from_name in ['controller', 'server']:
                    raise NameError('Client with this name already exists')
                else:
                    MioServer.clients[from_name] = self
                    if os.path.isfile(f'{from_name}.key'):
                        self.crypto.load(f'{from_name}.key')
                    MioServer.keys[from_name] = self.crypto
        elif data_type:
            if to_name == 'controller':
                MioServer.controller[to_name].transport.write(MioServer.keys[to_name].encypt(data))
            elif to_name == 'server':
                pass
            else:
                data = MioServer.keys[to_name].encrypt(data)
                MioServer.clients[to_name].transport(data)

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
        machineio.network.Crypto.genorate_keyfile('controller.key')
        clients = input('Input the names of your controllers (space separated): ').split(' ')
        for client in clients:
            machineio.network.Crypto.genorate_keyfile(f'{client}.key')
        print('=== Please distribute these key files to the proper hosts ===')

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
