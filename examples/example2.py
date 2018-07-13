from machineio.group import Group
from machineio.pin import Device
from machineio.pin import Pin
from machineio.safety import Safe
from machineio.safety import stop, kill
import math

aduino = Device('firmata')

right = Pin(aduino, 3, 'OUTPUT', 'SERVO', halt=lambda self: self(0))
left = Pin(aduino, 5, 'OUTPUT', 'SERVO', halt=lambda self: self(0))

power = Group(1)