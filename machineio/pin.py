from .safety import Safe
import warnings

class Pin:
    def __init__(self, device, pin, io, mod_flag, **kwargs):
        '''
        :param pin: the pin number on the device
        :param io: INPUT | OUTPUT
        :param pin_type: PWM | DIGITAL | ANALOG | SERVO
        :keyword limits: a tuple (low, high)
        :keyword translate: a function to do __call__ translation
        :keyword translate_limits: a tuple (low, high) limits before translated
        :keyword halt: function that takes (self) as a parameter and calls for safe shutdown in emergencies.
        :keyword callback: function that gets called when the pin state changes
        '''
        self.device = device
        self.pin = pin
        self.pin_type = mod_flag.type
        self.mod_flag = mod_flag
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

        if not self.limits and self.pin_type != 'DIGITAL':
            if not Safe.SUPPRESS_WARNINGS:
                warnings.warn(f'You have not given the mechanical/electrical limits to pin {self.pin} on {self.device}')

        # configure the pin in hardware
        self.device.config(self)
        # append pin to Safe
        Safe.pins.append(self)

    def __call__(self, value, *args, **kwargs):
        if Safe.proceed:
            if self.limits and type(value) is int or type(value) is float:
                if self.limits[0] > value or value > self.limits[1]:
                    raise ValueError(f'Call {value} is not within limits specified')
            if self.translate:
                if self.translate_limits:
                    if self.translate_limits[0] <= value <= self.translate_limits[1]:
                        value = self.translate(value)
                        self.state = value
                    else:
                        raise ValueError('Call not within limits post-translation specified.')
                else:
                    value = self.translate(value)
                    self.state = value
            value = self.device.io(self, value, *args, **kwargs)
            if value is not None:
                self.state = value
            return value
        else:
            if not Safe.SUPPRESS_WARNINGS:
                raise RuntimeWarning(f'Move command on {self.device} pin {self.pin} cannot be executed!,'
                                     f'Safe.proceed is False')