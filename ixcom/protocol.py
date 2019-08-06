import collections
import struct
from . import crc16
from enum import IntEnum, IntFlag, Flag, auto
from typing import NamedTuple

class XcomError(Exception):
    def __init__(self, message = '', thrower = None):
        super().__init__(message)
        self.thrower = thrower

class ParseError(XcomError):
    pass

class msg_iterator:
    def __init__(self, msg, in_bytes):
        self.msg = msg
        self.remaining_bytes = in_bytes
        self.start_idx = 0
        self.msg_size = self.msg.size()

        
    def __iter__(self):
        return self

    def __next__(self):
        try:
            byte_chunk = self.remaining_bytes[self.start_idx:self.start_idx+self.msg_size ]
            self.start_idx += self.msg_size 
            self.msg.from_bytes(byte_chunk)

            return self.msg.data
        except:
            raise StopIteration()

SYNC_BYTE = 0x7E
GENERAL_PORT = 3000
BROADCAST_PORT = 4000
LAST_CHANNEL_NUMBER = 31
WAIT_TIME_FOR_RESPONSE = 10
    
class Response(IntEnum):
    OK                  = 0x0
    InvalidParameter    = 0x1
    InvalidChecksum     = 0x2
    InvalidLog          = 0x3
    InvalidRate         = 0x4
    InvalidPort         = 0x5
    InvalidCommand      = 0x6
    InvalidID           = 0x7
    InvalidChannel      = 0x8
    OutOfRange          = 0x9
    LogExists           = 0xA
    InvalidTrigger      = 0xB
    InternalError       = 0xC

class DatatSelectionMask(IntEnum):
    IMURAW  = 0b0000000000000001
    IMUCORR = 0b0000000000000010
    IMUCOMP = 0b0000000000000100
    VELNED  = 0b0000000000001000
    VELECEF = 0b0000000000010000
    VELBDY  = 0b0000000000100000
    ALTITUDE= 0b0000000001000000
    MSL     = 0b0000000010000000
    BAROALT = 0b0000000100000000
    WGS84POS= 0b0000001000000000
    ECEFPOS = 0b0000010000000000

class MessageID(IntEnum):
    COMMAND       = 0xFD
    RESPONSE      = 0xFE
    PARAMETER     = 0xFF

class EkfCommand(IntEnum):
    ALIGN           = 0
    SAVEPOS         = 1
    SAVEHDG         = 2
    SAVEANTOFFSET   = 3
    FORCED_ZUPT     = 4
    ALIGN_COMPLETE  = 5

class LogTrigger(IntEnum):
    SYNC          = 0
    EVENT         = 1
    POLLED        = 2

class LogCommand(IntEnum):
    ADD         = 0
    STOP        = 1
    START       = 2
    CLEAR       = 3
    CLEAR_ALL   = 4
    STOP_ALL    = 5
    START_ALL   = 6

class StartupPositionMode(IntEnum):
    GNSSPOS     = 0
    STOREDPOS   = 1
    FORCEDPOS   = 2
    CURRENTPOS  = 3

class StartupHeadingMode(IntEnum):
    DEFAULT     = 0
    STOREDHDG   = 1
    FORCEDHDG   = 2
    MAGHDG      = 3
    DUALANTHDG  = 4

class GlobalAlignStatus(IntEnum):
    LEVELLING = 0
    ALIGNING = 1
    ALIGN_COMPLETE = 2
    HDG_GOOD = 3

class GlobalPositionStatus(IntEnum):
    BAD = 0
    MEDIUM = 1
    HIGH = 2
    UNDEFINED = 3

class GlobalStatusBit(IntFlag):
    HWERROR = auto()
    COMERROR = auto()
    NAVERROR = auto()
    CALERROR = auto()

    GYROOVR = auto()
    ACCOVR = auto()
    GNSSINVALID = auto()
    STANDBY = auto()

    DYNAMICALIGN = auto()
    TIMEINVALID = auto()
    NAVMODE = auto()
    AHRSMODE = auto()

    @property
    def alignment_status(self):
        return GlobalAlignStatus((self.value & 0x3000) >> 12)

    @property
    def position_status(self):
        return GlobalPositionStatus((self.value & 0xc000) >> 14)

class SysstatBit(IntFlag):
    IMU_INVALID         =  auto()
    IMU_CRC_ERROR       =  auto()
    IMU_TIMEOUT         =  auto()
    IMU_SAMPLE_LOST     =  auto()
    ACC_X_OVERRANGE     =  auto()
    ACC_Y_OVERRANGE     =  auto()
    ACC_Z_OVERRANGE     =  auto()
    RESERVED            = auto()
    OMG_X_OVERRANGE     =  auto()
    OMG_Y_OVERRANGE     =  auto()
    OMG_Z_OVERRANGE     =  auto()
    INVALID_CAL         =  auto()
    BIT_FAIL            =  auto()
    DEFAULT_CONF        = auto()
    GNSS_INVALID        = auto()
    ZUPT_CALIB          = auto()
    GNSS_CRC_ERROR      = auto()
    GNSS_TIMEOUT        = auto()
    EKF_ERROR           = auto()
    SAVEDPOS_ERROR      = auto()
    SAVEDHDG_ERROR      = auto()
    MAG_TIMEOUT         = auto()
    MADC_TIMEOUT        = auto()
    LICENSE_EXPIRED     = auto()
    IN_MOTION           = auto()
    ODO_PLAUSIBILITY    = auto()
    ODO_HW_ERROR        = auto()
    WAITING_INITVAL     = auto()
    PPS_LOST            = auto()
    LIMITED_ACCURACY    = auto()
    REC_ENABLED         = auto()
    FPGA_NOGO           = auto()

class EKF_STATUS_LOW(IntFlag):
    POSLLH_UPDATE = auto()
    POSLLH_LAT_OUTLIER = auto()
    POSLLH_LON_OUTLIER = auto()
    POSLLH_ALT_OUTLIER = auto()
    VNED_UPDATE = auto()
    VNED_VN_OUTLIER = auto()
    VNED_VE_OUTLIER = auto()
    VNED_VD_OUTLIER = auto()
    HEIGHT_UPDATE = auto()
    HEIGHT_OUTLIER = auto()
    BAROHEIGHT_UPDATE = auto()
    BAROHEIGHT_OUTLIER = auto()
    VBDY_UPDATE = auto()
    VBDY_VX_OUTLIER = auto()
    VBDY_VY_OUTLIER = auto()
    VBDY_VZ_OUTLIER = auto()
    VODO_UPDATE = auto()
    VODO_OUTLIER = auto()
    VAIR_UPDATE = auto()
    VAIR_OUTLIER = auto()
    HDGT_UPDATE = auto()
    HDGT_OUTLIER = auto()
    HDGM_UPDATE = auto()
    HDGM_OUTLIER = auto()
    MAGFIELD_UPDATE = auto()
    MAGFIELD_HX_OUTLIER = auto()
    MAGFIELD_HY_OUTLIER = auto()
    MAGFIELD_HZ_OUTLIER = auto()
    PSEUDORANGE_UPDATE = auto()
    RANGERATE_UPDATE = auto()
    TIME_UPDATE = auto()
    ZUPT_UPDATE = auto()

class EKF_STATUS_HIGH(IntFlag):
    EKF_RTKLLH_UPDATE = 1 << 0
    EKF_RTKLLH_LAT_OUTLIER = 1 << 1
    EKF_RTKLLH_LON_OUTLIER = 1 << 2
    EKF_RTKLLH_ALT_OUTLIER = 1 << 3

    EKF_DUALANT_UPDATE = 1 << 4
    EKF_DUALANT_OUTLIER = 1 << 5
    EKF_COG_UPDATE = 1 << 6
    EKF_COG_OUTLIER = 1 << 7

    EKF_TDCP_UPDATE = 1 << 8
    EKF_TDCP_DD_UPDATE = 1 << 9
    EKF_ODO_ALONGTRACK_UPDATE = 1 << 10
    EKF_ODO_ALONGTRACK_OUTLIER = 1 << 11        

    EKF_ODO_CONSTRAINT_UPDATE = 1 << 12
    EKF_ODO_CONSTRAINT_OUTLIER = 1 << 13
    EKF_GRAVITY_UPDATE = 1 << 14
    EKF_GRAVITY_OUTLIER = 1 << 15

    EKF_EXTPOS_UPDATE = 1 << 16
    EKF_EXTPOS_OUTLIER = 1 << 17
    EKF_EXTVEL_UPDATE = 1 << 18
    EKF_EXTVEL_OUTLIER = 1 << 19

    EKF_ZARU_UPDATE = 1 << 20

    EKF_WAHBA_UPDATE = 1 << 24
    EKF_WAHBA_FILTER = 1 << 25
    EKF_FILTER_MODE_1 = 1 << 26
    EKF_FILTER_MODE_2 = 1 << 27

    EKF_WAHBA_INTERNAL = 1 << 28
    EKF_LEVELLING_COMPLETE = 1 << 29
    EKF_STATIONARY_ALIGN_COMPLETE = 1 << 30
    EKF_POSITION_VALID = 1 << 31

class EkfStatus:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f'Low Status: {str(EKF_STATUS_LOW(self.value[0]))}, High status: {str(EKF_STATUS_LOW(self.value[0]))}'

    

class PayloadItem(NamedTuple):
    name: str
    dimension: int
    datatype: str
    description: str = ''
    unit: str = ''
    metatype = None

class Message:
    def __init__(self, item_list: [PayloadItem], name = ''):
        self.item_list = item_list
        self.data = self.generate_data_dict()
        self.struct_inst = struct.Struct(self.generate_struct_string())
        self.name = name

    def unpack_from(self, buffer, offset = 0):
        try:
            data = dict(self.data)
            keyList = self.data.keys()
            valueList = self.struct_inst.unpack_from(buffer, offset)
            start_idx = 0
            for key in keyList:
                if isinstance(self.data[key], (list, tuple)):
                    end_idx = start_idx + len(self.data[key])
                    value = valueList[start_idx:end_idx]
                    start_idx = end_idx
                else:
                    value = valueList[start_idx]
                    start_idx += 1
                data[key] = value
            return data
        except struct.error:
            raise ParseError(f'Could not convert {self.name}')

    def generate_struct_string(self):
        struct_string = '='
        for item in self.item_list:
            if item.dimension != 1:
                struct_string += '%d' % item.dimension
            struct_string += item.datatype
        return struct_string

    def generate_data_dict(self):
        data = collections.OrderedDict()
        for item in self.item_list:
            if item.dimension == 1:
                data[item.name] = self.null_item(item.datatype)
            elif item.datatype is not 's':
                data[item.name] = [self.null_item(item.datatype) for _ in range(0, item.dimension)]
            else:
                data[item.name] = b'\0'*item.dimension
        return data

    def null_item(self, datatype):
        if datatype in 'BbHhIiLlQq':
            return 0
        elif datatype in 'fd':
            return 0.0
        elif datatype in 's':
            return b'\0'
        else:
            raise ValueError('Illegal datatype "{}"'.format(datatype))

class MessageItem:
    struct_inst: struct.Struct

    def __init__(self):
        pass

    def to_bytes(self):
        raise NotImplementedError()

    def from_bytes(self, inBytes):
        raise NotImplementedError()

    def size(self):
        try:
            return self.struct_inst.size
        except:
            raise NotImplementedError()

class ProtocolHeader(MessageItem):
    structString = "=BBBBHHII"

    def __init__(self):
        self.sync               = 0x7E
        self.msgID              = 0
        self.frameCounter       = 0
        self.reserved           = 0
        self.msgLength          = 0
        self.week               = 0
        self.timeOfWeek_sec     = 0
        self.timeOfWeek_usec     = 0
        self.struct_inst = struct.Struct(self.structString)

    def get_time(self):
        return self.timeOfWeek_sec + 1.0e-6*self.timeOfWeek_usec

    def set_time(self, time_of_week):
        self.timeOfWeek_sec = int(time_of_week)
        self.timeOfWeek_usec = int((time_of_week-self.timeOfWeek_sec)/1e-6)

    def to_bytes(self):
        return bytearray(self.struct_inst.pack(self.sync, self.msgID, self.frameCounter, self.reserved, self.msgLength, self.week, self.timeOfWeek_sec, self.timeOfWeek_usec))

    def from_bytes(self, inBytes):
        self.sync, self.msgID, self.frameCounter, self.reserved, self.msgLength, self.week, self.timeOfWeek_sec, self.timeOfWeek_usec = self.struct_inst.unpack(inBytes[:16])

    def get_data(self):
        d = {
            'sync': self.sync, 
            'msg_id': self.msgID, 
            'frame_counter': self.frameCounter, 
            'reserved': self.reserved,
            'msg_length': self.msgLength,
            'week': self.week,
            'time_of_week_sec': self.timeOfWeek_sec,
            'time_of_week_usec': self.timeOfWeek_usec}
        return d



class ProtocolBottom(MessageItem):
    structString = "=HH"

    def __init__(self):
        self.gStatus = 0
        self.crc = 0
        self.struct_inst = struct.Struct(self.structString)

    def to_bytes(self):
        return bytearray(self.struct_inst.pack(self.gStatus, self.crc))

    def from_bytes(self, inBytes):
        self.gStatus, self.crc = self.struct_inst.unpack(inBytes)

class ProtocolPayload(MessageItem):
    message_id = 0
    message_description = None
    _structString = None
    data = collections.OrderedDict()


    def __init__(self):
        if type(self)._structString is None:
            if type(self).message_description is not None:
                type(self)._structString = type(self).message_description.generate_struct_string()
                type(self).struct_inst = struct.Struct(self._structString)
        if type(self).message_description is not None:
            self.message_description.name = self.get_name()
            self.data = type(self).message_description.generate_data_dict()

    @property
    def structString(self):
        return self._structString

    @structString.setter
    def structString(self, value):
        self._structString = value
        self.struct_inst = struct.Struct(self._structString)

    def to_bytes(self):
        values = []
        for value in self.data.values():
            if isinstance(value, (list, tuple)):
                values += value
            else:
                values += [value]
        return bytearray(self.struct_inst.pack(*values))

    def from_bytes(self, inBytes):
        self.data.update(self.message_description.unpack_from(inBytes))

    @classmethod
    def get_name(cls):
        classname = cls.__name__
        return classname.split('_Payload')[0]

    @classmethod
    def construct_message(cls):
        return getMessageWithID(cls.message_id)

class ProtocolMessage(MessageItem):
    def __init__(self):
        self.header  =  ProtocolHeader()
        self.payload =  ProtocolPayload()
        self.bottom  =  ProtocolBottom()

    def to_bytes(self):
        self.header.msgLength = self.size()
        msgBytes = self.header.to_bytes()
        msgBytes += self.payload.to_bytes()
        msgBytes += b'\x00\x00'
        self.bottom.crc = crc16.crc16xmodem(bytes(msgBytes))
        return self.header.to_bytes() + self.payload.to_bytes() + self.bottom.to_bytes()

    def from_bytes(self, inBytes):
        headerBytes = inBytes[:16]
        self.header.from_bytes(headerBytes)
        messageBytes = inBytes[16:self.header.msgLength-4]
        self.payload.from_bytes(messageBytes)
        bottomBytes = inBytes[self.header.msgLength-4:self.header.msgLength]
        self.bottom.from_bytes(bottomBytes)

    @property
    def data(self):
        result = self.header.get_data()
        result.update(self.payload.data)
        result['global_status'] = self.bottom.gStatus
        result['crc'] = self.bottom.crc
        return result

    @property
    def structString(self):
        return self.header.structString + self.payload.structString[1:] + self.bottom.structString[1:]


    def __str__(self):
        tmp = str(self.header.frameCounter)+","+str(self.header.timeOfWeek_sec+1e-6*self.header.timeOfWeek_usec)
        for item in self.payload.data:
            if isinstance(self.payload.data[item],(list, tuple)):
                datastr = ','.join(map(str, self.payload.data[item]))
            else:
                datastr = str(self.payload.data[item])
            tmp += ","+datastr
        return tmp

    def to_double_array(self):
        tmp = [self.header.frameCounter, (self.header.timeOfWeek_sec+1e-6*self.header.timeOfWeek_usec)]
        for item in self.payload.data:
            if isinstance(self.payload.data[item],(list, tuple)):
                tmp += self.payload.data[item]
            else:
                tmp += [self.payload.data[item]]
        return tmp

    def iter_unpack(self, buffer):
        struct_string = '=' + self.header.structString[1:] + self.payload.structString[1:] + self.bottom.structString[1:]
        struct_inst = struct.Struct(struct_string)
        return struct_inst.iter_unpack(buffer)

    def get_numpy_dtype(self):
        struct_string = self.header.structString[1:] + self.payload.structString[1:] + self.bottom.structString[1:]
        current_item = ''
        item_list = []
        dtype_list = []
        while len(struct_string) > 0:
            while struct_string[0] not in 'fdsbBhHiI':
                current_item += struct_string[0]
                struct_string = struct_string[1:]
            current_item += struct_string[0]
            struct_string = struct_string[1:]
            item_list.append(current_item)
            current_item = ''

        for idx, item in enumerate(item_list):
            fieldname = list(self.data.keys())[idx]
            cardinality = item.rstrip('fdsbBhHiI')
            if len(cardinality) == 0:
                cardinality = 1
            else:
                cardinality = int(cardinality)
            dtype = item[-1]
            if dtype in 'bB':
                byte_size = '1'
            elif dtype in 'hH':
                byte_size = '2'
            elif dtype in 'iIf':
                byte_size = '4'
            elif dtype in 'd':
                byte_size = '8'
            if dtype in 'bhi':
                out_type = 'i'
            elif dtype in 'BHI':
                out_type = 'u'
            elif dtype in 'fd':
                out_type = 'f'
            elif dtype in 's':
                out_type = 'S'

            if out_type == 'S':
                out_type = 'S'+str(cardinality)
                item_spec = (fieldname, out_type)
            else:
                out_type = out_type + byte_size
                item_spec = (fieldname, out_type, cardinality)
            dtype_list.append(item_spec)

        return dtype_list

    def size(self):
        return self.header.size()+self.payload.size()+self.bottom.size()


class XcomCommandParameter(IntEnum):
    reset_timebias = 6
    update_svn        = 5
    reset_omg_int  = 4
    warmreset      = 3
    reboot         = 2
    channel_open   = 1
    channel_close  = 0

class ParameterAction(IntEnum):
    CHANGING = 0
    REQUESTING = 1

class DefaultCommandPayload(ProtocolPayload):
    message_id = MessageID.COMMAND
    command_id = 0
    command_header = Message([
        PayloadItem(name = 'cmdID', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'specific', dimension = 1, datatype = 'H'),
    ])
    command_payload = Message([])

    def __init__(self):
        if type(self).message_description is None:
            type(self).message_description = Message(type(self).command_header.item_list + type(self).command_payload.item_list)
        super().__init__()


class DefaultParameterPayload(ProtocolPayload):
    message_id = MessageID.PARAMETER
    parameter_id = 0
    parameter_header = Message([
        PayloadItem(name = 'parameterID', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved_paramheader', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'action', dimension = 1, datatype = 'B'),
    ])
    parameter_payload = Message([])
    message_description = None

    def __init__(self):
        if type(self).message_description is None:
            type(self).message_description = Message(type(self).parameter_header.item_list + type(self).parameter_payload.item_list)
        super().__init__()

    def payload_from_bytes(self, in_bytes):
        self.data.update(self.parameter_payload.unpack_from(in_bytes))

        

MessagePayloadDictionary = dict()
def message(message_id):
    def decorator(cls):
        cls.message_id = message_id
        #print(MessagePayloadDictionary)
        MessagePayloadDictionary[message_id] = cls
        return cls

    return decorator


ParameterPayloadDictionary = dict()
def parameter(parameter_id):
    def decorator(cls):
        cls.parameter_id = parameter_id
        ParameterPayloadDictionary[parameter_id] = cls
        return cls

    return decorator

CommandPayloadDictionary = dict()
def command(command_id):
    def decorator(cls):
        cls.command_id = command_id
        CommandPayloadDictionary[command_id] = cls
        return cls

    return decorator



def getMessageWithID(msgID):
    message = ProtocolMessage()
    message.header.msgID = msgID
    if msgID in MessagePayloadDictionary:
        message.payload = MessagePayloadDictionary[msgID]()
        return message
    else:
        return None


def getCommandWithID(cmdID):
    message = ProtocolMessage()
    message.header.msgID = MessageID.COMMAND
    if cmdID in CommandPayloadDictionary:
        message.payload = CommandPayloadDictionary[cmdID]()
        message.payload.data['cmdID'] = cmdID
        return message
    else:
        return None


def getParameterWithID(parameterID):
    message = ProtocolMessage()
    message.header.msgID = MessageID.PARAMETER
    if parameterID in ParameterPayloadDictionary:
        message.payload = ParameterPayloadDictionary[parameterID]()
        message.payload.data['parameterID'] = parameterID
        return message
    else:
        return None
