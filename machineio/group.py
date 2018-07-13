from .safety import Safe
import asyncio
import warnings

class Group:
    def __init__(self, dimensions, limit=lambda x: True, **kwargs):
        '''
        A group of Pin(s) or Group(s)
        :param dimensions: how many args are taken by the functor call
        :param limit: a function that returns a bool based on functor call inputs
        :keyword halt: the safety halting function, see the Move documentation

        It is recommended to use group.add instead of these.
        :keyword objects: a list of objects
        :keyword translations: a list of translation functions
        :keyword delay: a list of time in seconds before triggering
        '''
        # pins OR groups
        self.dimensions = dimensions
        self.objects = []
        self.translations = []
        self.delay = []
        self.limit = limit if type(limit) is tuple else (limit,)

        if 'halt' in kwargs:
            self.halt = kwargs['halt']
        else:
            if not Safe.SUPPRESS_WARNINGS:
                warnings.warn('Safety keyword argument halt=func(Group_obj) was not given.')

        if 'objects' in kwargs and 'translations' in kwargs and 'delay' in kwargs:
            self.objects = kwargs['objects']
            self.translations = kwargs['translations']
            self.delay = kwargs['delay']
            if len(self.objects) != len(self.translations) or \
                    len(self.objects) != len(self.limit) or \
                    len(self.objects) != len(self.delay):
                raise TypeError('There must be translation functions for every object.')

        # append group to safe
        Safe.insert_group(self)

    def __call__(self, *args, **kwargs):
        '''
        Functor call
        :param args:
        :param kwargs:
        :return:
        '''
        if len(args) != self.dimensions:
            raise TypeError(f'This group requires {self.dimensions} arguments')
        for arg, limit in zip(args, self.limit):
            if not limit(arg):
                raise ValueError(f'The value {arg} is not valid with limit {limit}')
        for obj, trans, delay in zip(self.objects, self.translations, self.delay):
            if delay:
                asyncio.TimerHandle(delay, Group._delay_event, [obj, trans, args, kwargs], asyncio.get_event_loop())
            else:
                return obj(trans(*args, **kwargs))

    def add(self, pin_or_group, translation=lambda x: x, delay=None):
        '''
        :param pin_or_group: Pin or Group object
        :param translation: function that takes all inputs of this Group
            and changes it to give to the respective members of the Pin or Group.
            default is x -> x
        :param delay: the number of seconds before event is triggered
        :return:
        '''
        self.delay.append(delay)
        self.objects.append(pin_or_group)
        self.translations.append(translation)

    @staticmethod
    def _delay_event(obj, trans, args, kwargs):
        obj(trans(*args, **kwargs))