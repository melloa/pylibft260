from enum import Enum
from ctypes import wintypes
import ctypes
import os

DEFAULT_FTDI_VID = 0x0403
DEFAULT_FTDI_PID = 0x6030
DEFAULT_BAUDRATE = 9600
DEFAULT_I2C_CLOCK_SPEED = 400  # kHz

I2C_START_ADDRESS = 0x08
I2C_END_ADDRESS = 0x7C


class I2C_FLAG(Enum):
    NONE = 0x00
    START = 0x02
    REPEATED_START = 0x03
    STOP = 0x04
    START_AND_STOP = 0x06


def CHECK_STATUS(status, info=None):
    if status != STATUS.OK.value:
        raise FT260Exception("Failed to {}: {}".format(info, STATUS(status)))


class FT260Exception(Exception):
    pass


class FT260:
    def __init__(self, path="LibFT260.dll"):
        if not os.path.exists(path):
            raise FileNotFoundError("LibFT260.dll not found!")
        self._lib = ctypes.windll.LoadLibrary(path)
        self.device = ctypes.c_void_p()

    def open(self, vid=DEFAULT_FTDI_VID, pid=DEFAULT_FTDI_PID, device_number=0):
        status = self._lib.FT260_OpenByVidPid(
            wintypes.WORD(vid),
            wintypes.WORD(pid),
            wintypes.DWORD(device_number),
            ctypes.byref(self.device),
        )
        CHECK_STATUS(status, info="open device")
        self.i2c = self.I2C(self)

    class I2C:
        def __init__(self, parent):
            self.parent = parent
            self.active = False

        def activate(self, clock_speed=DEFAULT_I2C_CLOCK_SPEED):
            status = self.parent._lib.FT260_I2CMaster_Init(
                self.parent.device, ctypes.c_uint32(clock_speed)
            )
            CHECK_STATUS(status, info="initialize I2C")
            self.active = True

        def _check_status(self):
            errors = []
            status = ctypes.c_uint8(0)
            self.parent._lib.FT260_I2CMaster_GetStatus(
                self.parent.device, ctypes.byref(status)
            )
            if status == STATUS.OK.value:
                return
            if status & (1 << 0):
                errors.append("Controller Busy")
            if status & (1 << 1):
                errors.append("Error Condition")
            if status & (1 << 2):
                errors.append("Target Address Not Acknowledged")
            if status & (1 << 3):
                errors.append("Data Not Acknowledged")
            if status & (1 << 4):
                errors.append("Arbitration Lost")
            if status & (1 << 5):
                errors.append("Controller Idle")
            if status & (1 << 6):
                errors.append("Bus Busy")
            raise FT260Exception("I2C STATUS Error: {}".format(", ".join(errors)))

        def write(self, slave_address, data, flag=I2C_FLAG.START_AND_STOP):
            if not self.active:
                self.activate()
            bytes_written = ctypes.c_ulong(0)
            data_to_be_written = ctypes.create_string_buffer(data)
            CHECK_STATUS(
                self.parent._lib.FT260_I2CMaster_Write(
                    self.parent.device,
                    ctypes.c_uint8(slave_address),
                    flag,
                    ctypes.cast(data_to_be_written, ctypes.c_void_p),
                    wintypes.DWORD(len(data)),
                    ctypes.byref(bytes_written),
                )
            )
            assert len(data) == bytes_written.value, "I2C writing timed out!"
            self._check_status()

        def read(self, slave_address, length, flag=I2C_FLAG.START_AND_STOP):
            if not self.active:
                self.activate()
            bytes_actually_read = ctypes.c_ulong(0)
            buffer = ctypes.create_string_buffer(length + 1)
            CHECK_STATUS(
                self._lib.FT260_I2CMaster_Read(
                    self.parent.device,
                    ctypes.c_uint8(slave_address),
                    flag,
                    ctypes.cast(buffer, ctypes.c_void_p),
                    wintypes.DWORD(length),
                    ctypes.byref(bytes_actually_read),
                )
            )
            assert length == bytes_actually_read.value, "I2C reading timed out!"
            self._check_status()
            return buffer.raw

        def reset(self):
            CHECK_STATUS(
                self._lib.FT260_I2CMaster_Reset(
                    self.parent.device
                )
            )



class STATUS(Enum):  # CtypesEnum):
    OK = 0
    INVALID_HANDLE = 1
    DEVICE_NOT_FOUND = 2
    DEVICE_NOT_OPENED = 3
    DEVICE_OPEN_FAIL = 4
    DEVICE_CLOSE_FAIL = 5
    INCORRECT_INTERFACE = 6
    INCORRECT_CHIP_MODE = 7
    DEVICE_MANAGER_ERROR = 8
    IO_ERROR = 9
    INVALID_PARAMETER = 10
    NULL_BUFFER_POINTER = 11
    BUFFER_SIZE_ERROR = 12
    UART_SET_FAIL = 13
    RX_NO_DATA = 14
    GPIO_WRONG_DIRECTION = 15
    INVALID_DEVICE = 16
    INVALID_OPEN_DRAIN_SET = 17
    INVALID_OPEN_DRAIN_RESET = 18
    I2C_READ_FAIL = 19
    OTHER_ERROR = 20
