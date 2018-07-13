import unittest
import machineio as mio


class TestOutput(unittest.TestCase):
    def setUp(self):
        mio.Safe.SUPPRESS_WARNINGS = True
        self.device = mio.Device('test')
        self.pin_digital = mio.Pin(self.device, 1, 'OUTPUT', 'DIGITAL', halt=lambda self: self(False))
        self.pin_pwm = mio.Pin(self.device, 2, 'OUTPUT', 'PWM', limits=(-90, 90), halt=lambda self: self(0), translate=lambda x: x/2, translation_limits=(0, 100))
        self.pin_servo = mio.Pin(self.device, 3, 'OUTPUT', 'SERVO', limits=(0, 180), halt=lambda self: self(0), translate=lambda x: x+90)
        self.pin_analog = mio.Pin(self.device, 4, 'OUTPUT', 'ANALOG', limits=(0, 5), halt=lambda self: self(0), translate=lambda x: x*10, translate_limts=(0, 100))

    def test_halt(self):
        self.pin_digital(True)
        self.assertEqual(self.pin_digital.state, True)
        mio.kill(f'Running unit testing with device {self.device.protocol}')
        self.pin_digital(False)
        self.assertEqual(self.pin_digital.state, False)
        self.assertWarns(RuntimeWarning, self.pin_digital(True))
        mio.Safe.proceed = True

    def test_digital(self):
        self.pin_digital(True)
        self.assertEqual(self.pin_digital.state, True)
        self.pin_digital(False)
        self.assertEqual(self.pin_digital.state, False)

    def test_pwm(self):
        self.pin_pwm(10)
        self.assertEqual(self.pin_pwm.state, 5)
        self.assertRaises(ValueError, self.pin_pwm(200))

    def test_servo(self):
        self.pin_servo(0)
        self.assertEqual(self.pin_servo.state, 90)
        self.assertRaises(ValueError, self.pin_servo(-100))

    def test_analog(self):
        self.pin_analog(1.23)
        self.assertEqual(self.pin_analog.state, 12.3)

class TestInputs(unittest.TestCase):
    pass

class TestGroup(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()