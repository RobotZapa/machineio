import machineio as mio

aduino = mio.Device('firmata')

right = mio.Pin(aduino, 3, 'OUTPUT', 'SERVO', halt=lambda self: self(0))
left = mio.Pin(aduino, 5, 'OUTPUT', 'SERVO', halt=lambda self: self(0))

power = mio.Group(1)
power.add(right)
power.add(left)

