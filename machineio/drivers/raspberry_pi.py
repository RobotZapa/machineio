class Device:

    def __init__(self, protocol, com_port=None, network=None, **kwargs):
        self.object = [None]*40
        self.port = com_port
        self.protocol = protocol.lower()
        self.thread = None
        self.network = network
        self.pins = []
        self.connect()
        self.kwargs = kwargs

    def connect(self):
        pass

    def config(self, pin):
        self.pins.append(pin)
        from gpiozero import *
        if pin.pin_type == 'PWM':
            self.object[pin.pin] = PWMOutputDevice(pin.pin)
        elif pin.pin_type == 'DIGITAL':
            if pin.io == 'OUTPUT':
                self.object[pin.pin] = DigitalOutputDevice(pin.pin)
            elif pin.io == 'INPUT':
                pass# todo this
        elif pin.pin_type == 'ANALOG':
            if pin.io == 'INPUT':
                # todo this
        elif pin.pin_type == 'SERVO':
            self.object[pin.pin] = Servo(pin.pin)

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
