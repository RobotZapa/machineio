class Device:
    def __init__(self, protocol, com_port=None):
        self.object = None
        self.port = com_port
        self.protocol = protocol.lower()
        self.thread = None
        self.connect()

    def connect(self):
        print(f'Connecting to pretend device on port {self.port}...')

    def config(self, pin):
        print(f'Configuring pin {pin.pin} {pin.io} {pin.pin_type} hardware on port {self.port}...')

    def io(self, pin_obj, value, *args, **kwargs):
        print(f'pretend device {self.port} pin {pin_obj.pin} has {pin_obj.io} a {pin_obj.pin_type} signal of {value}')
        return self.port, pin_obj.pin, value
