# pyLibFT260 - Python Wrapper for FT260
Currently a work-in-progress and untested!
## Requirements
LibFT260 - This is a free download from FTDI found [here](https://ftdichip.com/wp-content/uploads/2021/04/LibFT260-v1.1.4.zip) and the DLL should be placed in the root directory of this library. Alternatively, you can specify a path in your code if you have LibFT260 in a different location.
## Usage
Example application to talk to a device on address `0x30`
```
from ft260 import FT260

TARGET_ADDRESS = 0x30

device = FT260()
device.open()
address_on_bus = device.i2c.scan()
if TARGET_ADDRESS in address_on_bus:
    device.i2c.write(TARGET_ADDRESS, length=2)
