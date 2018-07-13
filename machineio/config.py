import time
import sys
from pin import Pin


def servo():
    '''
    Helper for limits and translations
    :param servo_pin:
    :return:
    '''
    print('===Servo auto configurator===')
    print('WARNING: there are is no emergency safety shutdown in place... stay clear of machinery')
    device = input('What device is the servo connected to?:')
    pin = int(input('What pin number is the servo using on the device?:'))
    if input('Does your servo use a standard PWM/PPM range?(Y/N):').lower() in 'yes':
        print('===Hardware Values===')
        print('A start position of 90 should be 1/2 way on a 180 degree servo')
        pos = int(input('What should be the start position? 0 is recommended:'))
        print('Enter a number (or nothing for 5) to jump by that amount.(negatives ok)')
        print('Enter a letter to set: l to set low limit, h to set high limit, z to set as zero, q to quit')
        print('Note: do not enter a zero if there is at or beyond a limit')
        hard_low = 0
        hard_high = 180
        zero = 0
        servo = Pin(device, pin, 'OUTPUT', 'SERVO', halt=True)
        while True:
            val = input('Servo: ')
            if not val:
                pos += 5
            elif val.isdigit():
                pos += int(val)
            elif val.isalpha():
                if val.lower() in 'high':
                    hard_high = pos
                elif val.lower() in 'low':
                    hard_low = pos
                elif val.lower() in 'zero':
                    zero = pos
                elif val.lower() in 'quit':
                    break
            servo(pos)
        print('===Software Values===')
        print('This maps the desired input of your function to the hardware values')
        print('This uses the zero from your hardware configuration!')
        is_linear = input('Is the mapping linear (Y/N):')
        if is_linear.lower() in 'yes':
            low = int(input('What is the lowest value (will be negative if zero is higher then lowest)?:'))
            high = int(input('What is the highest value?:'))
            translation = (hard_high - hard_low) / (high - low)
            offset = hard_low + zero
            func = 'lambda x: '+str(translation)+' * x + '+str(offset)
        else:
            print('Example of a lambda function: "lambda x: math.sin(x)+7*math.pi"')
            func = input('please write a translation lambda function: ')
        halt = "lambda self: self("+input('what should be the value called on this servo when safety.stop() or safety.kill() are called:')+")"
        print('===Complete!===')
        print('Copy this into the __init__.py code')
        print("Pin("+device+", "+pin+", 'OUTPUT', 'SERVO', limits=("+hard_low+", "+hard_high+"), halt="+halt+", translation="+func+")")
    else:
        print('Not auto-configurable at this time')


if __name__ == '__main__':
    func = sys.argv[1]
    if func == 'servo':
        servo()

