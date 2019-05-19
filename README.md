# Raspberry Pi sim800l gsm module

## setup

## Usage examples

```python 
from sim800l import SIM800L
sim800l=SIM800L('/dev/serial0')
```
#### send sms
```python
sms="Hello there"
#sim800l.send(dest.no,sms)
sim800l.send('2547xxxxxxxx',sms)
```
#### read sms
```python
#sim800l.read_sms(id)
sim800l.read_sms(id)
```