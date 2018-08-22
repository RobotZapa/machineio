import sys, os, argparse
import threading, time
import socket
# for a reason as to why imports of siblings is so ugly
# see https://mail.python.org/pipermail/python-3000/2007-April/006793.html
sys.path.insert(0, os.path.abspath('..'))
import machineio

class MioClient:

    version = '2.0'

    def __init__(self, client_name, host, port):
        self.client_name = client_name
        self.host = host
        self.port = port
        self.send = None
        self.conn = None
        self.crypto = None
        self.link_failure = lambda s: machineio.kill('Link failure')

        self.mio_globals = {}
        self.mio_locals = {}

        # setup

        if os.path.isfile(f'{self.client_name}.key'):
            self.crypto = machineio.network.Crypto(self.client_name + '.key')
        else:
            print('Encryption key file was not located. You can create one with server.py --make_key client_name')
            self.crypto = machineio.network.Crypto()

        exec('import sys, os', self.mio_globals, self.mio_locals)
        exec("sys.path.insert(0, os.path.abspath('..'))", self.mio_globals, self.mio_locals)
        exec('import machineio', self.mio_globals, self.mio_locals)

        #           create the socket connection
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.conn = socket.socket(af, socktype, proto)
            except OSError as msg:
                self.conn = None
                continue
            try:
                self.conn.connect(sa)
            except OSError as msg:
                self.conn.close()
                self.conn = None
                continue
            break
        if self.conn is None:
            print('could not open socket')
            sys.exit(1)
        #           start the receiver thread
        receiver = threading.Thread(target=self._receiver_thread)
        receiver.start()

        ###########
        # self.send(msg_type, msg_to, msg_from, payload, **kwargs)
        ###########
        self.send = lambda ty, fo, to, pl, **ka: self.conn.sendall(
            machineio.network.pack(self.crypto.encrypt(
                machineio.network.assemble(ty, fo, to, pl, **ka)
            )))
        self.mio_globals['send'] = self.send
        self.mio_globals['client_name'] = self.client_name

        # handshake with server
        handshake = machineio.network.assemble('add', self.client_name, 'server', 'null')
        handshake = self.crypto.handshake_client(handshake)
        handshake = machineio.network.pack(handshake)
        self.conn.sendall(handshake)

        print(f'Client {MioClient.version} startup complete.')


    def _receiver_thread(self):
        #todo call self.link_failure on discconnect
        #todo print that execution was halted
        with self.conn:
            while True:
                socket_data = machineio.network.unpack(self.conn.recv(1024))
                for data in socket_data:
                    self.process_data(data)

    def process_data(self, data):
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
                        self.client_name,
                        'controller',
                        {'state': result, 'future_id': payload['future_id']},
                    )
            except Exception as e:
                print('Exception: ', e)
                print(f'Exception Packet: [{data_type}, {from_name}, {to_name}, {payload}]')
                self.send(
                    'notice',
                    self.client_name,
                    'controller',
                    {'reason': 'error', 'info': e}
                )
        elif data_type == 'data':
            # print('Data:', payload)
            if payload['action'] == 'exec':
                exec(payload['code'], self.mio_globals, self.mio_locals)
            if payload['action'] == 'eval':
                result = eval(payload['code'], self.mio_globals, self.mio_locals)
                self.send(
                    'response',
                    self.client_name,
                    'controller',
                    {'state': result, 'future_id': payload['future_id']},
                )
        elif data_type == 'notice' and from_name in ['server', 'controller']:
            if payload == 'halt':
                exec('machineio.kill()', self.mio_globals, self.mio_locals)
                print('Server or Controller sent halt signal.')
        else:
            print(f'message type: {data_type} is not handled.')


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

    client = MioClient(args.name, args.host, args.port)

    while True:
        time.sleep(10)
