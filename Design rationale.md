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
You must create a network object that spools up a receiver thread.
This network object is not name clutter though, because data can be sent/retrieved
over the connection. The encryption is not point to point, the server does processing
and routing of the packets, ultimately you have to have complete trust in the server.
There can be a separate server for each client or one server hosted on the controller,
or hosted somewhere else.
###### How it works
Commands are sent using exec for non-returnables or eval for returnable.
Code strings are generated on the controller network pseudo device. And sent off 
with an encrypted pickle. The server has to figure out where this pickle goes so
it opens it up to look. Also each connection to the server uses a different key file
so once it knows where that pickle is going it encrypts it for the destination and
sends it on its way.

#### Safety
When a pin configures over the network it attempts a reconstruction
of the safety function. This might fail if it is compiled code that has no source 
available. If this is the case it will throw an error about halt not being
available automatically. If this happens you can manually configure a halt on the
remote system by sending a data function containing a string defining a halt function

#### Security
The servers and clients will all be the latest implementation, they may 
not be backwards compatible. If so they will reside in scripts/archives 
unless they are deemed insecure. Pickles are used for the key files; however,
this should not be a security issue. As the clients in question are already 
under direct control of the creator of the pickle.
###### v0.1
Links work by encrypting each line separately from other links. The server acts as a router.
Each host has a key file. The server has, and generates all key files. You must manually 
distribute the files to the proper clients. These files are versioned at the top. The server
will securely generate the files if they are not present. It uses AES-GCM encryption.