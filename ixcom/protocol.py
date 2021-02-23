import collections
from collections.abc import Iterable
import struct
from enum import Flag, IntEnum, IntFlag, auto
from typing import NamedTuple

from . import crc16
from .exceptions import ParseError


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
    '''Enumeration for response IDs'''
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
    '''Enumeration for the mask bits in the datsel field of the INSSOL message'''
    
    IMURAW  = 0b0000000000000001
    '''Inertial data as measured by the ISA'''
    IMUCORR = 0b0000000000000010
    '''Inertial data as measured by the ISA, corrected for sensor errors (scale factor, bias, misalignments, nontorthogonality, etc...) estimated by the EKF'''
    IMUCOMP = 0b0000000000000100
    '''Inertial data corrected for sensor errors (scale factor, bias, misalignments, nontorthogonality, etc...) estimated by the EKF and compensated for gravity/earth rate'''
    VELNED  = 0b0000000000001000
    '''Velocity is in NED frame'''
    VELECEF = 0b0000000000010000
    '''Velocity is in ECEF frame'''
    VELBDY  = 0b0000000000100000
    '''Velocity is in body frame'''
    ALTITUDE_WGS84 = 0b0000000001000000
    '''Altitude is height above WGS84 ellipsoid'''
    ALTITUDE_MSL     = 0b0000000010000000
    '''Altitude is height above geoid'''
    ALTITUDE_BARO = 0b0000000100000000
    '''Altitude is baro altitude'''
    WGS84POS= 0b0000001000000000
    '''Position is longitude, latitude, altitude'''
    ECEFPOS = 0b0000010000000000
    '''Position is ECEF X,Y,Z'''

class MessageID(IntEnum):
    '''Enumeration for special message IDs'''
    COMMAND       = 0xFD
    RESPONSE      = 0xFE
    PARAMETER     = 0xFF

class EkfCommand(IntEnum):
    '''Enumeration for the EKF command subcommands'''
    ALIGN           = 0
    SAVEPOS         = 1
    SAVEHDG         = 2
    SAVEANTOFFSET   = 3
    FORCED_ZUPT     = 4
    ALIGN_COMPLETE  = 5

class LogTrigger(IntEnum):
    '''Logs can be triggered with a certain divider from the inertial sensor samples, polled, or triggered by events.'''
    SYNC          = 0
    EVENT         = 1
    POLLED        = 2

class LogCommand(IntEnum):
    '''This enum contains possible log command'''

    ADD         = 0
    '''Add the log'''

    STOP        = 1
    '''Stop the current log, but do not remove from loglist'''

    START       = 2
    '''Start a previously stopped log'''

    CLEAR       = 3
    '''Clear log from loglist'''

    CLEAR_ALL   = 4
    '''Clear all logs from loglist'''
    STOP_ALL    = 5
    '''Stop all logs'''

    START_ALL   = 6
    '''Start all logs'''

class StartupPositionMode(IntEnum):
    '''Enumeration for the available startup position modes'''

    GNSSPOS     = 0
    '''Feed initial position from GNSS'''

    STOREDPOS   = 1
    '''Feed initial position from stored position'''

    FORCEDPOS   = 2
    '''Feed initial position from forced position'''

    CURRENTPOS  = 3
    '''Feed initial position from current position'''

class StartupHeadingMode(IntEnum):
    '''Enumeration for the available startup heading modes'''

    DEFAULT     = 0
    '''Start with unknown heading'''

    STOREDHDG   = 1
    '''Feed initial heading from stored heading'''

    FORCEDHDG   = 2
    '''Feed initial heading from forced heading'''

    MAGHDG      = 3
    '''Feed initial heading from magnetic heading'''

    DUALANTHDG  = 4
    '''Feed initial heading from dual antenna heading'''

class AlignmentMode(IntEnum):
    '''Enumeration for the available alignment modes'''

    STATIONARY = 0
    '''Stationary alignment, INS has to be at standstill'''

    IN_MOTION = 1
    '''In-motion alignment, INS can move arbitrarily, needs aiding (e.g. GNSS)'''

class ExtAidingTimeMode(IntEnum):
    '''External aiding can be executed with two timestamp modes.'''

    GPS_SEC_OF_WEEK = 0
    '''The time field contains the second of week'''

    LATENCY = 1
    '''The time field contains the measurement latency'''

class GlobalAlignStatus(IntEnum):
    '''The alignment status will transition from levelling to aligning to alignment complete. 
    Only if the heading standard deviation falls below the threshold defined in PAREKF_HDGPOSTHR, the alignment status will be "heading good"
    '''
    LEVELLING = 0
    '''Roll and pitch are being estimated from accelerometer measurement'''

    ALIGNING = 1
    '''Heading is being estimated from available aiding data'''
    
    ALIGN_COMPLETE = 2
    '''Alignment is complete, the system is allowed to be moved.'''

    HDG_GOOD = 3
    '''Heading standard deviation is lower than the threshold defined in PAREKF_HDGPOSTHR'''

class GlobalPositionStatus(IntEnum):
    '''The position status depends on the 3D position standard deviation'''

    BAD = 0
    '''Position standard deviation is worse than the medium position standard deviation threshold defined in PAREKF_HDGPOSTHR'''
    
    MEDIUM = 1
    '''Position standard deviation is better than the medium position standard deviation threshold defined in PAREKF_HDGPOSTHR, 
    but worse than the high accuracy position standard deviation threshold'''

    HIGH = 2
    '''Position standard deviation is better than the high accuracy position standard deviation threshold'''

    UNDEFINED = 3
    '''Position has not yet been set'''

class GlobalStatusBit(IntFlag):
    '''The global status is contained in the footer of every iXCOM message'''

    HWERROR = auto()
    '''The hardware has detected an error condition during build-in-test'''

    COMERROR = auto()
    '''There is a communication error between the navigation processor and the IMU'''
    
    NAVERROR = auto()
    '''The navigation solution is erroneous, e.g. due to sensor overranges'''

    CALERROR = auto()
    '''The calibration routines have encountered an error, e.g. due to temperature being out of range'''

    GYROOVR = auto()
    '''A gyro overrange has been encountered'''

    ACCOVR = auto()
    '''An accelerometer overrange has been encountered'''

    GNSSINVALID = auto()
    '''No valid GNSS solution available'''

    STANDBY = auto()
    '''The system is in standby-mode, i.e. the inertial sensor assembly is not powered up.'''

    DYNAMICALIGN = auto()
    '''The system is in dynamic alignment.'''

    TIMEINVALID = auto()
    '''The system time has not been set from GNSS'''

    NAVMODE = auto()
    '''The system is in navigation mode'''

    AHRSMODE = auto()
    '''The system is in fallback AHRS mode'''

    @property
    def alignment_status(self):
        return GlobalAlignStatus((self.value & 0x3000) >> 12)

    @property
    def position_status(self):
        return GlobalPositionStatus((self.value & 0xc000) >> 14)

class SysstatBit(IntFlag):
    '''An enumeration for the status bits in the extended system status'''
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
    '''An enumeration for the status bits in the lower EKF status word'''
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
    '''An enumeration for the status bits in the higher EKF status word'''
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

class XcomCommandParameter(IntEnum):
    '''Parameters to the XCOM command'''
    channel_close  = 0
    '''Close the current XCOM channel'''
    channel_open   = 1
    '''Open an XCOM channel'''
    reboot         = 2
    '''Reboot the device'''
    _warmreset      = 3
    '''Do a warm reset'''
    _reset_omg_int  = 4
    '''Reset integration for OMGINT log'''
    _update_svn     = 5
    '''Update firmware from SVN'''
    _reset_timebias = 6
    '''Reset the time bias between system time and GNSS time'''
    
class ParameterAction(IntEnum):
    '''Allowed parameter actions'''
    CHANGING = 0
    REQUESTING = 1

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

    def c_type(self):
        d = {
            'b': 'int8_t',
            'B': 'uint8_t',
            'h': 'int16_t',
            'H': 'uint16_t',
            'i': 'int32_t',
            'I': 'uint32_t',
            'f': 'int8_t',
            'd': 'int8_t',
            's': 'char',
        }
        result = f'{d.get(self.datatype, "struct")} {self.name}'
        if self.dimension > 1:
            result += f' [{self.dimension}]'
        return result

    def describe(self):
        result = self.c_type()
        if self.description:
            result += ': ' + self.description
        if self.unit:
            result += f' (Unit: {self.unit})'
        return result

    def get_struct_string(self):
        if isinstance(self.datatype, str):
            struct_string = ''
            if self.dimension != 1:
                struct_string += '%d' % self.dimension
            struct_string += self.datatype
        elif isinstance(self.datatype, Message):
            struct_string = self.datatype.get_struct_string()*self.dimension
        return struct_string

    def get_size(self):
        basic_sizes = {'b': 1, 'B': 1, 's': 1, 'h': 2, 'H': 2, 'i': 4, 'I': 4, 'f': 4, 'd': 8}
        if isinstance(self.datatype, str):
            return basic_sizes[self.datatype]*self.dimension
        elif isinstance(self.datatype, Message):
            return self.datatype.get_size()*self.dimension

    def get_null_item(self):
        if isinstance(self.datatype, str):
            if self.datatype == 's':
                return b'\0'*self.dimension
            if self.datatype in 'BbHhIiLlQq':
                dt_null = 0
            elif self.datatype in 'fd':
                dt_null = 0.0
        elif isinstance(self.datatype, Message):
            dt_null = self.datatype.get_null_item()
        else:
            raise ValueError('Illegal datatype "{}"'.format(self.datatype))

        if self.dimension == 1:
            return dt_null
        else:
            return [dt_null for _ in range(0, self.dimension)]

    def consume(self, input_values):
        output_values = []
        if isinstance(self.datatype, str):
            if self.datatype == 's':
                num_to_pop = 1
            else:
                num_to_pop = self.dimension
            for _ in range(0, num_to_pop):
                output_values.append(input_values.pop(0))
        else:
            for _ in range(0, self.dimension):
                output_values.append(self.datatype.consume(input_values))
        if len(output_values) == 1:
            return {self.name: output_values[0]}
        else:
            return {self.name: output_values}

class Message:
    def __init__(self, item_list: [PayloadItem], name = ''):
        self.item_list = item_list
        self.data = self.generate_data_dict()
        self.struct_inst = struct.Struct(self.generate_final_struct_string())
        self.name = name

    def unpack_from(self, buffer, offset = 0):
        try:
            values = list(self.struct_inst.unpack_from(buffer, offset))
            return self.consume(values)
        except struct.error:
            raise ParseError(f'Could not convert {self.name}')

    def __repr__(self):
        result = 'Message([...])'
        return result

    def describe(self):
        result = ''
        for payload_item in self.item_list:
            result += f'\t- {payload_item.describe()}\n'
        return result

    def get_struct_string(self):
        result = ''
        for item in self.item_list:
            result += item.get_struct_string()
        return result

    def generate_final_struct_string(self):
        return '=' + self.get_struct_string()

    def generate_data_dict(self):
        data = collections.OrderedDict()
        for item in self.item_list:
            data[item.name] = item.get_null_item()
        return data

    def get_null_item(self):
        d = dict()
        for item in self.item_list:
            d[item.name] = item.get_null_item()
        return d

    def get_size(self):
        return self.struct_inst.size

    def consume(self, values):
        data = dict()
        for item in self.item_list:
            data.update(item.consume(values))
        return data

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

    def __init__(self, varsizehelper=None):
        if varsizehelper:
            self._get_varsize_message_description(varsizehelper)
            type(self)._structString = None
            type(self).item_list = self.item_list
            type(self).message_description = self.message_description
            self._structString = self.message_description.generate_final_struct_string()
        if type(self)._structString is None:
            if type(self).message_description is not None:
                type(self)._structString = self.message_description.generate_final_struct_string()
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
                if isinstance(value[0], dict):
                    for curd in value:
                        values += curd.values()
                else:
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
        self.header  = ProtocolHeader()
        self.payload = ProtocolPayload()
        self.bottom  = ProtocolBottom()

    def to_bytes(self):
        self.header.msgLength = self.size()
        header = self.header.to_bytes()
        payload = self.payload.to_bytes()
        bottom = self.bottom.to_bytes()
        msgBytes = header + payload + bottom[:2]
        self.bottom.crc = crc16.crc16xmodem(bytes(msgBytes))
        bottom = self.bottom.to_bytes()
        return header + payload + bottom

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
        cls.__doc__ = f'''Message (ID = {hex(message_id)}) with the following payload:\n\n{cls.message_description.describe()}'''
        cls.message_id = message_id
        MessagePayloadDictionary[message_id] = cls
        return cls

    return decorator


ParameterPayloadDictionary = dict()
def parameter(parameter_id):
    def decorator(cls):
        cls.__doc__ = f'''Parameter (ID = {parameter_id}) with the following payload:\n\n{cls.parameter_payload.describe()}'''
        cls.parameter_id = parameter_id
        ParameterPayloadDictionary[parameter_id] = cls
        return cls

    return decorator

CommandPayloadDictionary = dict()
def command(command_id):
    def decorator(cls):
        cls.__doc__ = f'''Command (ID = {command_id}) with the following payload:\n\n{cls.command_payload.describe()}'''
        cls.command_id = command_id
        CommandPayloadDictionary[command_id] = cls
        return cls

    return decorator


def getMessageWithID(msgID, varsizehelper=None):
    message = ProtocolMessage()
    message.header.msgID = msgID
    if msgID in MessagePayloadDictionary:
        if varsizehelper is None:
            message.payload = MessagePayloadDictionary[msgID]()
        else:
            message.payload = MessagePayloadDictionary[msgID](varsizehelper)
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
