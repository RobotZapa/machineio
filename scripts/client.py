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


class MioClient(asyncio.Protocol):

    client_name = 'test'

    def connection_made(self, transport):
        self.transport = transport
        self.mio_locals = {}
        self.mio_globals = {}
        exec('import importlib', self.mio_globals, self.mio_locals)
        exec('importlib.import_module(".", "machineio")', self.mio_globals, self.mio_locals)

        add = machineio.network.mionet_assembler(
            'add',
            MioClient.client_name,
            'server',
            'null',
        )
        self.transport.write(add)

    def data_received(self, data):
        data_type, from_name, to_name, payload = machineio.network.mionet_parser(data)
        if data_type == 'command' and from_name == 'controller':
            # this should be a function call
            result = eval(payload, self.mio_globals, self.mio_locals)
            self.transport.write(machineio.network.mionet_assembler(
                'result',
                MioClient.client_name,
                'controller',
                result,
            ))
        elif data_type == 'data':
            # this should be a variable setter
            exec(payload, self.mio_globals, self.mio_locals)
        elif data_type == 'key':
            pass

    def eof_received(self):
        pass

    def connection_lost(self, exc):
        machineio.kill('Connection lost')


def start_client(loop, host, port):
    t = asyncio.Task(loop.create_connection(MioClient, host, port))
    loop.run_until_complete(t)


ARGS = argparse.ArgumentParser(description='Machine IO network client.')
ARGS.add_argument(
    '--host', action='store', dest='host',
    default = '127.0.0.1', help='Host name')
ARGS.add_argument(
    '--port', action='store', dest='port',
    default=20801, type=int, help='Port number')
ARGS.add_argument(
    '--name', action='store', dest='name',
    default='test', help='Client Name')
ARGS.add_argument(
    '--iocp', action='store_true', dest='iocp',
    default=False, help='Use IOCP event loop')


if __name__ == '__main__':
    args = ARGS.parse_args()

    if ':' in args.host:
        args.host, port = args.host.split(':', 1)
        args.port = int(port)

    MioClient.client_name = args.name

    if args.iocp:
        from asyncio import windows_events
        loop = windows_events.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    print(f'Using backend: {loop.__class__.__name__}')

    if signal is not None and sys.platform != 'win32':
        loop.add_signal_handler(signal.SIGINT, loop.stop)

    client = start_client(loop, args.host, args.port)

    try:
        loop.run_forever()
    finally:
        client.close()
        loop.close()