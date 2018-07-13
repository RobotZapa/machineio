# Machine IO

**Do not use machineio on heavy machinery while in alpha**  
**Use caution and do dry runs before live testing**


# Pin and Group functor model

Every motion control system is different in design and implementation.
Therefor every motion control system must have a different set of functions that create its library.
A huge majority of these systems use the same protocols and are fundamentally based on I/O pins.
A single pin almost never does all of what you need, groups of pins perform complex actions together.
This is a way to overcome both of these problems in a very elegant manner.
You create your own function interface library for your machine based on Pins, 
and Groups of Pins, and Groups of Groups.
This is done by creating a Device, Pin and Group objects and specifying a few modifying functions.
They are all non-blocking calls and can have time delays and callbacks added with keyword arguments!

## Safety

halt functions are _required for all pins_ and _recommended for all groups_.
These calls will prevent any further calls from being executed and log the safety halt reason
If you are going to implement your own system for this you may use Safe.SUPPRESS_WARNINGS
All machineio commands must be executed in the same thread to run safely at this time.

 * #### machineio.stop(reason_string)  
    prevents further actions.
    halts all groups and all pins not in a group.
    logs stop reason.
 * #### machineio.kill(reason_string)  
    prevents further actions.
    halts all pins & logs reason.
    logs kill reason.
 * #### machineio.Safe.proceed = True  
    To continue normal operation after a halt has been called.

## Device
The device is where the machineio package connects to hardware via plugins (hopefully directly in the future)
before you define any pins you create the device objects with the protocol you want to use
The device object is only used to pass as the device parameter on a Pin.
 
Supported Protocols at this time include:
  * Test (prints the outputs/input the inputs)
  * Firmata
  
  
  * #### machineio.Device(protocol_name_string)  
    - RETURN: the device object to use when creating pins
    - Keyword arguments:  
        + device_port: The usb port the device is using.

## Pin

A pin functor is created by after defining a device (or directly inside a group if you don't need direct access)
It represents everything about the pin down to a single parameter function.
safety pin halt state should be some position that is safe for the
Callback is activated any time the pin state changes.

  * #### machineio.Pin(device_obj, pin_int, io_string, type_string, **keyword_args)  
    creates the pin functor. The pin is now a function that can be called, 
    and an object that can be added to a group.
    - RETURN: the Pin functor/object
    - device_obj: See Device
    - pin_int: The pin number of the device (determined by protocol)
    - io_string: "Input" | "Output" | "True"
    - type_string:  
        **Note**: Not every type pin can be every type.  
        Some devices will not support certain types at all.
      + "Digital"
      + "Analog"
      + "PWM"
      + "SERVO"
    - Keywords arguments:  
      + halt: (required) A function to call with the pin object as the argument
        when the pins needs to be in a safe state.
      + limits: tuple (low, high) where, low <= valid <= high. After translation
      + translate: A function used for modifying the pin's functor input.
      + translate_limits: tuple (low, high) where, low <= valid <= high, Before translation
      + callback: A function to call when the state of the pin changes. 
        Given (value, pin_obj) as arguments. 
        Called asynchronously.
  * #### Pin_obj.state  
    The value of the last known state of the pin.  Does not use the Pin_obj() call.

## Group
A group is a cluster of pins that work together in some way.  A single pin can be used in more than one group!
Pins can be defined to trigger after some time, this time can be different for each pin in the group. This is
handled as a non-blocking call, so it fires asynchronously from your code. Groups should not be used for inputs.

**A safety function should be defined for groups, while not necessary it is strongly recommended.**
The safety.stop() is a complex process you need to know.
All pins not in a group will be set to their halt/kill state
All pins that are in a group will ONLY have their group halt/stop function called.
For nested groups it will create a call chain top down.
A chain can be prevented from calling children by returning False on the groups halt/stop function.
For pins in more than one group whatever group it branches to first will stop it.
Further actions will be prevented until safety.Safe.proceed is True

  * ####machineio.Group(dimensions, limit=lambda x: True, **keyword_args)
    - RETURN: the Group functor/object
    - dimensions: int of how many arguments the group takes.
    - limit: a boolean return function to determine if the input is within the limits.
    - Keyword arguments:
        + objects: (not recommended use .add) a list of pins
        + translations: (not recommended use .add) a list of translation functions
        + delay: (not recommended use .add) a list of time delays in seconds
  * ####Group_obj.add(pin_or_group, translation=lambda x: x, delay=None)
    - RETURN: None
    - pin_or_group: the pin or group object your adding
    - translation: the function that takes this (parent) Group's functor call args and 
        returns the .add pin or groups args.
    - delay: when this (parent) Group is called it waits this amount of seconds
        before making the call to the .add group.
        

##Configuration
###Servos
Servos need a to be calibrated to get the desired results quite often. 
So I've added a tool to help you configure your servos.

**from the console:** Python3.7 machineio/machineio/config.py servo