import RPi.GPIO as GPIO

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

    def __del__(self):
        for obj in self.object:
            obj.stop()
        GPIO.cleanup()

    def connect(self):
        pass

    def config(self, pin):
        self.pins.append(pin)
        GPIO.setmode(GPIO.BOARD)
        if pin.pin_type == 'PWM':
            if pin.io == 'INPUT':
                print('PWM input not supported.')
            elif pin.io == 'OUTPUT':
                GPIO.setup(pin.pin, GPIO.OUT)
                if 'frequency' in pin.other:
                    self.object[pin.pin] = GPIO.PWM(pin.pin, pin.other['frequency'])
                else:
                    self.object[pin.pin] = GPIO.PWM(pin.pin, 50)
                self.object[pin.pin].start(0)
        elif pin.pin_type == 'DIGITAL':
            if pin.io == 'OUTPUT':
                GPIO.setup(pin.pin, GPIO.OUT)
            elif pin.io == 'INPUT':
                GPIO.setup(pin.pin, GPIO.IN)
        elif pin.pin_type == 'ANALOG':
                print('Analog not supported.')
        elif pin.pin_type == 'PPM':
            GPIO.setup(pin.pin, GPIO.OUT)
            if 'frequency' in pin.other:
                self.object[pin.pin] = GPIO.PWM(pin.pin, pin.other['frequency'])
            else:
                self.object[pin.pin] = GPIO.PWM(pin.pin, 50)
            self.object[pin.pin].start(50)

    def io(self, pin, value, *args, **kwargs):
        if pin.pin_type in ('PWM', 'PPM', 'ANALOG'):
            if pin.io == 'OUTPUT':
                self.object[pin.pin].ChangeDutyCycle(value)
            elif pin.io == 'INPUT':
                print('Analog,PWM,Servo Input not supported.')
        elif pin.pin_type == 'DIGITAL':
            if pin.io == 'OUTPUT':
                GPIO.output(pin.pin, value)
            elif pin.io == 'INPUT':
                return GPIO.input(pin.pin)
