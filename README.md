# CDX-GreyCell-Client<br>
2015 Grey Cell Client Code<br>
Required components:<br>
Python 2.7.4<br>
RabbitMQ pika<br>
<br>
Currently tested under windows 8, w/ Pika 0.9.14<br>
<br>
Proposed Comms Protocol:<br>
JSON Based, restricted to strings, integers and floats<br>
1. ClientID: String (School-HostName)<br>
2. AgeOff: String (YYYYMMDD-HHMMSSZ)<br>
3. CommandID: Integer Associated with command module<br>
4. TaskID: Integer defined by module<br>
5. CommandData: Key Value array, defined by module<br>
