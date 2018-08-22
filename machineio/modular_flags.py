# Modular flags


class Servo:
    type = 'SERVO'

    def __int__(self, **kwargs):
        self.netcode = f'machineio.Servo({**kwargs})'
        self.type = 'SERVO'


class PWM:
    type = 'PWM'

    def __init__(self, **kwargs):
        self.netcode = f'machineio.PWM({**kwargs})'
        self.type = 'PWM'


class Digital:
    type = 'DIGITAL'

    def __init__(self, **kwargs):
        self.netcode = f'machineio.Digital({**kwargs})'
        self.type = 'DIGITAL'


class Analog:
    type = 'ANALOG'

    def __init__(self, **kwargs):
        self.netcode = f'machineio.Analog({**kwargs})'
        self.type = 'ANALOG'


