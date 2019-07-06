class Safe:
    #Singleton pattern

    # blocks all move calls when False
    proceed = False

    # for use with 'test' protocol only OR if you don't want to use these safety features
    SUPPRESS_WARNINGS = False

    # error log file name
    logfile = None

    #functions (need assignment)
    #TODO add this to the docs and check for it after setup
    stop = None
    kill = None
    kwargs = None
    args = None

    @staticmethod
    def set(stop_function, kill_function, args, kwargs):
        '''
        :param stop_function: a function handle
        :param kill_function: a function handle
        :param args: list of arguments passed into the stop and kill functions
        :param kwargs: list of keyword arguments passed into the stop and kill functions
        :return:
        '''
        Safe.stop = stop_function
        Safe.kill = kill_function
        Safe.args = args
        Safe.kwargs = kwargs
        Safe.proceed = True

    @staticmethod
    def log(text, logfile='machine_error.log'):
        '''
        Writes a line of text to the safety log file.
        :param text: a string
        :return: appends error.log file
        '''
        try:
            file = open(logfile, 'r').close()
        except IOError:
            file = open(logfile, 'w+').close()
        file_handle = open(logfile, 'w')
        file_handle.write(text+'\n')
        file_handle.close()


def kill(reason='no reason given'):
    '''
    This function must cut power to the mechanically active systems.
    This function should cut power to high power non-control systems.
    :return:
    '''
    Safe.kill(*Safe.args, **Safe.kwargs)
    Safe.proceed = False
    Safe.log('Kill:'+reason)

def stop(reason='no reason given'):
    '''
    This function should halt operation in a mechanically safe fashion
    :return:
    '''
    Safe.stop(*Safe.args, **Safe.kwargs)
    Safe.proceed = False
    Safe.log('Stop:' + reason)