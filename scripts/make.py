import sys, os
# for a reason as to why imports of siblings is so ugly
# see https://mail.python.org/pipermail/python-3000/2007-April/006793.html
sys.path.insert(0, os.path.abspath('..'))
import machineio

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for client_name in sys.argv[:1]:
            print(f'Creating key for "{client_name}"')
            machineio.network.Crypto.generate_keyfile(client_name+'.key')
    else:
        print('Syntax is: make.py controller client_name_1 client_name_2')
