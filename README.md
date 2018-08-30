# Machine IO

Unified GPIO functor interface engine.

## What is machineio?
 Interface Engine/Protocol Translator 
Want to use functional programming that's specific to your machine/robot?

Machineio is a library to help you create a single unified interface for all your GPIO!
for your machines that use one or more micro controllers.
It helps you quickly create your own functions (functors) for interfacing with hardware.
The specific micro controller(s) you choose to use can later be swapped out with simple
modifications of your functor library. Devices can be added and controlled over a network
with a few simple additions to your functor library. Translations and groups allow complete
customizations.


# Pin and Group functor model

Every motion control system is different in design and implementation.
Therefor every motion control system must have a different set of functions that create its library.
A huge majority of these systems use the same protocols and are fundamentally based on I/O pins.
A single pin almost never does all of what you need, groups of pins perform complex actions together.
This is a way to overcome both of these problems in a very elegant manner.
You create your own function interface library for your machine based on Pins, 
and Groups of Pins, and Groups of Groups.
This is done by creating a Device, Pin and Group objects and specifying a few modifying functions.
The only blocking call in a pin input. It waits to return it's value and should only take a 
fraction of a second even over a network. Pins in groups and can have time delays and
input pins can have callbacks added with keyword arguments. Controlling a device over a network
can be added by creating a Network object and passing it as a parameter to a device.

