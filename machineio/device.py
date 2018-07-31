import sys, os
# put driver files in the current working path scope
sys.path.insert(0, os.path.dirname(os.path.realpath('drivers'))+'/drivers')


#Function that returns dynamic device protocol object
#It is pretending to be a class for the user
def Device(protocol, com_port=None, network=None):
    if network is not None:
        from .network import _NetworkDevice
        return _NetworkDevice(protocol, com_port, network)
    try:
        exec(f'from machineio.drivers import {protocol} as proto', locals(), globals())
    except ImportError:
        print('If you would like to add a driver file for this protocol please submit a request!')
        raise NotImplemented(f'Protocol {protocol} may not be implemented yet or dependencies for it are missing.')
    return proto.Device(protocol, com_port, network)

