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

    client_name = 'default'

    def connection_made(self, transport):
        self.transport = transport
        if os.path.isfile(f'{MioClient.client_name}.key'):
            self.crypto = machineio.network.Crypto(MioClient.client_name+'.key')
        else:
            print('Encryption key file was not located.')
            self.crypto = machineio.network.Crypto()
        self.mio_locals = {}
        self.mio_globals = {}
        exec('import sys, os', self.mio_globals, self.mio_locals)
        exec("sys.path.insert(0, os.path.abspath('..'))", self.mio_globals, self.mio_locals)
        exec('import machineio', self.mio_globals, self.mio_locals)

        # the first add transmission is unencrypted
        add = machineio.network.assemble(
            'add',
            MioClient.client_name,
            'server',
            'null',
        )
        handshake = self.crypto.handshake_client(add)
        self.transport.write(handshake)
        self.send = lambda ty, fr, to, pl: self.transport.write(
            self.crypto.encrypt(machineio.network.assemble(ty, fr, to, pl)))

        self.mio_globals['send'] = self.send
        self.mio_globals['client_name'] = MioClient.client_name

    def data_received(self, data):
        data = self.crypto.decrypt(data)
        data_type, from_name, to_name, payload = machineio.network.parse(data)
        if data_type == 'command' and from_name == 'controller':
            try:
                # print('payload:', payload)
                # print('locals', self.mio_locals)
                if 'exec' in payload:
                    exec(payload['exec'], self.mio_globals, self.mio_locals)
                if 'eval' in payload:
                    result = eval(payload['eval'], self.mio_globals, self.mio_locals)
                    self.send(
                        'response',
                        MioClient.client_name,
                        'controller',
                        {'state': result, 'future_id': payload['future_id']},
                    )
            except Exception as e:
                print(e)
                print(f'Packet: [{data_type}, {from_name}, {to_name}, {payload}]')
                self.send(
                    'notice',
                    MioClient.client_name,
                    'controller',
                    {'reason': 'error', 'info': e}
                    )
        elif data_type == 'data':
            print('Data:', payload)
            if payload['action'] == 'exec':
                exec(payload['code'], self.mio_globals, self.mio_locals)
            if payload['action'] == 'eval':
                result = eval(payload['code'], self.mio_globals, self.mio_locals)
                self.send(
                    'response',
                    MioClient.client_name,
                    'controller',
                    {'state': result, 'future_id': payload['future_id']},
                )
        else:
            print(f'message type: {data_type} is not handled.')

    def eof_received(self):
        pass

    def connection_lost(self, exc):
        print('Connection Lost! Killing Pins.')
        self.mio_locals['linkfailure']() if 'linkfailure' in self.mio_locals else machineio.kill('Connection lost')


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
    default='default', help='Client Name')
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