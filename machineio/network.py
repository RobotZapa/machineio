import asyncio
import functools
import machineio as mio
import inspect

'''
protocol headers (end of header delimited by the first ~)
(cAUTH_TOKEN,TO_CLIENT_NAME) command - only from controller
(rCLIENT_NAME) response - only to controller
(bCLIENT_NAME) callback - only to controller
(dFROM_NAME,TO_NAME) data - data shuttle
(nCLIENT_NAME) notice - sent to controller
(aCLIENT_NAME) add - adding a new client
(k) key - payload is public key
'''

class _NetworkDevice:
    '''
    The "device driver" to use on a network device
    '''
    def __init__(self, protocol, com_port=None, network=None):
        self.object = None
        self.port = com_port
        self.protocol = protocol.lower()
        self.thread = None
        self.network = network
        self.pins = []
        # sync with _Client
        self.future = None
        self.send = None
        if not self.network:
            self.connect()
        else:
            self.establish()
            self.connect()

    def establish(self):
        event_loop = asyncio.get_event_loop()
        client_completed = asyncio.Future()

        client_factory = functools.partial(
            _Client,
            self,
            future=client_completed,
        )

        factory_coroutine = event_loop.create_connection(
            client_factory,
            self.network.host,
            self.network.port,
        )
        try:
            event_loop.run_until_complete(factory_coroutine)
            event_loop.run_until_complete(client_completed)
        finally:
            event_loop.close()

    def connect(self):
        self.send(
            mionet_assembler(
                'command',
                'controller',
                self.network.client,
                f'device = machineio.Device("{self.protocol}", {self.port})',
            ))

    def config(self, pin):
        self.pins.append(pin)
        halt = inspect.getsource(pin.halt)
        if 'def' in halt:
            self.send(
                mionet_assembler(
                    'command',
                    'controller',
                    self.network.client,
                    halt,
                ))
            self.send(
                mionet_assembler(
                    'command',
                    'controller',
                    self.network.client,
                    f'pin{pin.pin} = machineio.Pin(device, {pin.pin}, {pin.io}, {self.pin_type},'
                    f' halt={halt.split("(")[0].replace("def ","")})',
                ))
        else:
            self.send(
                mionet_assembler(
                    'command',
                    'controller',
                    self.network.client,
                    f'pin{pin.pin} = machineio.Pin(device, {pin.pin}, {pin.io}, {self.pin_type}, halt={halt})',
                ))

    def io(self, pin_obj, value, *args, **kwargs):
        if pin_obj.pin_type == mio.OUTPUT:
            event_loop = asyncio.get_event_loop()
            self.future = asyncio.Future()
            self.send(
                mionet_assembler(
                    'command',
                    'controller',
                    self.network.client,
                    f'respond(pin{pin.pin}({value}))',
                ))
            value = event_loop.run_until_complete(self.future)
            event_loop.close()
        else:
            self.send(
                mionet_assembler(
                    'command',
                    'controller',
                    self.network.client,
                    f'pin{pin.pin}({value})',
                ))
        return value


class _Client(asyncio.Protocol):
    '''
    The connection to the server
    '''
    def __init__(self, device):
        self.device = device

    def connection_made(self, transport):
        q=mionet_assembler('add', 'controller', 'server', f'{self.device.network.control_token}~{self.network.client}')
        self.transport.write(q)
        self.device.send = self.transport.write

    def connection_lost(self, exc):
        self.device.network.linkfailure(self.device.network.client)

    def data_received(self, data):
        msg_type, from_name, to_name, payload = mionet_parser(data)
        # rCLIENT_NAME~PIN_NUMBER~VALUE
        if msg_type == 'response':
            for pin in self.device.pins:
                if pin.pin_type == mio.OUTPUT and int(payload.split('~')[0]) == pin.pin:
                    pin.state = payload.split('~')[1]
                    self.device.future.set_result(pin.state)
        # bCLIENT_NAME~PIN_NUMBER~VALUE
        elif msg_type == 'callback':
            for pin in self.device.pins:
                if pin.pin_type == mio.OUTPUT and int(payload.split('~')[0]) == pin.pin:
                    pin.callback(payload.split('~')[1], pin)
        elif msg_type == 'notice':
            self.network.notice(payload)

class Network:
    '''
    The user interface
    '''
    def __init__(self, client_name, control_token, host, port=20801, **kwargs):
        self.control_token = control_token
        self.host = host
        self.port = port
        self.client = client_name
        self.linkfailure = kwargs['linkfailure'] if 'linkfailure' in kwargs else None

    def notice(self, info):
        pass


def mionet_assembler(type, from_name, to_name, payload, auth_token=None):
    '''

    :param type: 'command', 'response', 'callback', 'notice', 'data', 'add'
    :param from_name:
    :param to_name:
    :param payload:
    :param auth_token: the authorization token created by the server.
    :return: b'string'
    '''
    data = []
    if type == 'command':
        data.append('c')
        if auth_token:
            data.append(auth_token)
            data.append(',')
        else:
            raise ValueError('Required authorization token for control is missing.')
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
    return ''.join(data).encode()


def mionet_parser(data):
    '''
    Validates the message, and returns the raw data for execution
    :param str_data:
    :return: type, from_name, to_name, payload
    '''
    type, from_name, to_name, payload = None, None, None, None
    data = data.decode()
    header = data.split('~')[0]
    payload = data.split('~')[1:]
    if data.startswith('c'):
        msg_type = 'command'
        from_name, to_name = header.splti(',')
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
