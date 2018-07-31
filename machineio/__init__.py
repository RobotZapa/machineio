from .group import Group
from .device import Device
from .network import Network
from .pin import Pin
from .safety import Safe
from .safety import stop, kill

def test():
    print('Import working')

# FLAG IO Type
OUTPUT = 'OUTPUT'
INPUT = 'INPUT'

# FLAG Encoding Type
SERVO = 'SERVO' # PPM range of PWM
PWM = 'PWM'
DIGITAL = 'DIGITAL'
ANALOG = 'ANALOG'
