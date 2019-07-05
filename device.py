import sys, os
# put driver files in the current working path scope
sys.path.insert(0, os.path.dirname(os.path.realpath('drivers'))+'/drivers')


# Function that returns dynamic device protocol object
# It is duck typed to look like a class since it functions like one
def Device(protocol, com_port=None):
    '''
    Represents the device
    (This is a duck typed function that returns the protocol relevant class object)
    :param protocol: the protocol/driver used on the device
    :param com_port: the com port to use
    :return: A device object
    '''
    try:
        exec(f'from machineio.drivers import {protocol} as proto', locals(), globals())
    except ImportError:
        print('If you would like to add a driver file for this protocol please submit a request!')
        raise NotImplemented(f'Protocol {protocol} may not be implemented yet or dependencies for it are missing.')
    return proto.Device(protocol, com_port)
