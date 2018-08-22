# Simple network remote control

import machineio as mio

_network = mio.Network('192.168.0.13')

_arduino = _network.Device('firmata', client_name='phidi')

#right(-1 to 1)
right = mio.Pin(_arduino, 5, mio.OUTPUT, mio.Servo(),
                halt=lambda self: self(90),
                translate=lambda x: int(x * 90 + 90))

#left(-1 to 1)
left = mio.Pin(_arduino, 6, mio.OUTPUT, mio.Servo(),
               halt=lambda self: self(90),
               translate=lambda x: int(x * 90 + 90))

# move.mix(speed, turn)
# speed = percentage
# turn = differential percentage
mix = mio.Group(2)
mix.add(right, translate=lambda speed, rotation: speed - rotation/2)
mix.add(left, translate=lambda speed, rotation: speed + rotation/2)


