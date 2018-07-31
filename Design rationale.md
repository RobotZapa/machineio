# Design rationale
**If there is something you don't understand you might find your answers here.**  


If you do not and they belong here please send me a message to the email in the setup.py

### The idea
I hope that this project becomes a beautifully simple, yet powerful, interface creation tool
for robotics and machines.

## Device
A device is a class with a connect, config, and io methods. (Refer to test for the simplest form)
These classes for any given protocol are stored in /machineio/drivers you can create your own.
The actual call made to machineio.Device is a _duck typed_ function that returns an object
from the correct protocol. If it does not exist it throws an error.

## Network
You defined a device normally while passing it a simple network object.
The device is then replaced with a network class instead of one of the drivers.
The network class on creation connects to the server.py script
where you have hopefully connect clients.py to the server already.
It then sends the commands to the client of the name you gave to the network object.
commands are exec strings at the moment.  In the future I hope to find a better way
to accomplish this.  
#### Safety
When a pin configures over the network it attempts a reconstruction
of the safety function. This might fail if it is compiled code that has no source 
available. If this is the case it will throw an error about halt not being
available automatically. If this happens you can manually configure a halt on the
remote system by **NOT YET FINISHED.**

