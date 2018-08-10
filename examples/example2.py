# Simple network remote control

import machineio as mio

network = mio.Network('192.168.0.5')

aduino = network.Device('firmata')

right = mio.Pin(aduino, 3, mio.OUTPUT, mio.SERVO, halt=lambda self: self(0))
left = mio.Pin(aduino, 5, mio.OUTPUT, mio.SERVO, halt=lambda self: self(0))

power = mio.Group(1)
power.add(right)
power.add(left)

power(10)
