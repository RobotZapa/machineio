from machineio import flags

class Device:
    # Do not alter this method.
    def __init__(self, protocol, com_port=None, network=None, **kwargs):
        self.object = None
        self.port = com_port
        self.protocol = protocol.lower()
        self.thread = None
        self.network = network
        self.pins = []
        self.connect()

    def connect(self):
        print(f'Connecting to pretend device on port {self.port}...')

    def config(self, pin):
        self.pins.append(pin)
        pin.callback = self.test_callback if pin.callback is None else pin.callback
        print(f'Configuring pretend pin {pin.pin} {pin.io} {pin.pin_type} hardware on port {self.port}...')

    def io(self, pin_obj, value, *args, **kwargs):
        print(f'pretend device {self.port} pin {pin_obj.pin} has {pin_obj.io} a {pin_obj.pin_type} signal of {value}')
        return value

    def test_input(self, pin, **kwargs):
        import random
        value = random.randint(0, 100)
        print('generated random callback:', value)
        pin.state = value
        pin.callback(value, pin)

    @staticmethod
    def test_callback(pin):
        print(f'callback triggered on pin {pin.pin} with value {pin.state}')