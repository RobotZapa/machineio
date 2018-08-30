# Modular flags

class PPM:
    type = 'PPM'

    def __int__(self, **kwargs):
        '''
        Modular type flag Servo for Pulse-position Modulation
        '''
        self.netcode = f'machineio.PPM()'
        self.type = 'PPM'

class PWM:
    type = 'PWM'

    def __init__(self, **kwargs):
        '''
        Modular type flag PWM
        '''
        self.netcode = f'machineio.PWM()'
        self.type = 'PWM'
        self.mode = kwargs['mode'] if 'mode' in kwargs else None


class Digital:
    type = 'DIGITAL'

    def __init__(self, **kwargs):
        '''
        Modular type flag Digital
        '''
        self.netcode = f'machineio.Digital()'
        self.type = 'DIGITAL'


class Analog:
    type = 'ANALOG'

    def __init__(self, **kwargs):
        '''
        Modular type flag Analog
        '''
        self.netcode = f'machineio.Analog()'
        self.type = 'ANALOG'


def Servo(**kwargs):
    return PPM(**kwargs)

def Input(**kwargs):
    return 'INPUT'

def Output(**kwargs):
    return 'OUTPUT'


_INPUT = Input()
_OUTPUT = Output()


