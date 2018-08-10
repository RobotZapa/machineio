import sys
import machineio as mio
import inspect
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import time
import threading
import socket
import pickle

'''
Network protocol

handshake
    keyfile_name.key~ENCRYPTED_MESSAGE_HERE

encryption
    see readme and design rational

packet
    serialized python list
    [packet_type, from_name, to_name, payload]
    payload is dict containing packet_type specific data 
'''


class _NetworkDevice:
    '''
    The "device driver" to use on a network device
    '''
    def __init__(self, protocol, com_port=None, client_name='default', network=None):
        self.object = None
        self.port = com_port
        self.protocol = protocol.lower()
        self.thread = None
        self.network = network
        self.client_name = client_name
        self.pins = []
        self.send = lambda dt, fn, tn, pl: network._transmit(dt, fn, tn, pl)
        self.connect()

    def connect(self):
        self.send(
            'command',
            'controller',
            self.client_name,
            {'exec': f'device = machineio.Device("{self.protocol}", {self.port})'},
            )

    def config(self, pin):
        self.pins.append(pin)
        network_callback = 'lambda val, pin: send("callback", client_name, ' \
                           '"controller", {"pin": pin.pin, "value": val})'
        code = inspect.getsource(pin.halt).split(',')
        for i, part in enumerate(code):
            if 'halt' in part:
                halt = part
                # if it's the last member of the split it is the end of the line
                if i + 1 == len(code):
                    halt = halt[0:halt.rfind(')')].strip()
                break
        if 'lambda' in halt:
            self.send(
                'command',
                'controller',
                self.client_name,
                {'exec': f'pin{pin.pin} = machineio.Pin(device, {pin.pin}, "{pin.io}", "{pin.pin_type}", {halt},'
                         f' callback={network_callback})'},
                )
        else:
            pass #todo if halt is not a lambda function

    def io(self, pin_obj, value, *args, **kwargs):
        if pin_obj.pin_type == mio.OUTPUT:
            future_id = secrets.randbits(16)
            while future_id in self.network.future_response:
                future_id = secrets.randbits(16)
            self.network.future_response[future_id] = Future()
            self.send(
                'command',
                'controller',
                self.client_name,
                {'eval': f'pin{pin_obj.pin}({value})', 'future_id': future_id},
                )
            timeout = 0
            while not self.network.future_response[future_id].done():
                time.sleep(.0001)
                timeout += 1
                if timeout == 10000:
                    raise IOError('network took to long to respond.')
            value = self.network.future_response[future_id].result()
            del self.network.future_response[future_id]
            pin_obj.state = value
        else:
            self.send(
                'command',
                'controller',
                self.client_name,
                {'exec': f'pin{pin_obj.pin}({value})'},
                )
        return value


class Future:
    def __init__(self):
        self.complete = False
        self.value = None

    def set_value(self, value):
        self.value = value
        self.complete = True

    def done(self):
        return self.complete

    def result(self):
        return self.value


class Network:
    def __init__(self, host, port=20801, key_file='controller.key', **kwargs):
        # public members
        self.host = host
        self.port = port
        self.clients = {}

        # private members
        self.device = None
        self.crypto = Crypto(key_file)
        self.future_response = {}
        self.conn = None
        self.linkfailure = kwargs['linkfailure'] if 'linkfailure' in kwargs else lambda self: mio.stop('link failure')

        # setup
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

    def _receiver_thread(self):
        with self.conn:
            while True:
                socket_data = self.conn.recv(1024)
                raw_data = self.crypto.decrypt(socket_data)
                msg_type, msg_from, msg_to, payload = parse(raw_data)
                if msg_type == 'response':
                    '''
                    response payload is
                    {'future_id': 4, 'state': 32.4}
                    '''
                    self.future_response[payload['future_id']].set_value(payload['state'])
                elif msg_type == 'callback':
                    '''
                    callback payload is
                    {'pin': 5, 'value': True}
                    '''
                    for pin in self.device.pins:
                        if payload['pin'] == pin.pin:
                            pin.callback(payload['value'], pin)
                            pin.state = payload['value']
                            break
                elif msg_type == 'notice':
                    '''
                    notice payload is
                    {'reason': why, 'info': extra_stuff}
                    '''
                    if payload['reason'] == 'linkfailure':
                        self.linkfailure(self)
                    elif payload['reason'] == 'error':
                        raise Exception(f'Unhandled exception on {msg_from}: {payload["info"]}')
                    else:
                        print('NOTICE:', payload)

    def _transmit(self, msg_type, msg_from, msg_to, msg_payload, **kwargs):
        raw_data = assemble(msg_type, msg_from, msg_to, msg_payload, **kwargs)
        if 'handshake' in kwargs:
            if kwargs['handshake'] == 'server':
                socket_data = self.crypto.handshake_server(raw_data)
            else:
                socket_data = self.crypto.handshake_client(raw_data)
        else:
            socket_data = self.crypto.encrypt(raw_data)
        print(self.conn)
        self.conn.sendall(socket_data)

    def send(self, client_name, **kwargs):
        '''
        To get data/command to a particular client
        :param client_name: the name of the client to send to.
        :param command: the line of python code to execute as a string.
        :param respond: set True if you would like to wait for the response.
        :return: The response if any else None.
        '''
        if 'exec' in kwargs:
            self._transmit(
                'data',
                'controller',
                client_name,
                {'action': 'exec', 'code': kwargs['exec']}
            )
        elif 'eval' in kwargs:
            future_id = secrets.randbits(16)
            while future_id in self.future_response:
                future_id = secrets.randbits(16)
            self.future_response[future_id] = Future()
            self._transmit(
                'data',
                'controller',
                client_name,
                {'action': 'eval', 'code': kwargs['eval'], 'future_id': future_id}
            )
            timeout = 0
            while not self.future_response[future_id].done():
                time.sleep(.0001)
                timeout += 1
                if timeout == 10000:
                    raise IOError('network took to long to respond.')
            value = self.future_response[future_id].result()
            del self.future_response[future_id]
            return value

    def Device(self, protocol, com_port=None, client_name='default'):
        '''
        Creates a network device object. Functions exactly like a regular object after creation.
        :param protocol: the device protocol/driver
        :param com_port: the port name the device is connected to on the client if applicable
        :param client_name: the name of the client (named at startup of client.py)
        :return: the network object
        '''
        self._transmit('add', 'controller', 'server', client_name, handshake='client')
        self.device = _NetworkDevice(protocol, com_port, client_name, self)
        self.clients[client_name] = self.device
        return self.device


class Crypto:

    def __init__(self, keyfile=None):
        self.link = None
        self.version = None
        self.auth = None
        self.iv_bytes = None
        self.keyfile = None

        self.load(keyfile)

    def load(self, keyfile):
        self.keyfile = keyfile
        if keyfile is not None:
            f = open(keyfile, 'rb')
            file_dict = pickle.loads(f.read())
            f.close()
            self.version = file_dict['version']
            if 'v0.1' == self.version:
                key = file_dict['key']
                self.iv_bytes = file_dict['iv_bytes']
                self.auth = file_dict['auth']
                self.link = AESGCM(key)

    def handshake_server(self, handshake):
        '''
        Takes handshake_packet and returns add_packet
        :param handshake:
        :return: add
        '''
        self.load(handshake.split(b'~')[0].decode())
        return self.decrypt(b'~'.join(handshake.split(b'~')[1:]))

    def handshake_client(self, add, **kwargs):
        '''
        Takes add_packet and returns handshake_packet
        :param add:
        :return: handshake
        '''
        return self.keyfile.encode()+b'~'+self.encrypt(add)

    def encrypt(self, data):
        if self.version == 'v0.1':
            iv = secrets.token_bytes(self.iv_bytes)
            cdata = iv + self.link.encrypt(iv, data, self.auth)
        else:
            raise UserWarning('A message was not encrypted!')
        return cdata

    def decrypt(self, cdata):
        iv = cdata[:self.iv_bytes]
        cdata = cdata[self.iv_bytes:]
        if self.version == 'v0.1':
            data = self.link.decrypt(iv, cdata, self.auth)
        else:
            raise UserWarning('A message was not encrypted!')
        return data

    @staticmethod
    def generate_keyfile(filename, version='v0.1', key_bits=128, iv_bytes=12, auth_bytes=32):
        auth = secrets.token_bytes(auth_bytes)
        if version == 'v0.1':
            key = AESGCM.generate_key(bit_length=key_bits)
        lines = pickle.dumps({'version': version,
                            'key': key,
                            'iv_bytes': iv_bytes,
                            'auth': auth,
                              })
        f = open(filename, 'wb+')
        f.write(lines)
        f.close()


def assemble(type_str, from_name, to_name, payload, **kwargs):
    data = [type_str, from_name, to_name, payload]
    return pickle.dumps(data)


def parse(raw_data):
    type_str, from_name, to_name, payload = pickle.loads(raw_data)
    return type_str, from_name, to_name, payload


def mionet_assembler(type, from_name, to_name, payload, **kwargs):
    '''

    :param type: 'command', 'response', 'callback', 'notice', 'data', 'add'
    :param from_name:
    :param to_name:
    :param payload:
    :return: b'string'
    '''
    data = []
    if type == 'command':
        data.append(to_name)
        data.append('~')
        data.append(payload)
    elif type == 'response':
        data.append('r')
        data.append(from_name)
        data.append('~')
        data.append(payload)
    elif type == 'callback':
        data.append('b')
        data.append(to_name)
        data.append('~')
        data.append(payload)
    elif type == 'notice':
        data.append('n')
        data.append(from_name)
        data.append('~')
        data.append(payload)
    elif type == 'data':
        data.append('d')
        data.append(from_name)
        data.append(',')
        data.append(to_name)
        data.append('~')
        data.append(payload)
    elif type == 'add':
        data.append('a')
        data.append(from_name)
        data.append('~')
        data.append(payload)
    data = ''.join(data).encode()
    return data


def mionet_parser(data, **kwargs):
    '''
    Validates the message, and returns the raw data for execution
    :param str_data:
    :return: type, from_name, to_name, payload
    '''
    type, from_name, to_name, payload = None, None, None, None
    data = data.decode()
    header = data.split('~')[0]
    payload = '~'.join(data.split('~')[1:])
    if data.startswith('c'):
        msg_type = 'command'
        from_name = 'controller'
        to_name = header[1:]
    elif data.startswith('r'):
        msg_type = 'respond'
        from_name = header[1:]
        to_name = 'controller'
    elif data.startswith('b'):
        msg_type = 'callback'
        from_name = header[1:]
        to_name = 'controller'
    elif data.startswith('n'):
        msg_type = 'notice'
        from_name = header[1:]
        to_name = 'controller'
    elif data.startswith('d'):
        msg_type = 'data'
        from_name, to_name = header.split(',')
    elif data.startswith('a'):
        msg_type = 'add'
        from_name = header.split(',')[0][1:]
        to_name = 'server'
    return msg_type, from_name, to_name, payload
