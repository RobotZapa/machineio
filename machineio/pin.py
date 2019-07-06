from .safety import Safe
import warnings
from machineio import flags

class Pin:
    def __init__(self, device, pin, io, mod_flag, **kwargs):
        '''
        :param pin: the pin number on the device
        :param io: Input() | Output()
        :param pin_type: PWM() | Digital() | Analog() | Servo()
        :keyword limits: a tuple (low, high)
        :keyword translate: a function to do __call__ translation
        :keyword translate_limits: a tuple (low, high) limits before translated
        :keyword callback: function that gets called when the pin state changes
        '''
        self.device = device
        self.pin = pin
        self.pin_type = mod_flag.type
        self.mod_flag = mod_flag
        self.limits = kwargs['limits'] if 'limits' in kwargs else None
        self.translate = kwargs['translate'] if 'translate' in kwargs else lambda x: x
        self.translate_limits = kwargs['translate_limits'] if 'translate_limits' in kwargs else False
        self.range = kwargs['range'] if 'range' in kwargs else None
        self.translate_range = kwargs['translate_range'] if 'translate_range' in kwargs else None
        self.state = None
        self.io = io
        self.callback = kwargs['callback'] if 'callback' in kwargs else None
        self.other = kwargs
        if self.range:
            self.limits = self.range
            self.range = True
        if self.translate_range:
            self.translate_limits = self.translate_range
            self.translate_range = True

        if not self.limits and self.pin_type != flags.Digital.type:
            if not Safe.SUPPRESS_WARNINGS:
                print(f'You have not given the mechanical/electrical limits to pin {self.pin} on {self.device}')

        # configure the pin in hardware
        self.device.config(self)

    def __call__(self, value, *args, **kwargs):
        if Safe.proceed:
            if self.limits:
                if type(value) is int or type(value) is float:
                    if self.limits[0] > value or value > self.limits[1]:
                        if self.range:
                            raise ValueError(f'Call {value} is not within limits {self.limits} specified on pin {self.pin}')
                        else:
                            if value < self.limits[0]:
                                return self.limits[0]
                            else:
                                return self.limits[1]
            if self.translate:
                if self.translate_limits:
                    if self.translate_limits[0] <= value <= self.translate_limits[1]:
                        value = self.translate(value)
                        self.state = value
                    else:
                        if self.translate_range:
                            raise ValueError(f'Call {value} not within limits post-translation {self.translate_limits} '
                                             f'specified on pin {self.pin}.')
                        else:
                            if value < self.translate_limits[0]:
                                return self.translate_limits[0]
                            else:
                                return self.translate_limits[1]
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
                                     f'Safe.proceed is False, (have you implemented safety?)')

    def state(self):
        return self.state
