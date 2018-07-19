class Device:
    def __init__(self, protocol, com_port=None):
        self.object = None
        self.port = com_port
        self.protocol = protocol.lower()
        self.thread = None
        self.connect()

    def connect(self):
        print(f'Connecting to device on port {self.port}...')
        from pymata_aio.pymata3 import PyMata3
        self.object = PyMata3(com_port=self.port)

    def config(self, pin):
        from pymata_aio.constants import Constants
        if pin.pin_type == 'PWM':
            self.object.set_pin_mode(pin.pin, Constants.PWM)
        elif pin.pin_type == 'DIGITAL':
            if pin.io == 'OUTPUT':
                self.object.set_pin_mode(pin.pin, Constants.OUTPUT, callback=pin.callback)
            elif pin.io == 'INPUT':
                self.object.set_pin_mode(pin.pin, Constants.INPUT, callback=pin.callback)
        elif pin.pin_type == 'ANALOG':
            if pin.io == 'INPUT':
                self.object.enable_analog_reporting(pin.pin)
            self.object.set_pin_mode(pin.pin, Constants.ANALOG, callback=pin.callback)
        elif pin.pin_type == 'SERVO':
            self.object.servo_config(pin.pin)

    def io(self, pin, value, *args, **kwargs):
        if pin.pin_type in ('PWM', 'SERVO', 'ANALOG'):
            if pin.io == 'OUTPUT':
                self.object.analog_write(pin.pin, value)
            elif pin.io == 'INPUT':
                return self.object.analog_read(pin.pin)
        elif pin.pin_type == 'DIGITAL':
            if pin.io == 'OUTPUT':
                self.object.digital_pin_write(pin.pin, value)
            elif pin.io == 'INPUT':
                return self.object.digital_read(pin.pin)