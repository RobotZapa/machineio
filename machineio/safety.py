class Safe:
    '''
    Safe is a non-instanced class used as a global variable for movement safety
    Due to this, all move instructions must be executed from the same thread or
        without GIL bypasses, like mutiprocessing.
    '''
    # blocks all move calls when False
    proceed = True
    # a list of all pins in use
    pins = []
    # a list of all groups in use (ordered from deepest first)
    groups = []

    # for use with 'test' protocol only OR if you don't want to use these safety features
    SUPPRESS_WARNINGS = False

    #error log file name
    # logfile = 'error.log'
    # open(logfile, 'w+').close()

    @staticmethod
    def insert_group(group):
        depth = Safe._measure_depth(group)
        for i in range(0, len(Safe.groups)):
            if Safe._measure_depth(Safe.groups[i]) <= depth:
                Safe.groups.insert(i, group)
                return


    @staticmethod
    def _list_children(group):
        contains = []
        if type(group).__name__ == 'Pin':
            return contains
        for item in group.objects:
            if type(item).__name__ == 'Group':
                contains.append(item)
                contains += Safe._list_children(item)
            else:
                contains.append(item)
        return contains

    @staticmethod
    def _measure_depth(group, depth=0):
        if type(group).__name__ == 'Pin':
            return 0
        for item in group.objects:
            if type(item).__name__ == 'Group':
                measure = Safe._measure_depth(item, depth+1)
                depth = measure if measure > depth else depth
        return depth


def kill(reason_message='No reason was given.'):
    '''
    Sets all pins to their assigned safe state.
    Logs any given reasons
    Prevents further movement
    :return:
    '''
    for pin in Safe.pins:
        pin.halt(pin)
    Safe.proceed = False
    reason_message = 'KILL: '+reason_message+'\n'
    logfile = open(Safe.logfile, 'a')
    logfile.write(reason_message)
    logfile.close()


def stop(reason_message='No reason was given.'):
    '''
    Calls the stop function assigned to all groups
    Sets safe state of all pins not in a group
    Prevents further movement
    :return:
    '''
    incomplete = Safe.groups + Safe.pins
    for item in incomplete:
        result = item.halt(item)
        if result is False:
            children = Safe._list_children(item)
            for child in children:
                incomplete.remove(child)
    Safe.proceed = False
    reason_message = 'STOP: '+reason_message+'\n'
    logfile = open(Safe.logfile, 'a')
    logfile.write(reason_message)
    logfile.close()
