import serial
import struct 
import serial.threaded
import time 

class DgusProtocol(serial.threaded.Protocol):
    START_1 = b'\x5a'
    START_2 = b'\xa5'
    PENDING_START_1 = 0
    PENDING_START_2 = 1
    PENDING_SIZE = 2
    PENDING_BODY = 3

    READ_VP_CMD = 0x83
    WRITE_VP_CMP = 0x82

    def __init__(self, callback):
        self._buf = bytearray()
        self._transport = None
        self._state = DgusProtocol.PENDING_START_1
        self._pending_body_size = 0
        self._callback = callback

    def connection_made(self, transport):
        self._transport = transport

    def connection_lost(self, exc):
        self._transport = None
        self._state = DgusProtocol.PENDING_START_1
        self._buf.clear()
        super(DgusProtocol, self).connection_lost(exc)

    def handle_packet(self, msg):
        cmd = msg[0]
        if cmd == DgusProtocol.READ_VP_CMD:
            vp, _, value = struct.unpack_from('>hbh', msg, 1)
            self._callback(vp, value)
            
    def data_received(self, data):
        for byte in serial.iterbytes(data):
            if self._state == DgusProtocol.PENDING_START_1 and byte == DgusProtocol.START_1:
                self._state = DgusProtocol.PENDING_START_2
            elif self._state == DgusProtocol.PENDING_START_2 and byte == DgusProtocol.START_2:
                self._state = DgusProtocol.PENDING_SIZE
            elif self._state == DgusProtocol.PENDING_SIZE:
                self._pending_body_size = byte[0]
                self._state = DgusProtocol.PENDING_BODY
            elif self._state == DgusProtocol.PENDING_BODY:
                self._buf.extend(byte)
                if len(self._buf) == self._pending_body_size:
                    self.handle_packet(self._buf)
                    self._buf.clear()
                    self._state = DgusProtocol.PENDING_START_1
            else:
                # error in parsing, reset state
                self._state = DgusProtocol.PENDING_START_1

    def request_vp(self, vp):
        HEADER = 0x5aa50483
        WORDS_TO_READ = 1
        message = struct.pack('>iHb', HEADER, vp, WORDS_TO_READ)
        self._transport.write(message)
        self._transport.serial.flush()
        

    def write_vp(self, vp, value):
        HEADER = 0x5aa50582
        message = struct.pack('>iHh', HEADER, vp, value)
        self._transport.write(message)
        self._transport.serial.flush()


def create_protocol(port_name, baudrate, callback):
    ser = serial.Serial(port_name, baudrate)
    proto = serial.threaded.ReaderThread(ser, lambda:DgusProtocol(callback))
    proto.start()
    return proto

    

if __name__ == "__main__":
    num = 0x0
    p = None
    def result(vp, value):
        if value != 0:
            print(vp, value)
        global num
        num += 1
        if num < 0xFFFF:
            p.protocol.request_vp(num)
        else:
            print('complete')

    p = StartSerial('COM14', 115200, result)
    p.connect()
    p.protocol.request_vp(num)
    time.sleep(300)