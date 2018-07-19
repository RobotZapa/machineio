from .safety import Safe
import warnings
import sys, os
# put driver files in the current working path scope
sys.path.insert(0, os.path.dirname(os.path.realpath('drivers'))+'/drivers')

class Pin:
    def __init__(self, device, pin, io, pin_type, **kwargs):
        '''
        :param pin: the pin number on the device
        :param io: INPUT | OUTPUT | True
        :param pin_type: PWM | DIGITAL | ANALOG | SERVO
        :keyword limits: a tuple (low, high)
        :keyword translate: a function to do __call__ translation
        :keyword translate_limits: a tuple (low, high) limits before translated
        :keyword halt: function that takes (self) as a parameter and calls for safe shutdown in emergencies.
        :keyword callback: function that gets called when the pin state changes
        '''
        self.device = device
        self.pin = pin
        self.limits = kwargs['limits'] if 'limits' in kwargs else False
        self.translate = kwargs['translate'] if 'translate' in kwargs else lambda x: x
        self.translate_limits = kwargs['translate_limits'] if 'translate_limits' in kwargs else False
        self.state = None
        self.io = io
        self.callback = kwargs['callback'] if 'callback' in kwargs else None

        if 'halt' in kwargs:
            self.halt = kwargs['halt']
        else:
            if not Safe.SUPPRESS_WARNINGS:
                raise Warning('Safety keyword argument halt=func(Pin_obj) was not given.')

        if pin_type == 'BOOLEAN':
            pin_type = 'DIGITAL'
            self.translate = lambda x: int(x)
        elif pin_type == 'PPM' or pin_type == 'PCM':
            pin_type = 'SERVO'
        self.pin_type = pin_type

        if io not in ('INPUT', 'OUTPUT', True):
            raise Exception(f'I/O {io} is not valid.')
        if pin_type not in ('PWM', 'DIGITAL', 'ANALOG', 'SERVO'):
            raise NotImplemented(f'Type {pin_type} does not have a code path!')

        if not self.limits and pin_type != 'DIGITAL':
            if not Safe.SUPPRESS_WARNINGS:
                warnings.warn(f'You have not given the mechanical/electrical limits to pin {self.pin} on {self.device}')

        # configure the pin in hardware
        self.device.config(self)
        # append pin to Safe
        Safe.pins.append(self)

    def __call__(self, value, *args, **kwargs):
        if Safe.proceed:
            if self.limits and value is int:
                if value < self.limits[0] or value > self.limits[1]:
                    raise ValueError(f'Call {value} is not within mechanical/electrical/logical limits specified')
            if self.translate:
                if self.translate_limits:
                    if value > self.translate_limits[0] and value < self.translate_limits[1]:
                        value = self.translate(value)
                        self.state = value
                    else:
                        raise ValueError('Call not within translatable limits.')
                else:
                    value = self.translate(value)
                    self.state = value
            self.device.io(self, value, *args, **kwargs)
        else:
            if not Safe.SUPPRESS_WARNINGS:
                raise RuntimeWarning(f'Move command on {self.device} pin {self.pin} cannot be executed!,'
                                     f'Safe.proceed is False')


#Function that returns dynamic device protocol object
#It is pretending to be a class for the user
def Device(protocol, com_port=None):
    try:
        exec(f'from machineio.drivers import {protocol} as proto', locals(), globals())
    except ImportError:
        print('If you would like to add a driver file for this protocol please submit a request!')
        raise NotImplemented(f'Protocol {protocol} may not be implemented yet. Or dependencies for it are missing.')
    return proto.Device(protocol, com_port)