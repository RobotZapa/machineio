Welcome to MachineIO's developer documentation!
===============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:
    index

The Goal
--------
To have a simple, stable and safe functor tooling for using GPIO.
The user will create their own interface for interacting with their project via functors.
These functors should be easy to read and self explanatory to look at.
These functors keywords and formatting should be as consistent as possible.

Project parts
=============

Device
------

The protocol driver
+++++++++++++++++++
This is where the unified interface diverges into separate hardware controls.
It loads up the Device class for the specific protocol from it's named driver file.
This way device support can be added simply by dropping in new files.

Pins
----

Groups
------

Network
=======

protocol
--------
the packet is list containing [type, source, dest, payload]
the payload is dict

currently it's packed using pickle (not a security risk because system are already under direct control)

Types are: 'notice', 'data', 'command', 'response' and 'callback'

* command
 * {'action': 'exec', 'code': <code_string>}
 * {'action': 'eval', 'code': <code_string>, 'future_id': <future_id>} this will send back a 'response' with the value
* data
 * {'action': 'exec', 'code': <code_string>}
 * {'action': 'eval', 'code': <code_string>, 'future_id': <future_id>} this will send back a 'response' with the value
* response
 * {'future_id': <future_id>, 'state': <future_value>}
* callback
 * {'pin': <int>, 'value': <new_value>}
* notice
 * client
  * {'reason': 'halt'}
  * {'reason': 'reset'}
  * {'reason': 'link_failure'}
 * controller
  * {'reason': 'link_failure', 'info': <client_name>}
  * {'reason': 'controller_link_failure', 'info': <controller_name>}
  * {'reason': 'error', 'info': <error information>}

to keep the connection alive to each client a b'O' can be sent from the client and a b'K' will be returned by the server
