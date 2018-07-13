from machineio.group import Group
from machineio.pin import Device
from machineio.pin import Pin
from machineio.safety import Safe
from machineio.safety import stop, kill
import math

arduino = Device('firmata')

_off = lambda self: self(False)
_zero = lambda self: self(0)

speed_pin = Pin(arduino, 3, 'OUTPUT', 'PWM', halt=_zero)

forward_right = Group(1)
forward_right.add(Pin(arduino, 2, 'OUTPUT', 'DIGITAL', halt=_off))
forward_right.add(Pin(arduino, 4, 'OUTPUT', 'DIGITAL', halt=_off))

forward_left = Group(1)
forward_left.add(Pin(arduino, 7, 'OUTPUT', 'DIGITAL', halt=_off))
forward_left.add(Pin(arduino, 8, 'OUTPUT', 'DIGITAL', halt=_off))

backward_right = Group(1)
backward_right.add(Pin(arduino, 19, 'OUTPUT', 'DIGITAL', halt=_off))
backward_right.add(Pin(arduino, 18, 'OUTPUT', 'DIGITAL', halt=_off))

backward_left = Group(1)
backward_left.add(Pin(arduino, 17, 'OUTPUT', 'DIGITAL', halt=_off))
backward_left.add(Pin(arduino, 16, 'OUTPUT', 'DIGITAL', halt=_off))

forward_pins = Group(1)
forward_pins.add(forward_right)
forward_pins.add(forward_left)

backward_pins = Group(1)
backward_pins.add(backward_right)
backward_pins.add(backward_left)

speed = Group(1, limit=lambda x: -100 <= x <= 100)
speed.add(speed_pin, translation=lambda x: abs(x))
speed.add(forward_pins, translation=lambda x: x > 0)
speed.add(backward_pins, translation=lambda x: x < 0)

_degrees = lambda x: x-90
servo_fr = Pin(arduino, 5, 'OUTPUT', 'SERVO', limits=(-90, 90), halt=_zero, translation=_degrees)
servo_fl = Pin(arduino, 6, 'OUTPUT', 'SERVO', limits=(-90, 90), halt=_zero, translation=_degrees)
servo_br = Pin(arduino, 9, 'OUTPUT', 'SERVO', limits=(-90, 90), halt=_zero, translation=_degrees)
servo_bl = Pin(arduino, 10, 'OUTPUT', 'SERVO', limits=(-90, 90), halt=_zero, translation=_degrees)

steer = Group(1)
steer.add(servo_fr)
steer.add(servo_fl, translation=lambda x: -x)
steer.add(servo_br)
steer.add(servo_bl, translation=lambda x: -x)

drive = Group(2, limit=(lambda x: -100 <= x <= 100, lambda y: -45 <= y <= 45))
drive.add(speed, translation=lambda x, y: x)
drive.add(steer, translation=lambda x, y: y)

point_turn = Group(1, limit=lambda x: -100 <= x <= 100)
point_turn.add(servo_fr, translation=lambda x: 45)
point_turn.add(servo_fl, translation=lambda x: 45)
point_turn.add(servo_br, translation=lambda x: 45)
point_turn.add(servo_bl, translation=lambda x: 45)
point_turn.add(speed_pin, delay=0.5)
point_turn.add(forward_right, translation=lambda x: x > 0)
point_turn.add(forward_left, translation=lambda x: x < 0)
point_turn.add(backward_right, translation=lambda x: x < 0)
point_turn.add(backward_left, translation=lambda x: x > 0)