.. MachineIO documentation master file, created by
   sphinx-quickstart on Fri Aug 24 09:39:03 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MachineIO's documentation!
=====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. warning:: Not for use on heavy machinery while in alpha.
.. warning:: Dry run your code prior to live testing.

About MachineIO
===============
A little about MachineIO
------------------------
MachineIO is a toolkit to help you create a functional interface to control GPIO.
for your machines that use one or more micro controllers.
It helps you quickly create your own functions (functors) for interfacing with hardware.
The specific micro controller(s) you choose to use can later be swapped out with simple
modifications of your functor library. Devices can be added and controlled over a network
with a few simple additions to your functor library.

Before you start
================
What you need to know to get started.

Functors
--------
What is a functor?
A functor is a class who's objects are meant to be called like a function.

Why not just functions?
Functions are great! Simple and effective. But having a entire library of functions with oddly specific names that require you to put in what pin you want to perfom the action every time gets tiresome and is hard to read. Also, if you change how a pin works you might have to change it a throughout your code.

Why not just classes?
Classes are good but end up getting complex and messy once the code gets too big. This gets extra bad in python because you might want to access members as well as functions for this or that.

Lambda Functions
----------------
A lambda function is simply an inline function.
It returns the result of the right hand side of the colon, while the left is used to define the arguments

Here is an example::

   lambda arg: arg*2

GPIO
----
General purpose input/output

Single pin types
----------------
Digital

Analog

PWM (pulse width modulation)

PPM (pulse-position modulation used on servos)


Getting Started
===============

The basics
----------
machineio.Pin(*device*, *pin_number*, *io_type_flag*, *data_type_flag*, ***keywords*)

**Device**
Devices are objects that represent a GPIO group. They are used as an address and protocol for each pin.

**Pin number**
this will be specific to the driver/protocol but should be referenced directly from the hardware's standard layout.
you should be able to look this up with "(your hardware's name) pin layout"

**modular IO flags**
mio.Input() and mio.Output()

**modular type flags**
mio.Digital() mio.Analog() mio.PWM() mio.PPM()

**keyword basics for safety and flexibility**
 * halt: a lambda function for safe shutdown
 * translate: a function for translation
 * limits: acceptable input range, as a tuple, before translation.

Examples
--------

**Creating a device and pin**::

   import machineio as mio
   device = mio.Device("test")
   pin5 = mio.Pin(device, 5, mio.Output(), mio.Digital(), halt=lambda self: self(False))

A device must first be created. in this example we use the "test" protocol that just prints out the changes.
The halt keyword is a function that returns the pin to it's default state. It is required for safety reasons.

**Using your pin**::

   import my_funclib as flib
   flib.pin5(True)

The control library is meant to be created in it's own file and imported into your code.

.. note:: For Linux users, your code will need to run in a privileged mode to access the usb ports.

Device
======
Devices are created with machineio.Device(*protocol_name*, *serial_port*)::

   import machineio as mio
   arduino_device = mio.Device('firmata', 'AMC0')

Protocols / Drivers
-------------------

**test**

prints the outputs.

**firmata**

A usb controlled firmware for the arduino.
You will need to look up how to load this firmware on to the arduino before you can start.

**raspberry-pi**

not implemented yet :(

Pin
===
A pin functor is created by after defining a device (or directly inside a group if you don't need direct access)
It represents everything about the pin down to a single parameter function for output, or none for input.
safety pin halt state should be some position that is safe for the machine to stop operation.

**pin1 = machineio.Pin**(*device*, *pin_number*, *io_type_flag*, *data_type_flag*, ***keywords*)::

   pin3 = machineio.Pin(arduino_device, 3, mio.Output(), mio.PPM(), halt=lambda self: self(90))

**pin1.state()**::

   current_value = pin3.state()

* Device: a device object
* Pin number: the pin number on the board.
* modular IO flags:
 * mio.Input()
 * mio.Output()
* modular type flags:
 * mio.Digital()
 * mio.Analog()
 * mio.PWM()
 * mio.PPM() - this is the PWM servo range (Pulse-position modulation)
* supported keywords:
 * halt: a lambda function for safe shutdown
 * translate: a function for translation
 * limits: acceptable input range, as a tuple (low,high), before translation.
 * translate_limits: acceptable input range, as a tuple (low,high), after translation.
 * callback: a function called with the pin object as a parameter upon updating state. Given (value, pin_obj) as arguments. Called asynchronously; however, it must not block the thread.


Group
=====
A single pin hardly ever does something you need by itself. Often pins must work together to accomplish a task.
A single pin can be used in more than one group; however, it will take on the state of the latest call made to it.
Groups can be have more then one parameter and a activation delay can be set for each pin if required. The delay is
handled as a non-blocking call, so it fires asynchronously from your code.

.. Note:: Groups can not be used for inputs (at the moment).

**A safety function should be defined for groups, while not necessary it is strongly recommended.**
The safety.stop() is a complex process you need to know.
All pins not in a group will be set to their halt/kill state
All pins that are in a group will ONLY have their group halt/stop function called.
For nested groups it will create a call chain top down.
A chain can be prevented from calling children by returning False on the groups halt/stop function.
For pins in more than one group whatever group it branches to first will stop it.
Further actions will be prevented until safety.Safe.proceed is True

machineio.Group(dimensions, limit=lambda x: True, **keywords)
 * RETURN: the Group functor/object
 * dimensions: int of how many arguments the group takes.
 * limit: a boolean return function to determine if the input is within the limits.
 * Keyword arguments:
  * objects: (not recommended use .add) a list of pins
  * translations: (not recommended use .add) a list of translation functions
  * delay: (not recommended use .add) a list of time delays in seconds\

Group_obj.add(pin_or_group, translation=lambda x: x, delay=None)
 * RETURN: None
 * pin_or_group: the pin or group object your adding
 * translate: the function that takes this (parent) Group's functor call args and returns the .add pin or groups args.
 * delay: when this (parent) Group is called it waits this amount of seconds before making the call to the .add group.

**Group_obj.state()**: the last known state of the group as the called tuple

Example::

   #Setup
   import machineio as mio
   device = mio.Device('firmata')
   pin3 = machineio.Pin(arduino_device, 3, mio.Output(), mio.PPM(), halt=lambda self: self(90))
   pin5 = machineio.Pin(arduino_device, 5, mio.Output(), mio.PPM(), halt=lambda self: self(90))
   mixed = mio.Group(2, lambda x,y: x+y <= 180)
   mixed.add(pin3, translate=lambda x,y: x)
   mixed.add(pin5, translate=lambda x,y: y, delay=.25)

   #Use
   mixed(90,90)
   assert mixed.state() == (90,90)

Network
=======
Encryption is a part of how the network functions, it should not be disabled.

Definitions
 * Server: the machineio/scripts/server.py script
 * Client: the machineio/scripts/client.py script
 * Controller: the Network object created in your code. (also technically a client)

Setup
-----
1. generate all the required key files
  1. to do this use the make.py script with each client and controller name as an argument
2. distribute the key files to their intended hosts
  1. copy the "controller.key" file to where your running your code.
  2. copy any other named file to it's equally named client.
3. start the server.py script
  1. with ALL the required key files still with server.py start server.py
4. connect the client.py script to the server
  1. with ONLY the key file with the same name as the client, start client.py
5. run your code.
  1. with ONLY the controller.key file in your execution directory start your program.

The client and server are hands off. You should only need to start them up and they will do everything else.
This includes recovery on errors and reset on restart of your code.

Code
----
.. Note:: Halt must be a lambda function for network to operate properly at this time.

.. Note:: At the moment, only pins (not groups) are given to the client. Stop will not work properly on link_failure.

Before creating a network device you must create a network.
 * ctrl_net = machineio.Network(host, port=20801, key_file='controller.key')

Once you have a network you can create a device
 * ctrl_net.Device(protocol, serial_com_port, client_name='default', linkfailure=machineio.kill)

If you need to transport some data from or to device client you can do that. (This will likely change)
 * ctrl_net.send('data', 'controller', 'to_client_name', {'exec': code})

If you would like to reinitialize the client without restarting it send the command
 * ctrl_net.send('notice', 'controller', client_name, 'reset')

Very little changes in your code. You add a network object at the top of your code, and change your device to a network
device. A network device is just like a regular device, only it needs an extra keyword argument "client_name"

Example::

   #Setup
   import machineio as mio
   network = mio.Network('192.168.0.5')
   device = network.Device('firmata', client_name='default')
   pin3 = machineio.Pin(arduino_device, 3, mio.Output(), mio.PPM(), halt=lambda self: self(90))
   pin5 = machineio.Pin(arduino_device, 5, mio.Output(), mio.PPM(), halt=lambda self: self(90))
   mixed = mio.Group(2, lambda x,y: x+y <= 180)
   mixed.add(pin3, translate=lambda x,y: x)
   mixed.add(pin5, translate=lambda x,y: y, delay=.25)

   #Use
   mixed(90,90)
   assert mixed.state() == (90,90)


Safety
------
If the only controller disconnects the server will tell all clients to halt.
If a client disconnects the server will call the Network.link_failure()
given by the link_failure(client_name) keyword. If not given it will do nothing.
If one of multiple controllers disconnects it will call
Network.controller_link_failure(self, controller_name) given as a keyword.
If that does not exist it will do nothing.