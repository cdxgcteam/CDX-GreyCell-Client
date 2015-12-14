# CDX-GreyCell-Client<br>
2015 Grey Cell Client Code<br>
Required components:<br>
Python 2.7.4<br>
RabbitMQ pika<br>
<br>
Currently tested under windows 8, w/ Pika 0.9.14<br>
<br>

ClientID == SchoolName_Hostname
SpecialNames:
All_All
SchoolName_All

Proposed Comms Protocol:<br>
JSON Based, restricted to strings, integers and floats<br>
1. ClientID: String (School-HostName)<br>
2. TaskCreateDT: String (YYYYMMDDZHHMMSS.SSS) <withheld><br>
3. ModuleID: Integer Associated with command module<br>
4. TaskRef: Integer defined by module<br>
5. CommandData: Key Value array, defined by module<br>


Response:
1. ClientID: String (School-HostName)<br>
2. ModuleID: Integer Associated with command module<br>
3. TaskRef: Integer defined by module<br>
4. TaskRecieveTime: String (YYYYMMDDZHHMMSS.SSS) <br>
5. TaskCompleteTime: String (YYYYMMDDZHHMMSS.SSS) <br>
6. ResponseData: Key Value array, defined by module<br>


Tasks:
TaskId {Selemnium}
TaskingObj
	cmd {execute}
	url
	worktime
	
	
TaskId {Diagnostics}

TaskId {Install}
TaskingObj
	type
	filename
	data

TaskId {Pause}
TaskingObj
	time

TaskId {Quit}

TaskId {Reload} # Reloads all modules