import threading


def concurrent(func):
    '''
    For functions that end but need to run concurrently
    :param func:
    :return:
    '''
    def decorator(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return decorator
