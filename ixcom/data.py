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

        

"""
Commands
"""
CommandPayloadDictionary = dict()
def command(command_id):
    def decorator(cls):
        cls.command_id = command_id
        CommandPayloadDictionary[command_id] = cls
        return cls

    return decorator

@command(0x0)
class CMD_LOG_Payload(DefaultCommandPayload):
    command_payload = Message([
        PayloadItem(name = 'messageID', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'trigger', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'parameter', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'divider', dimension = 1, datatype = 'H'),
    ])

@command(0x4)
class CMD_EKF_Payload(DefaultCommandPayload):
    command_payload = Message([
        PayloadItem(name = 'subcommand', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'numberOfParams', dimension = 1, datatype = 'H'),
    ])

@command(0x3)
class CMD_CONF_Payload(DefaultCommandPayload):
    command_payload = Message([
        PayloadItem(name = 'configAction', dimension = 1, datatype = 'I'),
    ])

@command(0x1)
class CMD_EXT_Payload(DefaultCommandPayload):
    command_payload = Message([
        PayloadItem(name = 'time', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'timeMode', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'cmdParamID', dimension = 1, datatype = 'H'),
    ])

@command(0x5)
class XcomCommandPayload(DefaultCommandPayload):
    command_payload = Message([
        PayloadItem(name = 'mode', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'channelNumber', dimension = 1, datatype = 'H'),
    ])

"""
PARSYS
"""
ParameterPayloadDictionary = dict()
def parameter(parameter_id):
    def decorator(cls):
        cls.parameter_id = parameter_id
        ParameterPayloadDictionary[parameter_id] = cls
        return cls

    return decorator

class PARSYS_STRING_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'str', dimension = 32, datatype = 's')
    ])

class PARSYS_STRING64_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'str', dimension = 64, datatype = 's')
    ])

@parameter(0)
class PARSYS_PRJNUM_Payload(PARSYS_STRING_Payload):
    pass

@parameter(1)
class PARSYS_PARTNUM_Payload(PARSYS_STRING_Payload):
    pass

@parameter(2)
class PARSYS_SERIALNUM_Payload(PARSYS_STRING_Payload):
    pass

@parameter(3)
class PARSYS_MFG_Payload(PARSYS_STRING_Payload):
    pass

@parameter(5)
class PARSYS_FWVERSION_Payload(PARSYS_STRING_Payload):
    pass

@parameter(6)
class PARSYS_NAVLIB_Payload(PARSYS_STRING_Payload):
    pass

@parameter(7)
class PARSYS_EKFLIB_Payload(PARSYS_STRING_Payload):
    pass

@parameter(8)
class PARSYS_EKFPARSET_Payload(PARSYS_STRING_Payload):
    pass

@parameter(9)
class PARSYS_NAVNUM_Payload(PARSYS_STRING_Payload):
    pass

@parameter(10)
class PARSYS_NAVPARSET_Payload(PARSYS_STRING_Payload):
    pass

@parameter(11)
class PARSYS_MAINTIMING_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'maintiming', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])

@parameter(4)
class PARSYS_CALDATE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'str', dimension = 32, datatype = 's'),
    ])

@parameter(12)
class PARSYS_PRESCALER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'prescaler', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])

@parameter(13)
class PARSYS_UPTIME_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'uptime', dimension = 1, datatype = 'f'),
    ])

@parameter(14)
class PARSYS_OPHOURCOUNT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'ophours', dimension = 1, datatype = 'I'),
    ])

@parameter(15)
class PARSYS_BOOTMODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'bootmode', dimension = 1, datatype = 'I'),
    ])

@parameter(16)
class PARSYS_FPGAVER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'major', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'minor', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'imutype', dimension = 1, datatype = 'H'),
    ])

@parameter(17)
class PARSYS_CONFIGCRC_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'romCRC', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'ramCRC', dimension = 1, datatype = 'H'),
    ])

@parameter(18)
class PARSYS_OSVERSION_Payload(PARSYS_STRING64_Payload):
    pass

@parameter(19)
class PARSYS_SYSNAME_Payload(PARSYS_STRING64_Payload):
    pass

"""
PARIMU
"""
@parameter(105)
class PARIMU_MISALIGN_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'rpy', dimension = 3, datatype = 'f'),
    ])

@parameter(107)
class PARIMU_TYPE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'type', dimension = 1, datatype = 'I'),
    ])

@parameter(108)
class PARIMU_LATENCY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'latency', dimension = 1, datatype = 'd'),
    ])


@parameter(111)
class PARIMU_REFPOINTOFFSET_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'offset', dimension = 3, datatype = 'd'),
    ])

@parameter(112)
class PARIMU_BANDSTOP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'bandwidth', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'center', dimension = 1, datatype = 'f'),
    ])

@parameter(113)
class PARIMU_COMPMETHOD_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'method', dimension = 1, datatype = 'I'),
    ])

@parameter(114)
class PARIMU_ACCLEVERARM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'leverarms', dimension = 9, datatype = 'd'),
    ])

@parameter(115)
class PARIMU_STRAPDOWNCONF_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'isIncType', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'deltaVFrame', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'numberOfDeltaTheta', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
    ])

@parameter(117)
class PARIMU_RANGE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'range_accel', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'range_gyro', dimension = 1, datatype = 'f'),
    ])



"""
PARGNSS
"""
@parameter(200)
class PARGNSS_PORT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])

@parameter(201)
class PARGNSS_BAUD_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])

@parameter(203)
class PARGNSS_LATENCY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'baud', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])

@parameter(204)
class PARGNSS_ANTOFFSET_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'antennaOffset', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdDev', dimension = 3, datatype = 'f'),
    ])

    def get_name(self):
        
        return super().get_name() + '_' + str(self.data.get('reserved_paramheader', ''))

@parameter(207)
class PARGNSS_RTKMODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'rtkMode', dimension = 1, datatype = 'I'),
    ])


@parameter(209)
class PARGNSS_AIDFRAME_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'aidingFrame', dimension = 1, datatype = 'I'),
    ])


@parameter(211)
class PARGNSS_DUALANTMODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'dualAntMode', dimension = 1, datatype = 'I'),
    ])


@parameter(212)
class PARGNSS_LOCKOUTSYSTEM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'lockoutMask', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved3', dimension = 1, datatype = 'H'),
    ])


@parameter(213)
class PARGNSS_RTCMV3CONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
    ])


@parameter(214)
class PARGNSS_NAVCONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'elevationCutoff', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'CN0ThreshSVs', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'CN0Thresh', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(215)
class PARGNSS_STDDEV_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'stdDevScalingPos', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'minStdDevPos', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDevScalingRTK', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'minStdDevRTK', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDevScalingVel', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'minStdDevVel', dimension = 1, datatype = 'f'),
    ])


@parameter(216)
class PARGNSS_VOTER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'debugEnable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'timeout', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'voterMode', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'hysteresis', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'PortInt', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'PortExt', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'selectionMode', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'baudInt', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'baudExt', dimension = 1, datatype = 'I'),
    ])

@parameter(217)
class PARGNSS_MODEL_Payload(DefaultParameterPayload):
    __sub_payloads = [
        [PayloadItem(name = f'modelName_{idx}', dimension = 16, datatype = 's'),
        PayloadItem(name = f'year_{idx}', dimension = 1, datatype = 'I'),
        PayloadItem(name = f'month_{idx}', dimension = 1, datatype = 'I'),
        PayloadItem(name = f'day_{idx}', dimension = 1, datatype = 'I')] for idx in range(0, 6)
    ]
    parameter_payload = Message([
        PayloadItem(name = 'rtkCode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved3', dimension = 1, datatype = 'H'),
    ] + [
        payload_item for model in __sub_payloads for payload_item in model
    ])

@parameter(218)
class PARGNSS_VERSION_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'type', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'model', dimension = 16, datatype = 's'),
        PayloadItem(name = 'psn', dimension = 16, datatype = 's'),
        PayloadItem(name = 'hwversion', dimension = 16, datatype = 's'),
        PayloadItem(name = 'swversion', dimension = 16, datatype = 's'),
        PayloadItem(name = 'bootversion', dimension = 16, datatype = 's'),
        PayloadItem(name = 'compdate', dimension = 16, datatype = 's'),
        PayloadItem(name = 'comptime', dimension = 16, datatype = 's'),
    ])


@parameter(219)
class PARGNSS_RTKSOLTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'positionType', dimension = 1, datatype = 'I'),
    ])


@parameter(220)
class PARGNSS_TERRASTAR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'PPPPosition', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 7, datatype = 'B'),
    ])


@parameter(224)
class PARGNSS_CORPORTCFG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'rxType', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'txType', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'periodGGA', dimension = 1, datatype = 'f'),
    ])


@parameter(226)
class PARGNSS_SWITCHER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'switcher', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(221)
class PARGNSS_REFSTATION_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enableNTRIP', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'useFIXPOS', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enableRTCMoutput', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
    ])


@parameter(222)
class PARGNSS_FIXPOS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'pos', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'posStdDev', dimension = 1, datatype = 'd'),
    ])


@parameter(223)
class PARGNSS_POSAVE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'maxTime', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'maxHorStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'maxVertStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'aveStatus', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'aveTime', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'state', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
    ])

        
"""
PARMAG
"""
@parameter(300)
class PARMAG_COM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved3', dimension = 3, datatype = 'B'),
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
    ])


@parameter(302)
class PARMAG_PERIOD_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'period', dimension = 1, datatype = 'I'),
    ])


@parameter(304)
class PARMAG_MISALIGN_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'rpy', dimension = 3, datatype = 'f'),
    ])


@parameter(307)
class PARMAG_CAL_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'C', dimension = 9, datatype = 'f'),
        PayloadItem(name = 'bias', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'valid', dimension = 1, datatype = 'I'),
    ])


@parameter(308)
class PARMAG_CALSTATE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'calstate', dimension = 1, datatype = 'i'),
    ])


@parameter(310)
class PARMAG_CFG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'configbitfield', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'paramIdx', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(311)
class PARMAG_ENABLE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
    ])


@parameter(309)
class PARMAG_FOM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'FOM', dimension = 1, datatype = 'f'),
    ])


"""
PARMADC
"""
@parameter(400)
class PARMADC_ENABLE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
    ])


@parameter(401)
class PARMADC_LEVERARM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'leverArm', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'leverArmStdDev', dimension = 3, datatype = 'f'),
    ])


@parameter(402)
class PARMADC_LOWPASS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'cutoff', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'enableFilter', dimension = 1, datatype = 'I'),
    ])


"""
PARODO
"""
@parameter(1100)
class PARODO_SCF_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'scfOdo', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'scfEst', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'selection', dimension = 1, datatype = 'I'),
    ])


@parameter(1101)
class PARODO_TIMEOUT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'timeout', dimension = 1, datatype = 'f'),
    ])


@parameter(1102)
class PARODO_MODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'mode', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'deglitcherA', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'deglitcherB', dimension = 1, datatype = 'H'),
    ])


@parameter(1103)
class PARODO_LEVERARM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'leverArm', dimension = 3, datatype = 'f'),
    ])


@parameter(1104)
class PARODO_VELSTDDEV_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'stdDev', dimension = 1, datatype = 'f'),
    ])


@parameter(1105)
class PARODO_DIRECTION_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'direction', dimension = 3, datatype = 'f'),
    ])


@parameter(1106)
class PARODO_CONSTRAINTS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved3', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'stdDev', dimension = 1, datatype = 'f'),
    ])


@parameter(1107)
class PARODO_RATE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'rate', dimension = 1, datatype = 'f'),
    ])


@parameter(1108)
class PARODO_THR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'thrAcc', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'thrOmg', dimension = 1, datatype = 'f'),
    ])


@parameter(1109)
class PARODO_EQEP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'mode', dimension = 1, datatype = 'I'),
    ])


"""
PARARINC
"""
@parameter(1200)
class PARARINC825_PORT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'I'),
    ])


@parameter(1201)
class PARARINC825_BAUD_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
    ])


@parameter(1202)
class PARARINC825_ENABLE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'H'),
    ])

@parameter(1204)
class PARARINC825_LOGLIST_Payload(DefaultParameterPayload):
    __sub_payload = [
        [PayloadItem(name = f'divider_{idx}', dimension = 1, datatype = 'H'), PayloadItem(name = f'reserved_{idx}', dimension = 1, datatype = 'H'), PayloadItem(name = f'docnumber_{idx}', dimension = 1, datatype = 'H')] for idx in range(0, 30)
    ]
    parameter_payload = Message([
        item for docitem in __sub_payload for item in docitem
    ])


@parameter(1205)
class PARARINC825_BUSRECOVERY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(1206)
class PARARINC825_RESETSTATUS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'reset', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'busStatus', dimension = 1, datatype = 'H'),
    ])


@parameter(1207)
class PARARINC825_SCALEFACTOR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'ScfAcc', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfOmg', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfRPY', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'ScfVel', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfTime', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfPos', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'ScfRPYStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfInsPosStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfVelStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfGnssPosStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ScfSideSlip', dimension = 1, datatype = 'd'),
    ])


@parameter(1208)
class PARARINC825_EVENTMASK_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'eventMask', dimension = 1, datatype = 'I'),
    ])


"""
PARREC
"""
@parameter(600)
class PARREC_CONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'channelNumber', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'autostart', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(603)
class PARREC_START_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'str', dimension = 128, datatype = 's'),
    ])


@parameter(604)
class PARREC_STOP_Payload(DefaultParameterPayload):
    pass

@parameter(605)
class PARREC_POWER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
    ])


@parameter(607)
class PARREC_DISKSPACE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'freespace', dimension = 1, datatype = 'd'),
    ])


@parameter(608)
class PARREC_AUXILIARY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'baudrate', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'ip', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'udpport', dimension = 1, datatype = 'I'),
    ])

        
@parameter(606)
class PARREC_SUFFIX_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'suffix', dimension = 128, datatype = 's'),
    ])


"""
PAREKF
"""
@parameter(700)
class PAREKF_ALIGNMODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'alignmode', dimension = 1, datatype = 'I'),
    ])


@parameter(708)
class PAREKF_HDGPOSTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'hdgGoodThr', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'posMedThr', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'posHighThr', dimension = 1, datatype = 'f'),
    ])


@parameter(701)
class PAREKF_ALIGNTIME_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'aligntime', dimension = 1, datatype = 'I'),
    ])


@parameter(702)
class PAREKF_COARSETIME_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'coarsetime', dimension = 1, datatype = 'I'),
    ])


@parameter(703)
class PAREKF_VMP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'leverArm', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'mask', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'cutoff', dimension = 1, datatype = 'H'),
    ])



@parameter(706)
class PAREKF_DELAY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'delay', dimension = 1, datatype = 'I'),
    ])


@parameter(716)
class PAREKF_OUTLIER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'outlierMode', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'outlierMask', dimension = 1, datatype = 'I'),
    ])


@parameter(707)
class PAREKF_STARTUP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'initLon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'initLat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'initAlt', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDev', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'initHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDevHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'posMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'hdgMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'gnssTimeout', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'realign', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'inMotion', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'autoRestart', dimension = 1, datatype = 'B'),
    ])


@parameter(731)
class PAREKF_STARTUPV2_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'initLon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'initLat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'initAlt', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDev', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'initHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDevHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'leverArm', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdLeverArm', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'posMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'hdgMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'gnssTimeout', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'altMSL', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'realign', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'inMotion', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'autoRestart', dimension = 1, datatype = 'B'),
    ])


@parameter(712)
class PAREKF_ZUPT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'accThr', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'omgThr', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'velThr', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'cutoff', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'zuptrate', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'minStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'weightingFactor', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'timeConstant', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'delay', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'mask', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'autoZupt', dimension = 1, datatype = 'B'),
    ])


@parameter(714)
class PAREKF_DEFPOS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'lon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'lat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'alt', dimension = 1, datatype = 'f'),
    ])


@parameter(715)
class PAREKF_DEFHDG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'hdg', dimension = 1, datatype = 'f'),
    ])


@parameter(709)
class PAREKF_SMOOTH_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'smooth', dimension = 1, datatype = 'I'),
    ])


@parameter(717)
class PAREKF_POWERDOWN_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'savestate', dimension = 1, datatype = 'I'),
    ])


@parameter(718)
class PAREKF_EARTHRAD_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'M', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'N', dimension = 1, datatype = 'f'),
    ])


@parameter(719)
class PAREKF_STOREDPOS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'lon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'lat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'alt', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'stdDevLon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'stdDevLat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'stdDevAlt', dimension = 1, datatype = 'd'),
    ])


@parameter(723)
class PAREKF_STOREDATT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'rpy', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdDev', dimension = 3, datatype = 'f'),
    ])


@parameter(720)
class PAREKF_ALIGNZUPTSTDDEV_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'zuptStdDev', dimension = 1, datatype = 'd'),
    ])


@parameter(721)
class PAREKF_POSAIDSTDDEVTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'thr', dimension = 1, datatype = 'd'),
    ])


@parameter(724)
class PAREKF_ODOMETER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'sfError', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'sfStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'rwScalefactor', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'misalignmentY', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'misalignmentZ', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdMisalignmentY', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdMisalignmentZ', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'rwMisalignmentY', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'rwMisalignmentZ', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'minVel', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'maxVel', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'useAvgInno', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'enableCoarseCal', dimension = 1, datatype = 'H'),
    ])


@parameter(725)
class PAREKF_ODOBOGIE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'distance', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
    ])


@parameter(726)
class PAREKF_GNSSLEVERARMEST_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'primary', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'secondary', dimension = 1, datatype = 'H'),
    ])


@parameter(727)
class PAREKF_GNSSAIDINGRATE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'psrpos', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'psrvel', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'rtk', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'rtktimeout', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'hdg', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'duringzupt', dimension = 1, datatype = 'H'),
    ])


@parameter(728)
class PAREKF_KINALIGNTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'thr', dimension = 1, datatype = 'f'),
    ])


@parameter(729)
class PAREKF_PDOPTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'thr', dimension = 1, datatype = 'f'),
    ])


@parameter(730)
class PAREKF_DUALANTAID_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'thrHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'thrPitch', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'thrINSHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'mode', dimension = 1, datatype = 'I'),
    ])


@parameter(732)
class PAREKF_MAGATTAID_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'samplePeriods', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'thrHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'latency', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'thrINSHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'aidingMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'updateMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'aidingInterval', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'magFieldStdDev', dimension = 3, datatype = 'f'),
    ])


@parameter(733)
class PAREKF_MADCAID_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'altStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'latency', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'aidInterval', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'sfError', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'sfStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'rwSf', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'bias', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'biasStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'rwBias', dimension = 1, datatype = 'f'),
    ])


@parameter(734)
class PAREKF_ALIGNMENT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'method', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'levellingDuration', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'stationaryDuration', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'alignZuptStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'enableGyroAvg', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enableTrackAlign', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'trackAlignThresh', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'trackAlignDirection', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved3', dimension = 3, datatype = 'I'),
    ])


@parameter(735)
class PAREKF_GRAVITYAID_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'omgThresh', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'accThresh', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'gnssTimeout', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'aidingInterval', dimension = 1, datatype = 'f'),
    ])



@parameter(737)
class PAREKF_ZARU_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 3, datatype = 'B'),
    ])


@parameter(738)
class PAREKF_IMUCONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'accPSD', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'accOffStdDev', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'accOffRW', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'accSfStdDev', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'accSfRW', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'accMaStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'accMaRW', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'accQuantization', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'gyroPSD', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'gyroOffStdDev', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'gyroOffRW', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'gyroSfStdDev', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'gyroSfRW', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'gyroMaStdDev', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'gyroMaRW', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'gyroQuantization', dimension = 3, datatype = 'd'),
    ])


@parameter(739)
class PAREKF_ZUPTCALIB_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'zuptCalibTime', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])



@parameter(741)
class PAREKF_RECOVERY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'recoveryMask', dimension = 1, datatype = 'I'),
    ])


"""
PARDAT
"""
@parameter(800)
class PARDAT_POS_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'posMode', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'altMode', dimension = 1, datatype = 'H'),
    ])


@parameter(801)
class PARDAT_VEL_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'velMode', dimension = 1, datatype = 'I'),
    ])


@parameter(802)
class PARDAT_IMU_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'imuMode', dimension = 1, datatype = 'I'),
    ])


@parameter(803)
class PARDAT_SYSSTAT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'statMode', dimension = 1, datatype = 'I'),
    ])


class PARDAT_STATFPGA_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'powerStatLower', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'powerStatUpper', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'fpgaStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'supervisorStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'imuStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'tempStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


"""
PARXCOM
"""
@parameter(902)
class PARXCOM_SERIALPORT_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'switch', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'baudRate', dimension = 1, datatype = 'I'),
    ])


@parameter(903)
class PARXCOM_NETCONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'mode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'protocol', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'interface', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'speed', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'port', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'ip', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'subnetmask', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'gateway', dimension = 1, datatype = 'I'),
    ])

@parameter(905)
class PARXCOM_LOGLIST_Payload(DefaultParameterPayload):
    __sub_payload = [
        [PayloadItem(name = f'divider_{idx}', dimension = 1, datatype = 'H'), PayloadItem(name = f'msgid_{idx}', dimension = 1, datatype = 'H')] for idx in range(0, 16)
    ]
    parameter_payload = Message([
        logitem for log in __sub_payload for logitem in log
    ])


@parameter(906)
class PARXCOM_AUTOSTART_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'channelNumber', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'autoStart', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'port', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(907)
class PARXCOM_NTRIP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'stream', dimension = 128, datatype = 's'),
        PayloadItem(name = 'user', dimension = 128, datatype = 's'),
        PayloadItem(name = 'password', dimension = 128, datatype = 's'),
        PayloadItem(name = 'server', dimension = 128, datatype = 's'),
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
    ])


@parameter(908)
class PARXCOM_POSTPROC_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'channel', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])

@parameter(910)
class PARXCOM_UDPCONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'ip', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'port', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'channel', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enableABD', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
    ])


@parameter(911)
class PARXCOM_DUMPENABLE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
    ])


@parameter(912)
class PARXCOM_MIGRATOR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'I'),
    ])

@parameter(913)
class PARXCOM_TCPKEEPAL_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'timeout', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'interval', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'probes', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'H'),
    ])


@parameter(914)
class PARXCOM_CANGATEWAY_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'srcPort', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'destPort', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'destAddr', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'arinc825Loopback', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'debugEnable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'interface', dimension = 1, datatype = 'B'),
    ])


@parameter(915)
class PARXCOM_DEFAULTIP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'defaultAddress', dimension = 1, datatype = 'I'),
    ])


@parameter(916)
class PARXCOM_ABDCONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'destinationPort', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'sourcePort', dimension = 1, datatype = 'I'),
    ])

@parameter(917)
class PARXCOM_LOGLIST2_Payload(DefaultParameterPayload):
    __sub_payload = [
        [
            PayloadItem(name = f'divider_{idx}', dimension = 1, datatype = 'H'), 
            PayloadItem(name = f'msgid_{idx}', dimension = 1, datatype = 'H'),
            PayloadItem(name = f'running_{idx}', dimension = 1, datatype = 'B'),
            PayloadItem(name = f'reserved2_{idx}', dimension = 1, datatype = 'B'),
            PayloadItem(name = f'reserved3_{idx}', dimension = 1, datatype = 'H')
        ] for idx in range(0, 16)
    ]
    parameter_payload = Message([
        logitem for log in __sub_payload for logitem in log
    ])

@parameter(919)
class PARXCOM_CLIENT_Payload(DefaultParameterPayload):
    def __init__(self):
        item_list = []
        for idx in range(0, 8):
            item_list += [
                PayloadItem(name = f'ipAddress_{idx}', dimension = 1, datatype = 'I'),
                PayloadItem(name = f'port_{idx}', dimension = 1, datatype = 'I'),
                PayloadItem(name = f'enable_{idx}', dimension = 1, datatype = 'B'),
                PayloadItem(name = f'channel_{idx}', dimension = 1, datatype = 'B'),
                PayloadItem(name = f'connectionRetr_{idx}', dimension = 1, datatype = 'H'),
            ]
            for idx2 in range(0, 8):
                item_list += [
                    PayloadItem(name = f'messageId_{idx}{idx2}', dimension = 1, datatype = 'B'),
                    PayloadItem(name = f'trigger_{idx}{idx2}', dimension = 1, datatype = 'B'),
                    PayloadItem(name = f'dividerLogs_{idx}{idx2}', dimension = 1, datatype = 'H'),
                ]
        item_list += [
            PayloadItem(name = 'useUDPInterface', dimension = 1, datatype = 'B'),
            PayloadItem(name = 'reserved2', dimension = 3, datatype = 'B'),
        ]

        type(self).parameter_payload = Message(item_list)
        super().__init__()


"""
PARFPGA
"""


@parameter(1002)
class PARFPGA_TIMINGREG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'timing_reg', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'userTimer', dimension = 3, datatype = 'H'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])


@parameter(1000)
class PARFPGA_IMUSTATUSREG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'register', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])


@parameter(1001)
class PARFPGA_HDLCREG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'mode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'clock', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'invertData', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'invertClock', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])


@parameter(1004)
class PARFPGA_INTERFACE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'matrix', dimension = 23, datatype = 'I'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'password', dimension = 1, datatype = 'H'),
    ])


@parameter(1005)
class PARFPGA_CONTROLREG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'controlReg', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(1006)
class PARFPGA_POWERUPTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'powerupThr', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'f'),
    ])


@parameter(1007)
class PARFPGA_INTMAT245_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'interfaceMatrix', dimension = 32, datatype = 'B'),
    ])


@parameter(1008)
class PARFPGA_TYPE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'type', dimension = 1, datatype = 'I'),
    ])


@parameter(1009)
class PARFPGA_GLOBALCONF_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'configuration', dimension = 1, datatype = 'I'),
    ])


@parameter(1010)
class PARFPGA_HDLCPINMODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'pinMode', dimension = 1, datatype = 'I'),
    ])

@parameter(1012)
class PARFPGA_ALARMTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'alarmThr', dimension = 1, datatype = 'I'),
    ])


@parameter(1013)
class PARFPGA_PPTCONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'pptValue', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'pptPulseWidth', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(1014)
class PARFPGA_AUTOWAKEUP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enableAutoWakeup', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'interval', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'retries', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
    ])




"""
PARNMEA
"""
@parameter(1300)
class PARNMEA_COM_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved3', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'baud', dimension = 1, datatype = 'I'),
    ])


@parameter(1301)
class PARNMEA_ENABLE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'qualityMode', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'selectionSwitch', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved4', dimension = 1, datatype = 'B'),
    ])


@parameter(1302)
class PARNMEA_TXMASK_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'txMask', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'txMaskUDP', dimension = 1, datatype = 'I'),
    ])


@parameter(1303)
class PARNMEA_DECPLACES_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'digitsPos', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'digitsHdg', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
    ])


@parameter(1304)
class PARNMEA_RATE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'divisor', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'divisorUDP', dimension = 1, datatype = 'I'),
    ])


@parameter(1305)
class PARNMEA_UDP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'serverAddress', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'port', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved3', dimension = 1, datatype = 'H'),
    ])


"""
PARARINC429
"""
@parameter(1400)
class PARARINC429_CONFIG_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'port', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved3', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'highSpeed', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved4', dimension = 1, datatype = 'H'),
    ])

@parameter(1401)
class PARARINC429_LIST_Payload(DefaultParameterPayload):
    __sub_payload = [
        [
            PayloadItem(name = f'channel_{idx}', dimension = 1, datatype = 'B'), 
            PayloadItem(name = f'label_{idx}', dimension = 1, datatype = 'B'),
            PayloadItem(name = f'datIdx_{idx}', dimension = 1, datatype = 'B'),
            PayloadItem(name = f'enable_{idx}', dimension = 1, datatype = 'B'),
            PayloadItem(name = f'range_{idx}', dimension = 1, datatype = 'd'),
            PayloadItem(name = f'scf_{idx}', dimension = 1, datatype = 'd'),
            PayloadItem(name = f'width_{idx}', dimension = 1, datatype = 'B'),
            PayloadItem(name = f'period_{idx}', dimension = 1, datatype = 'I'),
            PayloadItem(name = f'timer{idx}', dimension = 1, datatype = 'I'),
        ] for idx in range(0, 32)
    ]
    parameter_payload = Message([
        logitem for log in __sub_payload for logitem in log
    ])

"""
IO
"""
@parameter(1500)
class PARIO_HW245_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'configIO', dimension = 1, datatype = 'I'),
    ])


@parameter(1501)
class PARIO_HW288_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'toDef', dimension = 1, datatype = 'I'),
    ])


"""
Messages
"""
MessagePayloadDictionary = dict()
def message(message_id):
    def decorator(cls):
        cls.message_id = message_id
        MessagePayloadDictionary[message_id] = cls
        return cls

    return decorator

@message(MessageID.RESPONSE)
class ResponsePayload(ProtocolPayload):
    def __init__(self, msgLength):
        self.message_description = Message([
            PayloadItem(name = 'responseID', dimension = 1, datatype = 'H'),
            PayloadItem(name = 'repsonseLength', dimension = 1, datatype = 'H'),
            PayloadItem(name = 'responseText', dimension = msgLength-24, datatype = 's'),
        ])
        super().__init__()


@message(0x40)
class POSTPROC_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'acc', dimension = 3, datatype = 'f', unit = 'm/s²', description = 'Specific force'),
        PayloadItem(name = 'omg', dimension = 3, datatype = 'f', unit = 'rad/s', description = 'Angular rate'),
        PayloadItem(name = 'delta_theta', dimension = 12, datatype = 'f'),
        PayloadItem(name = 'delta_v', dimension = 12, datatype = 'f'),
        PayloadItem(name = 'q_nb', dimension = 4, datatype = 'd'),
        PayloadItem(name = 'pos', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'vel', dimension = 3, datatype = 'd', unit = 'm/s', description = 'NED Velocity'),
        PayloadItem(name = 'sysStat', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'ekfStat', dimension = 2, datatype = 'I'),
        PayloadItem(name = 'odoSpeed', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'odoTicks', dimension = 1, datatype = 'i'),
        PayloadItem(name = 'odoInterval', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'odoTrigEvent', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'odoNextEvent', dimension = 1, datatype = 'I'),
    ])


@message(0x03)
class INSSOL_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'acc', dimension = 3, datatype = 'f', unit = 'm/s²', description = 'Acceleration'),
        PayloadItem(name = 'omg', dimension = 3, datatype = 'f', unit = 'rad/s', description = 'Specific force'),
        PayloadItem(name = 'rpy', dimension = 3, datatype = 'f', unit = 'rad', description = 'Angle'),
        PayloadItem(name = 'vel', dimension = 3, datatype = 'f', unit = 'm/s', description = 'Velocity'),
        PayloadItem(name = 'lon', dimension = 1, datatype = 'd', unit = 'rad', description = 'Longitude'),
        PayloadItem(name = 'lat', dimension = 1, datatype = 'd', unit = 'rad', description = 'Latitude'),
        PayloadItem(name = 'alt', dimension = 1, datatype = 'f', unit = 'm', description = 'Altitude'),
        PayloadItem(name = 'undulation', dimension = 1, datatype = 'h', unit = 'cm', description = 'Undulation'),
        PayloadItem(name = 'DatSel', dimension = 1, datatype = 'H'),
    ])

@message(0x47)
class INSSOLECEF_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'acc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'omg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'pos_ecef', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'vel_ecef', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'q_nb', dimension = 4, datatype = 'f'),
    ])

class IMU_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'acc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'omg', dimension = 3, datatype = 'f'),
    ])


@message(0x00)
class IMURAW_Payload(IMU_Payload):
    pass

@message(0x01)
class IMUCORR_Payload(IMU_Payload):
    pass

@message(0x02)
class IMUCOMP_Payload(IMU_Payload):
    pass

@message(0x0D)
class INSROTTEST_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'accNED', dimension = 3, datatype = 'd'),
    ])


@message(0x20)
class STATFPGA_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'usParID', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'uReserved', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucAction', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'uiPowerStatLower', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiPowerStatUpper', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'usFpgaStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'usSupervisorStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'ucImuStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucTempStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'usRes', dimension = 1, datatype = 'H'),
    ])


@message(0x19)
class SYSSTAT_Payload(ProtocolPayload):
    def from_bytes(self, inBytes):
        item_list = [
            PayloadItem(name = 'statMode', dimension = 1, datatype = 'I'),
            PayloadItem(name = 'sysStat', dimension = 1, datatype = 'I'),
        ]
        stat_mode = struct.unpack("I", inBytes[:4])[0]
        item_list += self._get_payload(stat_mode)
        self.message_description = Message(item_list)
        super().from_bytes(inBytes)

    def _get_payload(self, stat_mode):
        item_list = []
        if(stat_mode & (1 << 0)):
            item_list += [PayloadItem(name = 'imuStat', dimension = 1, datatype = 'I')]
        if(stat_mode & (1 << 1)):
            item_list += [PayloadItem(name = 'gnssStat', dimension = 1, datatype = 'I')]
        if(stat_mode & (1 << 2)):
            item_list += [PayloadItem(name = 'magStat', dimension = 1, datatype = 'I')]
        if(stat_mode & (1 << 3)):
            item_list += [PayloadItem(name = 'madcStat', dimension = 1, datatype = 'I')]
        if(stat_mode & (1 << 4)):
            item_list += [PayloadItem(name = 'ekfStat', dimension = 2, datatype = 'I')]
        if(stat_mode & (1 << 5)):
            item_list += [PayloadItem(name = 'ekfGeneralStat', dimension = 1, datatype = 'I')]
        if(stat_mode & (1 << 6)):
            item_list += [PayloadItem(name = 'addStat', dimension = 4, datatype = 'I')]
        if(stat_mode & (1 << 7)):
            item_list += [PayloadItem(name = 'serviceStat', dimension = 1, datatype = 'I')]
        if(stat_mode & (1 << 8)):
            item_list += [PayloadItem(name = 'remainingAlignTime', dimension = 1, datatype = 'f')]
        return item_list


@message(0x04)
class INSRPY_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'rpy', dimension = 3, datatype = 'f'),
    ])


@message(0x05)
class INSDCM_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'DCM', dimension = 9, datatype = 'f'),
    ])


@message(0x06)
class INSQUAT_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'quat', dimension = 4, datatype = 'f'),
    ])


@message(0x0A)
class INSPOSLLH_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'lon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'lat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'alt', dimension = 1, datatype = 'f'),
    ])


@message(0x0C)
class INSPOSUTM_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'zone', dimension = 1, datatype = 'i'),
        PayloadItem(name = 'easting', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'northing', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'height', dimension = 1, datatype = 'f'),
    ])


@message(0x0B)
class INSPOSECEF_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'pos', dimension = 3, datatype = 'd'),
    ])


class INSVEL_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'vel', dimension = 3, datatype = 'f'),
    ])


@message(0x07)
class INSVELNED_Payload(INSVEL_Payload):
    pass

@message(0x08)
class INSVELECEF_Payload(INSVEL_Payload):
    pass

@message(0x09)
class INSVELBODY_Payload(INSVEL_Payload):
    pass

@message(0x23)
class INSVELENU_Payload(INSVEL_Payload):
    pass

@message(0x18)
class MAGDATA_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'field', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'magHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'magBank', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'magElevation', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'magDeviation', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'status', dimension = 1, datatype = 'I'),
    ])


@message(0x17)
class AIRDATA_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'TAS', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'IAS', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'baroAlt', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'baroAltRate', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'Pd', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'Ps', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'OAT', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'estBias', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'estScaleFactor', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'estBiasStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'estScaleFactorStdDev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'status', dimension = 1, datatype = 'I'),
    ])


@message(0x0F)
class EKFSTDDEV_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'pos', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'vel', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'tilt', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'biasAcc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'biasOmg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'scfAcc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'scfOmg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'scfOdo', dimension = 1, datatype = 'f'),
    ])


@message(0x28)
class EKFSTDDEV2_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'pos', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'vel', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'rpy', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'biasAcc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'biasOmg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'fMaAcc', dimension = 9, datatype = 'f'),
        PayloadItem(name = 'fMaOmg', dimension = 9, datatype = 'f'),
        PayloadItem(name = 'scfOdo', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fMaOdo', dimension = 2, datatype = 'f'),
    ])


@message(0x27)
class EKFERROR2_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'biasAcc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'biasOmg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'fMaAcc', dimension = 9, datatype = 'f'),
        PayloadItem(name = 'fMaOmg', dimension = 9, datatype = 'f'),
        PayloadItem(name = 'scfOdo', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'maOdo', dimension = 2, datatype = 'f'),
    ])


@message(0x10)
class EKFERROR_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'biasAcc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'biasOmg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'scfAcc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'scfOmg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'scfOdo', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'maOdo', dimension = 2, datatype = 'f'),
    ])


@message(0x11)
class EKFTIGHTLY_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'ucSatsAvailablePSR', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsUsedPSR', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsAvailableRR', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsUsedRR', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsAvailableTDCP', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsUsedTDCP', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucRefSatTDCP', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'usReserved', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'uiUsedSatsPSR_GPS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiOutlierSatsPSR_GPS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiUsedSatsPSR_GLONASS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiOutlierSatsPSR_GLONASS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiUsedSatsRR_GPS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiOutlierSatsRR_GPS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiUsedSatsRR_GLONASS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiOutlierSatsRR_GLONASS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiUsedSatsTDCP_GPS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiOutlierSatsTDCP_GPS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiUsedSatsTDCP_GLONASS', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'uiOutlierSatsTDCP_GLONASS', dimension = 1, datatype = 'I'),
    ])


@message(0x29)
class EKFPOSCOVAR_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'fPosCovar', dimension = 9, datatype = 'f'),
    ])


@message(0x21)
class POWER_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'power', dimension = 32, datatype = 'f'),
    ])


@message(0x22)
class TEMP_Payload(ProtocolPayload):
    
    message_description = Message([
        PayloadItem(name = 'temp_power_pcb', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'temp_switcher', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'temp_oem628', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'temp_oem615', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'temp_cpu', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'temp_acc', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'temp_omg', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'temp_other', dimension = 5, datatype = 'f'),
    ])


@message(0x1F)
class HEAVE_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'StatFiltPos', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'AppliedFreqHz', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'AppliedAmplMeter', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'AppliedSigWaveHeightMeter', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'PZpos', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ZDpos', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ZDvel', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'AccZnavDown', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'HeavePosVelDown', dimension = 2, datatype = 'd'),
        PayloadItem(name = 'HeaveAlgoStatus1', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'HeaveAlgoStatus2', dimension = 1, datatype = 'I'),
    ])


@message(0x24)
class CANSTAT_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'uiErrorMask', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'ucControllerStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucTransceiverStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucProtocolStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucProtocolLocation', dimension = 1, datatype = 'B'),
    ])


@message(0x1D)
class ARINC429STAT_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'uiStatus', dimension = 1, datatype = 'I'),
    ])


@message(0x26)
class TIME_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'sysTime', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'ImuInterval', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'TimeSincePPS', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'PPS_IMUtime', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'PPS_GNSStime', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'GNSSbias', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'GNSSbiasSmoothed', dimension = 1, datatype = 'd'),
    ])


@message(0x12)
class GNSSSOL_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'lon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'lat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'alt', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'undulation', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'velNED', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdDevPos', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdDevVel', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'solStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'posType', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'pdop', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'satsUsed', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'solTracked', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'res', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'diffAge', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'solAge', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'gnssStatus', dimension = 1, datatype = 'I'),
    ])


@message(0x14)
class GNSSTIME_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'utcOffset', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'offset', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'year', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'month', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'day', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'hour', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'minute', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'millisec', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'status', dimension = 1, datatype = 'I'),
    ])


@message(0x15)
class GNSSSOLCUST_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'dLon', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'dLat', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'fAlt', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fUndulation', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fStdDev_Pos', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'fVned', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'fStdDev_Vel', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'fDisplacement', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'fStdDev_Displacement', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'usSolStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'fDOP', dimension = 2, datatype = 'f'),
        PayloadItem(name = 'ucSatsPos', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsVel', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsDisplacement', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'usReserved', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'fDiffAge', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fSolAge', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'uiGnssStatus', dimension = 1, datatype = 'I'),
    ])


@message(0x33)
class GNSSHDG_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'hdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDevHdg', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'pitch', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'stdDevPitch', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'solStat', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'solType', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'res', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'satsUsed', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'satsTracked', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'gnssStatus', dimension = 1, datatype = 'I'),
    ])


@message(0x1B)
class GNSSLEVERARM_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'primary', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdDevPrimary', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'relative', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'stdDevRelative', dimension = 3, datatype = 'f'),
    ])


@message(0x1C)
class GNSSVOTER_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'ucSatsUsed_INT', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'ucSatsUsed_EXT', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'usReserved', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'fStdDevHDG_INT', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fStdDevHDG_EXT', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fStdDevPOS_INT', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fStdDevPOS_EXT', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'uiStatus', dimension = 1, datatype = 'I'),
    ])


@message(0x1E)
class GNSSHWMON_Payload(ProtocolPayload):
    message_description = None
    def __init__(self):
        if type(self).message_description is None:
            item_list = []
            for idx in range(0, 16):
                item_list += [PayloadItem(name = 'val %d' % idx, dimension = 1, datatype = 'f'),
                              PayloadItem(name = 'status %d' % idx, dimension = 1, datatype = 'I')]
            type(self).message_description = Message(item_list)



@message(0x25)
class GNSSSATINFO_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'svID', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'dPositionECEF', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'dVelocityECEF', dimension = 3, datatype = 'd'),
        PayloadItem(name = 'fClockError', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fIonoError', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fTropoError', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fElevation', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'fAzimuth', dimension = 1, datatype = 'f'),
    ])


@message(0x38)
class GNSSALIGNBSL_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'east', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'north', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'up', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'eastStddev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'northStddev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'upStddev', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'solStatus', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'posVelType', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'satsTracked', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'satsUsedInSolution', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'extSolStat', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved', dimension = 1, datatype = 'B'),
    ])


@message(0x16)
class WHEELDATA_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'odoSpeed', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'ticks', dimension = 1, datatype = 'i'),
    ])


@message(0x32)
class WHEELDATADBG_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'odoSpeed', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'ticks', dimension = 1, datatype = 'i'),
        PayloadItem(name = 'interval', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'trigEvent', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'trigNextEvent', dimension = 1, datatype = 'I'),
    ])


@message(0x34)
class EVENTTIME_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'dGpsTime_EVENT_0', dimension = 1, datatype = 'd'),
        PayloadItem(name = 'dGpsTime_EVENT_1', dimension = 1, datatype = 'd'),
    ])


@message(0x35)
class OMGINT_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'omgINT', dimension = 3, datatype = 'f'),
        PayloadItem(name = 'omgINTtime', dimension = 1, datatype = 'f'),
    ])


@message(0x36)
class ADC24STATUS_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'uiRRidx', dimension = 4, datatype = 'I'),
        PayloadItem(name = 'uiRRvalue', dimension = 4, datatype = 'I'),
    ])


@message(0x37)
class ADC24DATA_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'acc', dimension = 3, datatype = 'I'),
        PayloadItem(name = 'frameCounter', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'temperature', dimension = 1, datatype = 'h'),
        PayloadItem(name = 'errorStatus', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'intervalCounter', dimension = 3, datatype = 'B'),
    ])


@message(0x42)
class CSACDATA_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'status', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'alarm', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'serialNum', dimension = 32, datatype = 's'),
        PayloadItem(name = 'mode', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'contrast', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'laserCurrent', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'tcx0', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'heatP', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'sig', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'temperature', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'steer', dimension = 1, datatype = 'i'),
        PayloadItem(name = 'atune', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'phase', dimension = 1, datatype = 'i'),
        PayloadItem(name = 'discOk', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'timeSincePowerOn', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'timeSinceLock', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'dataValid', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'fwStatus', dimension = 1, datatype = 'H'),
    ])

@message(0x57)
class TAG_Payload(ProtocolPayload):
    message_description = Message([
        PayloadItem(name = 'tag', dimension = 128, datatype = 's')
    ])



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
