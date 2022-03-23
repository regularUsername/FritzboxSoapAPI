# Usage

Begin by importing Services and creating an instance of it with your FritzBox credentials.
```python
>>> from FritzboxSoapAPI import Services
>>> s = Services("username", "password")
```

## Exploring services and methods of the API

Use .listServices() to get a list of available services in the API.
```python
>>> s.listServices()
```
```
['DeviceInfo',
 'DeviceConfig',
 'Hosts'
 ...
]
```

Use .listMethod() on a service to get all methods of that service.
```python
>>> s.Hosts.listMethods()
```
```
['GetHostNumberOfEntries',
 'GetSpecificHostEntry',
 'GetGenericHostEntry',
 ...
]
```

Get signature of specific method in a service with .methodHelp("methodname").
```python
>>> s.Hosts.methodHelp("GetSpecificHostEntry")
```
```
GetSpecificHostEntry

:param NewMACAddress
:return {NewIPAddress, NewAddressSource, NewLeaseTimeRemaining, NewInterfaceType, NewActive, NewHostName}
```

## Retrieving data from the FritzBox
Parameters must be passed as keyword arguments.
```python
>>> s.Hosts.GetSpecificHostEntry(NewMACAddress="11:22:33:AA:BB:CC")
```
```
{'NewIPAddress': '192.168.0.1',
 'NewAddressSource': 'DHCP',
 'NewLeaseTimeRemaining': 0,
 'NewInterfaceType': 'Ethernet',
 'NewActive': 1,
 'NewHostName': 'someHostname'}
 ```