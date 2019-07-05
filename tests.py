import unittest, time, os
import machineio as mio


class TestOutput(unittest.TestCase):
    def setUp(self):
        mio.Safe.SUPPRESS_WARNINGS = True
        self.device = mio.Device('test')
        self.pin_digital = mio.Pin(self.device, 1, mio.Output(), mio.Digital(), halt=lambda self: self(False))
        self.pin_pwm = mio.Pin(self.device, 2, mio.Output(), mio.PWM(), limits=(-90, 90), halt=lambda self: self(0), translate=lambda x: x/2, translation_limits=(0, 100))
        self.pin_servo = mio.Pin(self.device, 3,  mio.Output(), mio.PPM(), limits=(0, 180), halt=lambda self: self(0), translate=lambda x: x+90)
        self.pin_analog = mio.Pin(self.device, 4, mio.Output(), mio.Analog(), limits=(0, 5), halt=lambda self: self(0), translate=lambda x: x*10, translate_limts=(0, 100))

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
        with self.assertRaises(ValueError):
            self.pin_pwm(200)

    def test_servo(self):
        self.pin_servo(0)
        self.assertEqual(self.pin_servo.state, 90)
        with self.assertRaises(ValueError):
            self.pin_servo(-100)

    def test_analog(self):
        self.pin_analog(1.23)
        self.assertEqual(self.pin_analog.state, 12.3)

class TestInputs(unittest.TestCase):
    pass#todo test callback


class TestGroup(unittest.TestCase):
    def setUp(self):
        mio.Safe.SUPPRESS_WARNINGS = True
        self.device = mio.Device('test')
        self.pin2 = mio.Pin(self.device, 2, mio.Output(), mio.Digital(), halt=lambda self: self(False))
        self.pin1 = mio.Pin(self.device, 1, mio.Output(), mio.PWM(), halt=lambda self: self(0))
        self.pin3 = mio.Pin(self.device, 3, mio.Output(), mio.PPM(), halt=lambda self: self(90))

        self.main = mio.Group(1, halt=lambda self: self(0))
        self.main.add(self.pin1)
        self.main.add(self.pin2, translate=lambda x: x>0)

        self.alt = mio.Group(2)
        self.alt.add(self.pin3, translate=lambda x, y: x)
        self.alt.add(self.pin2, translate=lambda x, y: y)

        self.timed = mio.Group(1)
        self.timed.add(self.pin2, delay=1)

    def test_halt(self):
        self.pin2(True)
        self.pin1(20)
        self.pin3(20)
        mio.stop('Testing group halt')
        self.assertEqual(self.pin1.state, 0)
        self.assertEqual(self.pin2.state, False)
        self.assertEqual(self.pin3.state, 90)
        self.assertWarns(RuntimeWarning, self.main(10))
        mio.Safe.proceed = True


    def test_main_group(self):
        self.main(0)
        self.assertEqual(self.pin1.state, 0)
        self.assertEqual(self.pin2.state, False)
        self.main(10)
        self.assertEqual(self.pin1.state, 10)
        self.assertEqual(self.pin2.state, True)

    def test_alt_group(self):
        self.pin2(False)
        self.alt(0, True)
        self.assertEqual(self.pin3.state, 0)
        self.assertEqual(self.pin2.state, True)
        self.alt(10, False)
        self.assertEqual(self.pin3.state, 10)
        self.assertEqual(self.pin2.state, False)

    def test_timed(self):
        self.pin2(False)
        self.timed(True)
        self.assertEqual(self.pin2.state, False)
        time.sleep(1.2)
        self.assertEqual(self.pin2.state, True)

class TestNetwork(unittest.TestCase):
    def setUp(self):
        input('Please startup your server.py and client.py (default name) scripts...')
        self.network = mio.Network('127.0.0.1')
        self.device = self.network.Device('test')
        # connect a client

    def test_all(self):
        self.pinTest1 = mio.Pin(self.device, 2, mio.Output(), mio.Digital(), halt=lambda self: self(True))
        self.pinTest1(False)
        self.pinTest2 = mio.Pin(self.device, 1, mio.Input(), mio.PWM(), halt=lambda x: x(0),
                                callback=lambda val, pin: print(f'callback value {val} on {pin.pin}'))
        self.network.send('default', exec='device.test_input(pin1)')
        time.sleep(1)
        if input('Error test y/(n):').lower() in 'yes':
            try:
                self.network.send('default', exec='raise Exception("test error")')
            except:
                print('Restart the test to make sure the client is ok.')
        print('You may disconnect the server to test client halt now.')
        time.sleep(10)
        # after tests it will disconnect and the networks halt will be fired.

if __name__ == '__main__':
    unittest.main()