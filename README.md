# CDX-GreyCell-Client
2015 Grey Cell Client Code
Required components:
Python 2.7.4
RabbitMQ pika

Currently tested under windows 8, w/ Pika 0.9.14

Proposed Comms Protocol:
JSON Based, restricted to strings, integers and floats
1. ClientID: String (School-HostName)
2. AgeOff: String (YYYYMMDD-HHMMSSZ)
3. CommandID: Integer Associated with command module
4. TaskID: Integer defined by module
5. CommandData: Key Value array, defined by module
