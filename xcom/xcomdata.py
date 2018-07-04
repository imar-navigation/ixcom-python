import collections
import struct
import crc16
from enum import IntEnum


class XcomResponse(IntEnum):
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
    IMURAW        = 0x00
    IMUCORR       = 0x01
    IMUCOMP       = 0x02
    INSSOL        = 0x03
    INSRPY        = 0x04
    INSDCM        = 0x05
    INSQUAT       = 0x06
    INSVELNED     = 0x07
    INSVELECEF    = 0x08
    INSVELBODY    = 0x09
    INSVELENU     = 0x23
    INSPOSLLH     = 0x0A
    INSPOSECEF    = 0x0B
    INSPOSUTM     = 0x0C
    INSROTTEST    = 0x0D
    POSTPROC      = 0x40

    EKFSTDDEV     = 0x0F
    EKFSTDDEV2    = 0x28
    EKFERROR      = 0x10
    EKFERROR2     = 0x27
    EKFTIGHTLY    = 0x11
    EKFPOSCOVAR   = 0x29

    GNSSSOL       = 0x12
    INSGNDSPEED   = 0x13
    GNSSTIME      = 0x14
    GNSSSOLCUST   = 0x15
    GNSSHDG       = 0x33
    GNSSLEVERARM  = 0x1B
    GNSSVOTER     = 0x1C
    GNSSHWMON     = 0x1E
    GNSSSATINFO   = 0x25
    GNSSALIGNBSL  = 0x38

    WHEELDATA     = 0x16
    AIRDATA       = 0x17
    MAGDATA       = 0x18
    SYSSTAT       = 0x19
    ARINC429STAT  = 0x1D
    HEAVE         = 0x1F
    STATFPGA      = 0x20
    POWER         = 0x21
    TEMP          = 0x22
    CANSTAT       = 0x24
    TIME          = 0x26

    IMUDBG        = 0x30
    IMUCAL        = 0x31
    WHEELDATADBG  = 0x32
    EVENTTIME     = 0x34
    OMGINT        = 0x35

    ADC24STATUS   = 0x36
    ADC24DATA     = 0x37

    COMMAND       = 0xFD
    RESPONSE      = 0xFE
    PARAMETER     = 0xFF

class CommandID(IntEnum):
    LOG     = 0x0
    EXT     = 0x1
    CAL     = 0x2
    CONF    = 0x3
    EKF     = 0x4
    XCOM    = 0x5
    FPGA    = 0x6
    EXTAID  = 0x7
    PCTRL   = 0x8
    USR     = 0x9

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

class ParameterID(IntEnum):
    PARSYS_PRJNUM           = 0
    PARSYS_PARTNUM          = 1
    PARSYS_SERIALNUM        = 2
    PARSYS_MFG              = 3
    PARSYS_CALDATE          = 4
    PARSYS_FWVERSION        = 5
    PARSYS_NAVLIB           = 6
    PARSYS_EKFLIB           = 7
    PARSYS_EKFPARSET        = 8
    PARSYS_NAVNUM           = 9
    PARSYS_NAVPARSET        = 10
    PARSYS_MAINTIMING       = 11
    PARSYS_PRESCALER        = 12
    PARSYS_UPTIME           = 13
    PARSYS_OPHOURCOUNT      = 14
    PARSYS_BOOTMODE         = 15
    PARSYS_FPGAVER          = 16
    PARSYS_CONFIGCRC        = 17
    PARSYS_OSVERSION        = 18
    PARSYS_SYSNAME          = 19

    PARIMU_MISALIGN         = 105
    PARIMU_TYPE             = 107
    PARIMU_LATENCY          = 108
    PARIMU_CALIB            = 109
    PARIMU_CROSSCOUPLING    = 110
    PARIMU_REFPOINTOFFSET   = 111
    PARIMU_BANDSTOP         = 112
    PARIMU_COMPMETHOD       = 113
    PARIMU_ACCLEVERARM      = 114
    PARIMU_STRAPDOWNCONF    = 115

    PARGNSS_PORT            = 200
    PARGNSS_BAUD            = 201
    PARGNSS_LATENCY         = 203
    PARGNSS_ANTOFFSET       = 204
    PARGNSS_RTKMODE         = 207
    PARGNSS_AIDFRAME        = 209
    # PARGNSS_RTCMV3AIDING    = 210 --> variable payload testing is not implemented yet
    PARGNSS_DUALANTMODE     = 211
    PARGNSS_LOCKOUTSYSTEM   = 212
    PARGNSS_RTCMV3CONFIG    = 213
    PARGNSS_NAVCONFIG       = 214
    PARGNSS_STDDEV          = 215
    PARGNSS_VOTER           = 216
    PARGNSS_MODEL           = 217
    PARGNSS_VERSION         = 218
    PARGNSS_RTKSOLTHR       = 219
    PARGNSS_TERRASTAR       = 220
    PARGNSS_REFSTATION      = 221
    PARGNSS_FIXPOS          = 222
    PARGNSS_POSAVE          = 223
    PARGNSS_CORPORTCFG      = 224
    
    PARMAG_COM              = 300
    PARMAG_PERIOD           = 302
    PARMAG_MISALIGN         = 304
    PARMAG_CAL              = 307
    PARMAG_CALSTATE         = 308
    PARMAG_FOM              = 309
    PARMAG_CFG              = 310
    PARMAG_ENABLE           = 311

    PARMADC_ENABLE          = 400
    PARMADC_LEVERARM        = 401
    PARMADC_LOWPASS         = 402

    PARMON_LEVEL            = 500
    PARMON_TPYE             = 501
    PARMON_PORT             = 502
    PARMON_BAUD             = 503

    PARREC_CONFIG           = 600
    PARREC_START            = 603
    PARREC_STOP             = 604
    PARREC_POWER            = 605
    PARREC_DISKSPACE        = 607
    PARREC_AUXILIARY        = 608
    
    PAREKF_ALIGNMODE        = 700
    PAREKF_ALIGNTIME        = 701
    PAREKF_COARSETIME       = 702
    PAREKF_VMP              = 703
    PAREKF_AIDING           = 704
    PAREKF_DELAY            = 706
    PAREKF_STARTUP          = 707
    PAREKF_HDGPOSTHR        = 708
    PAREKF_SMOOTH           = 709
    PAREKF_ZUPT             = 712
    PAREKF_DEFPOS           = 714
    PAREKF_DEFHDG           = 715
    PAREKF_OUTLIER          = 716
    PAREKF_POWERDOWN        = 717
    PAREKF_EARTHRAD         = 718
    PAREKF_STOREDPOS        = 719
    PAREKF_ALIGNZUPTSTDDEV  = 720
    PAREKF_POSAIDSTDDEVTHR  = 721
    PAREKF_SCHULERMODE      = 722
    PAREKF_STOREDATT        = 723
    PAREKF_ODOMETER         = 724
    PAREKF_ODOBOGIE         = 725
    PAREKF_GNSSLEVERARMEST  = 726
    PAREKF_GNSSAIDRATE      = 727
    PAREKF_KINALIGNTHR      = 728
    PAREKF_PDOPTHR          = 729
    PAREKF_DUALANTAID       = 730
    PAREKF_STARTUPV2        = 731
    PAREKF_MAGATTAID        = 732
    PAREKF_MADCAID          = 733
    PAREKF_ALIGNMENT        = 734
    PAREKF_GRAVITYAID       = 735
    PAREKF_FEEDBACK         = 736
    PAREKF_ZARU             = 737
    PAREKF_IMUCONFIG        = 738
    PAREKF_ZUPTCALIB        = 739
    PAREKF_STATEFREEZE      = 740
    PAREKF_RECOVERY         = 741
    
    PARDAT_POS              = 800
    PARDAT_VEL              = 801
    PARDAT_IMU              = 802
    PARDAT_SYSSTAT          = 803

    PARXCOM_SERIALPORT      = 902
    PARXCOM_NETCONFIG       = 903
    PARXCOM_LOGLIST         = 905
    PARXCOM_AUTOSTART       = 906
    PARXCOM_NTRIP           = 907
    PARXCOM_POSTPROC        = 908
    PARXCOM_BROADCAST       = 909
    PARXCOM_UDPCONFIG       = 910
    PARXCOM_DUMPENABLE      = 911
    PARXCOM_MIGRATOR        = 912
    PARXCOM_TCPKEEPAL       = 913
    PARXCOM_CANGATEWAY      = 914
    PARXCOM_DEFAULTIP       = 915
    PARXCOM_ABDCONFIG       = 916
    PARXCOM_LOGLIST2        = 917
    PARXCOM_CALPROC         = 918
    PARXCOM_CLIENT          = 919
    PARXCOM_FRAMEOUT        =	920

    PARFPGA_IMUSTATUSREG    = 1000
    PARFPGA_HDLCREG         = 1001
    PARFPGA_TIMINGREG       = 1002
    PARFPGA_TIMER           = 1003
    PARFPGA_INTERFACE       = 1004
    PARFPGA_CONTROLREG      = 1005
    PARFPGA_POWERUPTHR      = 1006
    PARFPGA_INTMAT245       = 1007
    PARFPGA_TYPE            = 1008
    PARFPGA_GLOBALCONF      = 1009
    PARFPGA_HDLCPINMODE     = 1010
    PARFPGA_POWER           = 1011
    PARFPGA_ALARMTHR        = 1012
    PARFPGA_PPTCONFIG       = 1013
    PARFPGA_AUTOWAKEUP      = 1014

    PARODO_SCF              = 1100
    PARODO_TIMEOUT          = 1101
    PARODO_MODE             = 1102
    PARODO_LEVERARM         = 1103
    PARODO_VELSTDDEV        = 1104
    PARODO_DIRECTION        = 1105
    PARODO_CONSTRAINT       = 1106
    PARODO_UPDATERATE       = 1107
    PARODO_THR              = 1108
    PARODO_EQEP             = 1109

    PARARINC825_PORT        = 1200
    PARARINC825_BAUD        = 1201
    PARARINC825_ENABLE      = 1202
    PARARINC825_LOGLIST     = 1204
    PARARINC825_BUSRECOVERY = 1205
    PARARINC825_RESETSTATUS = 1206
    PARARINC825_SCALEFACTOR = 1207
    PARARINC825_EVENTMASK   = 1208

    PARNMEA_COM             = 1300
    PARNMEA_ENABLE          = 1301
    PARNMEA_TXMASK          = 1302
    PARNMEA_DECPLACES       = 1303
    PARNMEA_RATE            = 1304
    PARNMEA_UDP             = 1305

    PARARINC429_CONFIG      = 1400
    PARARINC429_LIST        = 1401

    PARIO_HW245             = 1500
    PARIO_HW288             = 1501


class MessageItem(object):
    def __init__(self):
        self.structString = ''

    def to_bytes(self):
        raise NotImplementedError()

    def from_bytes(self, inBytes):
        raise NotImplementedError()

    def size(self):
        try:
            return struct.calcsize(self.structString)
        except:
            raise NotImplementedError()

class XcomProtocolHeader(MessageItem):
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

    def get_time(self):
        return self.timeOfWeek_sec + 1.0e-6*self.timeOfWeek_usec

    def to_bytes(self):
        return bytearray(struct.pack(self.structString, self.sync, self.msgID, self.frameCounter, self.reserved, self.msgLength, self.week, self.timeOfWeek_sec, self.timeOfWeek_usec))

    def from_bytes(self, inBytes):
        self.sync, self.msgID, self.frameCounter, self.reserved, self.msgLength, self.week, self.timeOfWeek_sec, self.timeOfWeek_usec = struct.unpack(self.structString, inBytes[:16])



class XcomProtocolBottom(MessageItem):
    structString = "=HH"

    def __init__(self):
        self.gStatus = 0
        self.crc = 0

    def to_bytes(self):
        return bytearray(struct.pack(self.structString, self.gStatus, self.crc))

    def from_bytes(self, inBytes):
        self.gStatus, self.crc = struct.unpack(self.structString, inBytes)

class XcomProtocolPayload(MessageItem):
    data = collections.OrderedDict()

    def __init__(self):
        super(XcomProtocolPayload, self).__init__()
        self.structString = "="
        self.data = collections.OrderedDict()

    def to_bytes(self):
        values = []
        for value in self.data.values():
            if isinstance(value, list):
                values += value
            else:
                values += [value]
        return bytearray(struct.pack(self.structString, *values))

    def from_bytes(self, inBytes):
        try:
            keyList = self.data.keys()
            valueList = list(struct.unpack(self.structString, inBytes))
            for key in keyList:
                if isinstance(self.data[key], list):
                    curLen = len(self.data[key])
                    value = valueList[:curLen]
                    valueList = valueList[curLen:]
                else:
                    value = valueList[0]
                    valueList = valueList[1:]
                self.data[key] = value
        except Exception as e:
            from sys import stderr
            stderr.write("Could not convert, %s, %s, %s" % ((inBytes), self.get_name(), str(e)))

    def get_name(self):
        classname = self.__class__.__name__
        return classname.split('_')[0]

class XcomProtocolMessage(MessageItem):
    def __init__(self):
        self.header  =  XcomProtocolHeader()
        self.payload =  XcomProtocolPayload()
        self.bottom  =  XcomProtocolBottom()

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
        result = dict()
        result['gpstime'] = self.header.get_time()
        result['gpsweek'] = self.header.week
        result['msg_id'] = self.header.msgID
        result['frame_cnt'] = self.header.frameCounter
        result.update(self.payload.data)
        result['global_status'] = self.bottom.gStatus
        return result


    def __str__(self):
        tmp = str(self.header.frameCounter)+","+str(self.header.timeOfWeek_sec+1e-6*self.header.timeOfWeek_usec)
        for item in self.payload.data:
            if isinstance(self.payload.data[item],list):
                datastr = ','.join(map(str, self.payload.data[item]))
            else:
                datastr = str(self.payload.data[item])
            tmp += ","+datastr
        return tmp

    def to_double_array(self):
        tmp = [self.header.frameCounter, (self.header.timeOfWeek_sec+1e-6*self.header.timeOfWeek_usec)]
        for item in self.payload.data:
            if isinstance(self.payload.data[item],list):
                tmp += self.payload.data[item]
            else:
                tmp += [self.payload.data[item]]
        return tmp

    def size(self):
        return self.header.size()+self.payload.size()+self.bottom.size()


class XcomCommandParameter(IntEnum):
    reboot        = 2
    channel_open  = 1
    channel_close = 0

class XcomParameterAction(IntEnum):
    CHANGING = 0
    REQUESTING = 1

class XcomDefaultCommandPayload(XcomProtocolPayload):
    def __init__(self):
        self.structString = "=HH"
        self.data = collections.OrderedDict([('cmdID',0),('specific',0)])

    def get_name(self):
        return CommandID(self.data['cmdID']).name

class XcomResponsePayload(XcomProtocolPayload):
    def __init__(self, msgLength):
        self.structString = "=HH%ds" % (msgLength-20-4)
        self.data = collections.OrderedDict()
        self.data['responseID'] = 0
        self.data['repsonseLength'] = 0
        self.data['responseText'] = ' '*(msgLength-24)

class XcomDefaultParameterPayload(XcomProtocolPayload):
    def __init__(self):
        self.structString = "=HBB"
        self.data = collections.OrderedDict([('parameterID',0),('reserved',0),('action',XcomParameterAction.REQUESTING)])

    def get_name(self):
        return ParameterID(self.data['parameterID']).name

"""
Commands
"""
class CMD_LOG_Payload(XcomDefaultCommandPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHH"
        self.data['messageID'] = 0
        self.data['trigger'] = 0
        self.data['parameter'] = 0
        self.data['divider'] = 0

class CMD_EKF_Payload(XcomDefaultCommandPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['subcommand'] = 0
        self.data['numberOfParams'] = 0


class CMD_CONF_Payload(XcomDefaultCommandPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['configAction'] = 0

class CMD_EXT_Payload(XcomDefaultCommandPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dHH"
        self.data['time'] = 0
        self.data['timeMode'] = 0
        self.data['cmdParamID'] = 0


class XcomCommandPayload(XcomDefaultCommandPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['mode'] = XcomCommandParameter.channel_open
        self.data['channelNumber'] = 0

"""
PARSYS
"""
class PARSYS_STRING_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "32s"
        self.data['str'] = bytes(' '*32, 'utf-8')

class PARSYS_STRING64_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "64s"
        self.data['str'] = bytes(' '*64, 'utf-8')

class PARSYS_MAINTIMIMG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['maintiming'] = 0
        self.data['password'] = 0

class PARSYS_CALDATE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH32s"
        self.data['password'] = 0
        self.data['reserved2'] = 0
        self.data['str'] = bytes(' '*32, 'utf-8')

class PARSYS_PRESCALER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['prescaler'] = 0
        self.data['password'] = 0

class PARSYS_UPTIME_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['uptime'] = 0

class PARSYS_OPHOURCOUNT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['ophours'] = 0

class PARSYS_BOOTMODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['bootmode'] = 0

class PARSYS_FPGAVER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['major'] = 0
        self.data['minor'] = 0
        self.data['imutype'] = 0

class PARSYS_CONFIGCRC_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['romCRC'] = 0
        self.data['ramCRC'] = 0

"""
PARIMU
"""
class PARIMU_MISALIGN_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f"
        self.data['rpy'] = [0, 0, 0]


class PARIMU_TYPE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['type'] = 0

class PARIMU_LATENCY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "d"
        self.data['latency'] = 0

class PARIMU_CALIB_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3f"
        self.data['sfAcc'] = [0, 0, 0]
        self.data['biasAcc'] = [0, 0, 0]
        self.data['sfOmg'] = [0, 0, 0]
        self.data['biasOmg'] = [0, 0, 0]

class PARIMU_CROSSCOUPLING_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "9d9d"
        self.data['CCAcc'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.data['CCOmg'] = [0, 0, 0, 0, 0, 0, 0, 0, 0]

class PARIMU_REFPOINTOFFSET_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3d"
        self.data['offset'] = [0, 0, 0]

class PARIMU_BANDSTOP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ff"
        self.data['bandwidth'] = 0
        self.data['center'] = 0

class PARIMU_COMPMETHOD_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['method'] = 0

class PARIMU_ACCLEVERARM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "9d"
        self.data['leverarms'] = [0]*9

class PARIMU_STRAPDOWNCONF_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBB"
        self.data['isIncType'] = 0
        self.data['deltaVFrame'] = 0
        self.data['numberOfDeltaTheta'] = 0
        self.data['reserved2'] = 0

"""
PARGNSS
"""
class PARGNSS_PORT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['port'] = 0
        self.data['reserved2'] = 0
        self.data['password'] = 0

class PARGNSS_BAUD_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IHH"
        self.data['baud'] = 0
        self.data['reserved2'] = 0
        self.data['password'] = 0

class PARGNSS_LATENCY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fH"
        self.data['baud'] = 0
        self.data['reserved2'] = 0

class PARGNSS_ANTOFFSET_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f"
        self.data['antennaOffset'] = [0,0,0]
        self.data['stdDev'] = [0,0,0]


class PARGNSS_RTKMODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['rtkMode'] = 0

class PARGNSS_AIDFRAME_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['aidingFrame'] = 0

class PARGNSS_DUALANTMODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['dualAntMode'] = 0

class PARGNSS_LOCKOUTSYSTEM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['lockoutMask'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0

class PARGNSS_RTCMV3CONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHI"
        self.data['port'] = 0
        self.data['enable'] = 0
        self.data['reserved2'] = 0
        self.data['baud'] = 0

class PARGNSS_NAVCONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fBBH"
        self.data['elevationCutoff'] = 0
        self.data['CN0ThreshSVs'] = 0
        self.data['CN0Thresh'] = 0
        self.data['reserved2'] = 0

class PARGNSS_STDDEV_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ffffff"
        self.data['stdDevScalingPos'] = 0
        self.data['minStdDevPos'] = 0
        self.data['stdDevScalingRTK'] = 0
        self.data['minStdDevRTK'] = 0
        self.data['stdDevScalingVel'] = 0
        self.data['minStdDevVel'] = 0

class PARGNSS_VOTER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHIfBBHII"
        self.data['enable'] = 0
        self.data['debugEnable'] = 0
        self.data['timeout'] = 0
        self.data['voterMode'] = 0
        self.data['hysteresis'] = 0
        self.data['PortInt'] = 0
        self.data['PortExt'] = 0
        self.data['selectionMode'] = 0
        self.data['baudInt'] = 0
        self.data['baudExt'] = 0

class PARGNSS_MODEL_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        modelstructstring = "16sIII"
        self.structString += "BBH"
        self.data['rtkCode'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0
        for idx in range(6):
            self.data['modelName_%d' % idx] = b"\0"*16
            self.data['year_%d' % idx] = 0
            self.data['month_%d' % idx] = 0
            self.data['day_%d' % idx] = 0
            self.structString += modelstructstring

class PARGNSS_VERSION_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I16s16s16s16s16s16s16s"
        self.data['type'] = 0
        self.data['model'] = b"\0"*16
        self.data['psn'] = b"\0"*16
        self.data['hwversion'] = b"\0"*16
        self.data['swversion'] = b"\0"*16
        self.data['bootversion'] = b"\0"*16
        self.data['compdate'] = b"\0"*16
        self.data['comptime'] = b"\0"*16

class PARGNSS_RTKSOLTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['positionType'] = 0

class PARGNSS_TERRASTAR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "B7B"
        self.data['PPPPosition'] = 0
        self.data['reserved2'] = [0, 0, 0, 0, 0, 0, 0]

class PARGNSS_CORPORTCFG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IIIIf"
        self.data['rxType'] = 0
        self.data['txType'] = 0
        self.data['baud'] = 0
        self.data['enable'] = 0
        self.data['periodGGA'] = 0

class PARGNSS_REFSTATION_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBB"
        self.data['enableNTRIP'] = 0
        self.data['useFIXPOS'] = 0
        self.data['enableRTCMoutput'] = 0
        self.data['reserved2'] = 0 
        
class PARGNSS_FIXPOS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dddfff"
        self.data['pos'] = [0, 0, 0]
        self.data['posStdDev'] = [0, 0, 0]

class PARGNSS_POSAVE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fffIIIBBBB"
        self.data['maxTime'] = 0
        self.data['maxHorStdDev'] = 0
        self.data['maxVertStdDev'] = 0
        self.data['aveStatus'] = 0
        self.data['aveTime'] = 0
        self.data['state'] = 0
        self.data['reserved2'] = [0, 0, 0]
        
"""
PARMAG
"""
class PARMAG_COM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "B3BI"
        self.data['port'] = 0
        self.data['reserved3'] = [0,0,0]
        self.data['baud'] = 0

class PARMAG_PERIOD_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['period'] = 0

class PARMAG_MISALIGN_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f"
        self.data['rpy'] = [0,0,0]

class PARMAG_CAL_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "9f3fI"
        self.data['C'] = [1,0,0, 0,0,0, 0,0,1]
        self.data['bias'] = [0,0,0]
        self.data['valid'] = 0

class PARMAG_CALSTATE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "i"
        self.data['calstate'] = 0

class PARMAG_CFG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['configbitfield'] = 0
        self.data['paramIdx'] = 0
        self.data['reserved2'] = 0

class PARMAG_ENABLE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['enable'] = 0

class PARMAG_FOM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['FOM'] = 0

"""
PARMADC
"""
class PARMADC_ENABLE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['enable'] = 0

class PARMADC_LEVERARM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f"
        self.data['leverArm'] = [0.0]*3
        self.data['leverArmStdDev'] = [0.0]*3

class PARMADC_LOWPASS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fI"
        self.data['cutoff'] = 0
        self.data['enableFilter'] = 0

"""
PARODO
"""
class PARODO_SCF_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ffI"
        self.data['scfOdo'] = 0
        self.data['scfEst'] = 0
        self.data['selection'] = 0

class PARODO_TIMEOUT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['timeout'] = 0

class PARODO_MODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HHHH"
        self.data['enable'] = 0
        self.data['mode'] = 0
        self.data['deglitcherA'] = 0
        self.data['deglitcherB'] = 0

class PARODO_LEVERARM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f"
        self.data['leverArm'] = [0, 0, 0]

class PARODO_VELSTDDEV_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['stdDev'] = 0

class PARODO_DIRECTION_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f"
        self.data['direction'] = [0, 0, 0]

class PARODO_CONSTRAINTS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHf"
        self.data['enable'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0
        self.data['stdDev'] = 0

class PARODO_RATE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['rate'] = 0

class PARODO_THR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ff"
        self.data['thrAcc'] = 0
        self.data['thrOmg'] = 0

class PARODO_EQEP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['mode'] = 0

"""
PARARINC
"""

class PARARINC825_PORT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['port'] = 0

class PARARINC825_BAUD_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['baud'] = 0

class PARARINC825_ENABLE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['reserved2'] = 0
        self.data['enable'] = 0

class PARARINC825_LOGLIST_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        for idx in range(0,29):
            self.structString += "HHI"
            self.data["divider_%d" % idx] = 0
            self.data["reserved_%d" % idx] = 0
            self.data["docnumber_%d" % idx] = 0

class PARARINC825_BUSRECOVERY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['enable'] = 0
        self.data['reserved2'] = 0

class PARARINC825_RESETSTATUS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['reset'] = 0
        self.data['busStatus'] = 0

class PARARINC825_SCALEFACTOR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dd3ddd3ddddd"
        self.data['ScfAcc'] = 0
        self.data['ScfOmg'] = 0
        self.data['ScfRPY'] = [0, 0, 0]
        self.data['ScfVel'] = 0
        self.data['ScfTime'] = 0
        self.data['ScfPos'] = [0, 0, 0]
        self.data['ScfRPYStdDev'] = 0
        self.data['ScfInsPosStdDev'] = 0
        self.data['ScfVelStdDev'] = 0
        self.data['ScfGnssPosStdDev'] = 0

class PARARINC825_EVENTMASK_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['eventMask'] = 0

"""
PARREC
"""
class PARREC_CONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['channelNumber'] = 0
        self.data['enable'] = 0
        self.data['reserved2'] = 0

class PARREC_START_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "128s"
        self.data['str'] = bytes(' '*128, 'utf-8')

class PARREC_STOP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()

class PARREC_POWER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['enable'] = 0
        
class PARREC_DISKSPACE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "d"
        self.data['freespace'] = 0

class PARREC_AUXILIARY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHIII"
        self.data['port'] = 0
        self.data['enable'] = 0
        self.data['reserved2'] = 0
        self.data['baudrate'] = 0
        self.data['ip'] = 0
        self.data['udpport'] = 0
        
        
class PARREC_SUFFIX_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "128s"
        self.data['suffix'] = bytes(' '*128, 'utf-8')

"""
PAREKF
"""
class PAREKF_ALIGNMODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['alignmode'] = 0

class PAREKF_HDGPOSTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fff"
        self.data['hdgGoodThr'] = 0
        self.data['posMedThr'] = 0
        self.data['posHighThr'] = 0

class PAREKF_ALIGNTIME_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['aligntime'] = 0

class PAREKF_COARSETIME_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['coarsetime'] = 0

class PAREKF_VMP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3fHH"
        self.data['leverArm'] = [0, 0, 0]
        self.data['mask'] = 0
        self.data['cutoff'] = 0

class PAREKF_AIDING_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "II"
        self.data['aidingMode'] = 0
        self.data['aidingMask'] = 0

class PAREKF_DELAY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['delay'] = 0

class PAREKF_OUTLIER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "II"
        self.data['outlierMode'] = 0
        self.data['outlierMask'] = 0

class PAREKF_STARTUP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddf3fffBBHBBBB"
        self.data['initLon'] = 0
        self.data['initLat'] = 0
        self.data['initAlt'] = 0
        self.data['stdDev'] = [0, 0, 0]
        self.data['initHdg'] = 0
        self.data['stdDevHdg'] = 0
        self.data['posMode'] = 0
        self.data['hdgMode'] = 0
        self.data['gnssTimeout'] = 0
        self.data['reserved2'] = 0
        self.data['realign'] = 0
        self.data['inMotion'] = 0
        self.data['autoRestart'] = 0

class PAREKF_STARTUPV2_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddf3fff3f3fBBHBBBB"
        self.data['initLon'] = 0
        self.data['initLat'] = 0
        self.data['initAlt'] = 0
        self.data['stdDev'] = [0, 0, 0]
        self.data['initHdg'] = 0
        self.data['stdDevHdg'] = 0
        self.data['leverArm'] = [0, 0, 0]
        self.data['stdLeverArm'] = [0, 0, 0]
        self.data['posMode'] = 0
        self.data['hdgMode'] = 0
        self.data['gnssTimeout'] = 0
        self.data['altMSL'] = 0
        self.data['realign'] = 0
        self.data['inMotion'] = 0
        self.data['autoRestart'] = 0

class PAREKF_ZUPT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dddfffffHBB"
        self.data['accThr'] = 0
        self.data['omgThr'] = 0
        self.data['velThr'] = 0
        self.data['cutoff'] = 0
        self.data['zuptrate'] = 0
        self.data['minStdDev'] = 0
        self.data['weightingFactor'] = 0
        self.data['timeConstant'] = 0
        self.data['delay'] = 0
        self.data['mask'] = 0
        self.data['autoZupt'] = 0

class PAREKF_DEFPOS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddf"
        self.data['lon'] = 0
        self.data['lat'] = 0
        self.data['alt'] = 0

class PAREKF_DEFHDG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['hdg'] = 0

class PAREKF_SMOOTH_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['smooth'] = 0

class PAREKF_POWERDOWN_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['savestate'] = 0

class PAREKF_EARTHRAD_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ff"
        self.data['M'] = 0
        self.data['N'] = 0

class PAREKF_STOREDPOS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dddddd"
        self.data['lon'] = 0
        self.data['lat'] = 0
        self.data['alt'] = 0

        self.data['stdDevLon'] = 0
        self.data['stdDevLat'] = 0
        self.data['stdDevAlt'] = 0

class PAREKF_STOREDATT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f"
        self.data['rpy'] = [0,0,0]
        self.data['stdDev'] = [0,0,0]

class PAREKF_ALIGNZUPTSTDDEV_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "d"
        self.data['zuptStdDev'] = 0

class PAREKF_POSAIDSTDDEVTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "d"
        self.data['thr'] = 0

class PAREKF_SCHULERMODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['enable'] = 0

class PAREKF_ODOMETER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fffffffffffHH"
        self.data['sfError'] = 0
        self.data['sfStdDev'] = 0
        self.data['rwScalefactor'] = 0
        self.data['misalignmentY'] = 0
        self.data['misalignmentZ'] = 0
        self.data['stdMisalignmentY'] = 0
        self.data['stdMisalignmentZ'] = 0
        self.data['rwMisalignmentY'] = 0
        self.data['rwMisalignmentZ'] = 0
        self.data['minVel'] = 0
        self.data['maxVel'] = 0
        self.data['useAvgInno'] = 0
        self.data['enableCoarseCal'] = 0

class PAREKF_ODOBOGIE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fI"
        self.data['distance'] = 0
        self.data['enable'] = 0

class PAREKF_GNSSLEVERARMEST_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['primary'] = 0
        self.data['secondary'] = 0

class PAREKF_GNSSAIDINGRATE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HHHHHH"
        self.data['psrpos'] = 0
        self.data['psrvel'] = 0
        self.data['rtk'] = 0
        self.data['rtktimeout'] = 0
        self.data['hdg'] = 0
        self.data['duringzupt'] = 0

class PAREKF_KINALIGNTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['thr'] = 0

class PAREKF_PDOPTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['thr'] = 0

class PAREKF_DUALANTAID_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fffI"
        self.data['thrHdg'] = 0
        self.data['thrPitch'] = 0
        self.data['thrINSHdg'] = 0
        self.data['mode'] = 0

class PAREKF_MAGATTAID_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IfffBBH3f"
        self.data['samplePeriods'] = 0
        self.data['thrHdg'] = 0
        self.data['latency'] = 0
        self.data['thrINSHdg'] = 0
        self.data['aidingMode'] = 0
        self.data['updateMode'] = 0
        self.data['aidingInterval'] = 0
        self.data['magFieldStdDev'] = [0]*3

class PAREKF_MADCAID_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ffHHffffff"
        self.data['altStdDev'] = 0.0
        self.data['latency'] = 0.0
        self.data['aidInterval'] = 0
        self.data['reserved2'] = 0
        self.data['sfError'] = 0.0
        self.data['sfStdDev'] = 0.0
        self.data['rwSf'] = 0.0
        self.data['bias'] = 0.0
        self.data['biasStdDev'] = 0.0
        self.data['rwBias'] = 0.0

class PAREKF_ALIGNMENT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IHHdBBf3fH3I"
        self.data['method'] = 0
        self.data['levellingDuration'] = 0
        self.data['stationaryDuration'] = 0
        self.data['alignZuptStdDev'] = 0.0
        self.data['enableGyroAvg'] = 0
        self.data['enableTrackAlign'] = 0
        self.data['trackAlignThresh'] = 0.0
        self.data['trackAlignDirection'] = [0.0]*3
        self.data['reserved2'] = 0
        self.data['reserved3'] = [0]*3

class PAREKF_GRAVITYAID_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "Ifffff"
        self.data['enable'] = 0
        self.data['omgThresh'] = 0.0
        self.data['accThresh'] = 0.0
        self.data['stdDev'] = 0.0
        self.data['gnssTimeout'] = 0.0
        self.data['aidingInterval'] = 0.0

class PAREKF_FEEDBACK_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['feedbackMask'] = 0

class PAREKF_ZARU_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "B3B"
        self.data['enable'] = 0
        self.data['reserved2'] = [0]*3

class PAREKF_IMUCONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        tmp = "3d3d3d3d3ddd3d"
        self.structString += tmp*2
        self.data['accPSD'] = [0]*3
        self.data['accOffStdDev'] = [0]*3
        self.data['accOffRW'] = [0]*3
        self.data['accSfStdDev'] = [0]*3
        self.data['accSfRW'] = [0]*3
        self.data['accMaStdDev'] = 0
        self.data['accMaRW'] = 0
        self.data['accQuantization'] = [0]*3

        self.data['gyroPSD'] = [0]*3
        self.data['gyroOffStdDev'] = [0]*3
        self.data['gyroOffRW'] = [0]*3
        self.data['gyroSfStdDev'] = [0]*3
        self.data['gyroSfRW'] = [0]*3
        self.data['gyroMaStdDev'] = 0
        self.data['gyroMaRW'] = 0
        self.data['gyroQuantization'] = [0]*3

class PAREKF_ZUPTCALIB_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['zuptCalibTime'] = 0
        self.data['reserved2'] = 0

class PAREKF_STATEFREEZE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['freezeMask'] = 0
        
class PAREKF_RECOVERY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['recoveryMask'] = 0

"""
PARDAT
"""
class PARDAT_POS_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['posMode'] = 0
        self.data['altMode'] = 0

class PARDAT_VEL_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['velMode'] = 0

class PARDAT_IMU_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['imuMode'] = 0

class PARDAT_SYSSTAT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['statMode'] = 0

class PARDAT_STATFPGA_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IIHHBBH"
        self.data['powerStatLower'] = 0
        self.data['powerStatUpper'] = 0
        self.data['fpgaStatus'] = 0
        self.data['supervisorStatus'] = 0
        self.data['imuStatus'] = 0
        self.data['tempStatus'] = 0
        self.data['reserved2'] = 0

"""
PARXCOM
"""
class PARXCOM_SERIALPORT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHI"
        self.data['port'] = 1 # port = 0 results in error 5: port is invalid
        self.data['switch'] = 0
        self.data['reserved2'] = 0
        self.data['baudRate'] = 0

class PARXCOM_NETCONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBBIIII"
        self.data['mode'] = 0
        self.data['protocol'] = 0
        self.data['interface'] = 0
        self.data['speed'] = 0
        self.data['port'] = 0
        self.data['ip'] = 0
        self.data['subnetmask'] = 0
        self.data['gateway'] = 0

class PARXCOM_LOGLIST_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        for idx in range(0,16):
            self.structString += "HH"
            self.data["divider_%d" % idx] = 0
            self.data["msgid_%d" % idx] = 0

class PARXCOM_AUTOSTART_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HHHH"
        self.data['channelNumber'] = 0
        self.data['autoStart'] = 0
        self.data['port'] = 0
        self.data['reserved2'] = 0

class PARXCOM_NTRIP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "128s128s128s128sBBHI"
        self.data['stream'] = b"\0"*128
        self.data['user'] = b"\0"*128
        self.data['password'] = b"\0"*128
        self.data['server'] = b"\0"*128
        self.data['port'] = 0
        self.data['enable'] = 0
        self.data['reserved2'] = 0
        self.data['baud'] = 0

class PARXCOM_POSTPROC_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['enable'] = 0
        self.data['channel'] = 0
        self.data['reserved2'] = 0

class PARXCOM_BROADCAST_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IBBH"
        self.data['port'] = 0
        self.data['hidden_mode'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0

class PARXCOM_UDPCONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IIBBBB"
        self.data['ip'] = 0
        self.data['port'] = 0
        self.data['enable'] = 0
        self.data['channel'] = 0
        self.data['enableABD'] = 0
        self.data['reserved2'] = 0

class PARXCOM_DUMPENABLE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['enable'] = 0

class PARXCOM_MIGRATOR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['enable'] = 0

class PARXCOM_FRAMEOUT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['outputframe'] = 0

class PARXCOM_TCPKEEPAL_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HHHH"
        self.data['timeout'] = 0
        self.data['interval'] = 0
        self.data['probes'] = 0
        self.data['enable'] = 0


class PARXCOM_CANGATEWAY_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IIIBBBB"
        self.data['srcPort'] = 0
        self.data['destPort'] = 0
        self.data['destAddr'] = 0
        self.data['arinc825Loopback'] = 0
        self.data['debugEnable'] = 0
        self.data['enable'] = 0
        self.data['interface'] = 0

class PARXCOM_DEFAULTIP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['defaultAddress'] = 0

class PARXCOM_ABDCONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "II"
        self.data['destinationPort'] = 0
        self.data['sourcePort'] = 0

class PARXCOM_LOGLIST2_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        for idx in range(0,16):
            self.structString += "HHBBH"
            self.data["divider_%d" % idx] = 0
            self.data["msgid_%d" % idx] = 0
            self.data["running %d" % idx] = 0
            self.data["reserved2 %d" % idx] = 0
            self.data["reserved3 %d" % idx] = 0

class PARXCOM_CALPROC_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH256s"
        self.data['enable'] = 0
        self.data['channel'] = 0
        self.data['divider'] = 0
        self.data['pathName'] = b"\0"*256

class PARXCOM_CLIENT_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        for idx in range(0,8):
            self.structString += "IIBBH"
            self.data["ipAddress %d" % idx] = 0
            self.data["port %d" % idx] = 0
            self.data["enable %d" % idx] = 0
            self.data["channel %d" % idx] = 0
            self.data["connectionRetr %d" % idx] = 0
            for idx2 in range(0, 8):
                self.structString += "BBH"
                self.data["messageId %d%d" % (idx, idx2)] = 0
                self.data["trigger %d%d" % (idx, idx2)] = 0
                self.data["dividerLogs %d%d" % (idx, idx2)] = 0
        #self.structString += "B3B"
        #self.data['useUDPInterface'] = 0
        #self.data['reserved2'] = [0]*3
        print(self.data)

"""
PARFPGA
"""
class PARFPGA_TIMER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "14HHH"
        self.data['timer'] = [0]*14
        self.data['reserved2'] = 0
        self.data['password'] = 0

class PARFPGA_TIMINGREG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BB2HH"
        self.data['timing_reg'] = 0
        self.data['reserved2'] = 0
        self.data['userTimer'] = [0]*2
        self.data['password'] = 0

class PARFPGA_IMUSTATUSREG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['register'] = 0
        self.data['reserved2'] = 0
        self.data['password'] = 0

class PARFPGA_HDLCREG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBBHH"
        self.data['mode'] = 0
        self.data['clock'] = 0
        self.data['invertData'] = 0
        self.data['invertClock'] = 0
        self.data['reserved2'] = 0
        self.data['password'] = 0

class PARFPGA_INTERFACE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "22IHH"
        self.data['matrix'] = [0]*22
        self.data['reserved2'] = 0
        self.data['password'] = 0

class PARFPGA_CONTROLREG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HH"
        self.data['controlReg'] = 0
        self.data['reserved2'] = 0

class PARFPGA_POWERUPTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ff"
        self.data['powerupThr'] = 0.0
        self.data['reserved2'] = 0.0

class PARFPGA_INTMAT245_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "32B"
        self.data['interfaceMatrix'] = [0]*32

class PARFPGA_TYPE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['type'] = 0

class PARFPGA_GLOBALCONF_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['configuration'] = 0

class PARFPGA_HDLCPINMODE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['pinMode'] = 0

class PARFPGA_POWER_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['powerSwitch'] = 0

class PARFPGA_ALARMTHR_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['alarmThr'] = 0

class PARFPGA_PPTCONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['pptValue'] = 0
        self.data['pptPulseWidth'] = 0
        self.data['reserved2'] = 0

class PARFPGA_AUTOWAKEUP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBB"
        self.data['enableAutoWakeup'] = 0
        self.data['interval'] = 0
        self.data['retries'] = 0
        self.data['reserved2'] = 0

"""
PARNMEA
"""
class PARNMEA_COM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHI"
        self.data['port'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0
        self.data['baud'] = 0

class PARNMEA_ENABLE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBB"
        self.data['reserved2'] = 0
        self.data['qualityMode'] = 0
        self.data['selectionSwitch'] = 0
        self.data['reserved4'] = 0

class PARNMEA_TXMASK_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['txMask'] = 0

class PARNMEA_DECPLACES_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['digitsPos'] = 0
        self.data['digitsHdg'] = 0
        self.data['reserved2'] = 0

class PARNMEA_RATE_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['divisor'] = 0

class PARNMEA_UDP_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IIBBH"
        self.data['serverAddress'] = 0
        self.data['port'] = 1
        self.data['enable'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0

"""
PARARINC429
"""

class PARARINC429_CONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHBBH"
        self.data['port'] = 0
        self.data['enable'] = 0
        self.data['reserved2'] = 0
        self.data['reserved3'] = 0
        self.data['highSpeed'] = 0
        self.data['reserved4'] = 0

class PARARINC429_LIST_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        for idx in range(0,32):
            self.structString += "BBBBddBII"
            self.data["channel %d" % idx] = 0
            self.data["label %d" % idx] = 0
            self.data["datIdx %d" % idx] = 0
            self.data["enable %d" % idx] = 0
            self.data["range %d" % idx] = 0
            self.data["scf %d" % idx] = 0
            self.data["width %d" % idx] = 0
            self.data["period %d" % idx] = 0
            self.data["timer %d" % idx] = 0

"""
IO
"""

class PARIO_HW245_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['configIO'] = 0

class PARIO_HW288_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['toDef'] = 0

"""
Messages
"""

class POSTPROC_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f12f12f4d3d3dI2IfiIII"
        self.data['acc'] = [0, 0, 0]
        self.data['omg'] = [0, 0, 0]
        self.data['delta_theta'] = [0]*12
        self.data['delta_v'] = [0]*12
        self.data['q_nb'] = [0, 0, 0, 0]
        self.data['pos'] = [0, 0, 0]
        self.data['vel'] = [0, 0, 0]
        self.data['sysStat'] = 0
        self.data['ekfStat'] = [0, 0]
        self.data['odoSpeed'] = 0
        self.data['odoTicks'] = 0
        self.data['odoInterval'] = 0
        self.data['odoTrigEvent'] = 0
        self.data['odoNextEvent'] = 0

class INSSOL_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3fddfhH"
        self.data['acc'] = [0, 0, 0]
        self.data['omg'] = [0, 0, 0]
        self.data['rpy'] = [0, 0, 0]
        self.data['vel'] = [0, 0, 0]
        self.data['lon'] = 0
        self.data['lat'] = 0
        self.data['alt'] = 0
        self.data['undulation'] = 0
        self.data['DatSel'] = 0

class IMU_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f"
        self.data['acc'] = [0, 0, 0]
        self.data['omg'] = [0, 0, 0]

class INSROTTEST_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3d"
        self.data['accNED'] = [0, 0, 0]

class IMUCAL_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3d3dd4d3d3d16fI2I6I"
        self.data['accLSB'] = [0, 0, 0]
        self.data['omgLSB'] = [0, 0, 0]
        self.data['accCal'] = [0, 0, 0]
        self.data['omgCal'] = [0, 0, 0]
        self.data['avgTime'] = 0
        self.data['q_nb']   = [1, 0, 0, 0]
        self.data['pos']    = [0, 0, 0]
        self.data['vel']    = [0, 0, 0]
        self.data['temp']   = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.data['sysstat']=  0
        self.data['ekfstat']= [0, 0]
        self.data['imustat']= [0, 0, 0, 0, 0, 0]

class STATFPGA_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HBBIIHHBBH"
        self.data['usParID'] = 0
        self.data['uReserved'] = 0
        self.data['ucAction'] = 0
        self.data['uiPowerStatLower'] = 0
        self.data['uiPowerStatUpper'] = 0
        self.data['usFpgaStatus'] = 0
        self.data['usSupervisorStatus'] = 0
        self.data['ucImuStatus'] = 0
        self.data['ucTempStatus'] = 0
        self.data['usRes'] = 0

class SYSSTAT_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "II"
        self.data['statMode']= 0
        self.data['sysStat'] = 0

    def from_bytes(self, inBytes):
        self.data['statMode'] = struct.unpack("I", inBytes[:4])[0]
        print(hex(self.data['statMode']))
        if(self.data['statMode'] & (1 << 0)):
            self.structString += "I"
            self.data['imuStat'] = 0
        if(self.data['statMode'] & (1 << 1)):
            self.structString += "I"
            self.data['gnssStat'] = 0
        if(self.data['statMode'] & (1 << 2)):
            self.structString += "I"
            self.data['magStat'] = 0
        if(self.data['statMode'] & (1 << 3)):
            self.structString += "I"
            self.data['madcStat'] = 0
        if(self.data['statMode'] & (1 << 4)):
            self.structString += "2I"
            self.data['ekfStat'] = [0, 0]
        if(self.data['statMode'] & (1 << 5)):
            self.structString += "I"
            self.data['ekfGeneralStat'] = 0
        if(self.data['statMode'] & (1 << 6)):
            self.structString += "4I"
            self.data['addStat'] = [0, 0, 0 ,0]
        if(self.data['statMode'] & (1 << 7)):
            self.structString += "I"
            self.data['serviceStat'] = [0]
        if(self.data['statMode'] & (1 << 8)):
            self.structString += "f"
            self.data['remainingAlignTime'] = [0]
        super().from_bytes(inBytes)

class INSRPY_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f"
        self.data['rpy']    = [0, 0, 0]

class INSDCM_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "9f"
        self.data['DCM']    = [0, 0, 0, 0, 0, 0, 0, 0, 0]

class INSQUAT_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "4f"
        self.data['quat']    = [0, 0, 0, 0]

class INSPOSLLH_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddf"
        self.data['lon']    = 0
        self.data['lat']    = 0
        self.data['alt']    = 0

class INSPOSUTM_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "iddf"
        self.data['zone']       = 0
        self.data['easting']    = 0
        self.data['northing']   = 0
        self.data['height']     = 0

class INSPOSECEF_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3d"
        self.data['pos'] = [0, 0, 0]

class INSVEL_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f"
        self.data['vel'] = [0, 0, 0]

class MAGDATA_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3fffffI"
        self.data['field']           = [0, 0, 0]
        self.data['magHdg']          =  0
        self.data['magBank']         =  0
        self.data['magElevation']    =  0
        self.data['magDeviation']    =  0
        self.data['status']          =  0

class AIRDATA_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fffffffffffI"
        self.data['TAS']        = 0
        self.data['IAS']        = 0
        self.data['baroAlt']    = 0
        self.data['baroAltRate'] = 0
        self.data['Pd']         = 0
        self.data['Ps']         = 0
        self.data['OAT']        = 0
        self.data['estBias']        = 0
        self.data['estScaleFactor']        = 0
        self.data['estBiasStdDev']        = 0
        self.data['estScaleFactorStdDev']        = 0
        self.data['status']     = 0

class EKFSTDDEV_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3f3f3f3ff"
        self.data['pos']        = [0, 0, 0]
        self.data['vel']        = [0, 0, 0]
        self.data['tilt']       = [0, 0, 0]
        self.data['biasAcc']    = [0, 0, 0]
        self.data['biasOmg']    = [0, 0, 0]
        self.data['scfAcc']     = [0, 0, 0]
        self.data['scfOmg']     = [0, 0, 0]
        self.data['scfOdo']     =  0

class EKFSTDDEV2_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3f3f9f9ff2f"
        self.data['pos']        = [0, 0, 0]
        self.data['vel']        = [0, 0, 0]
        self.data['rpy']        = [0, 0, 0]
        self.data['biasAcc']    = [0, 0, 0]
        self.data['biasOmg']    = [0, 0, 0]
        self.data['fMaAcc']     = [0, 0, 0]
        self.data['fMaOmg']     = [0, 0, 0]
        self.data['scfOdo']     = 0
        self.data['fMaOdo']     = [0]*2

class EKFERROR2_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f9f9ff2f"
        self.data['biasAcc']    = [0, 0, 0]
        self.data['biasOmg']    = [0, 0, 0]
        self.data['fMaAcc']     = [0]*9
        self.data['fMaOmg']     = [0]*9
        self.data['scfOdo']     = 0
        self.data['maOdo']      = [0, 0]

class EKFERROR_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3ff2f"
        self.data['biasAcc']    = [0, 0, 0]
        self.data['biasOmg']    = [0, 0, 0]
        self.data['scfAcc']     = [0, 0, 0]
        self.data['scfOmg']     = [0, 0, 0]
        self.data['scfOdo']     =  0
        self.data['maOdo']      = [0, 0]

class EKFTIGHTLY_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBBBBBBBIIIIIIIIIIII"
        self.data['ucSatsAvailablePSR'] = 0
        self.data['ucSatsUsedPSR'] = 0
        self.data['ucSatsAvailableRR'] = 0
        self.data['ucSatsUsedRR'] = 0

        self.data['ucSatsAvailableTDCP'] = 0
        self.data['ucSatsUsedTDCP'] = 0
        self.data['ucRefSatTDCP'] = 0
        self.data['usReserved'] = 0

        self.data['uiUsedSatsPSR_GPS'] = 0
        self.data['uiOutlierSatsPSR_GPS'] = 0

        self.data['uiUsedSatsPSR_GLONASS'] = 0
        self.data['uiOutlierSatsPSR_GLONASS'] = 0

        self.data['uiUsedSatsRR_GPS'] = 0
        self.data['uiOutlierSatsRR_GPS'] = 0

        self.data['uiUsedSatsRR_GLONASS'] = 0
        self.data['uiOutlierSatsRR_GLONASS'] = 0

        self.data['uiUsedSatsTDCP_GPS'] = 0
        self.data['uiOutlierSatsTDCP_GPS'] = 0

        self.data['uiUsedSatsTDCP_GLONASS'] = 0
        self.data['uiOutlierSatsTDCP_GLONASS'] = 0

class EKFPOSCOVAR_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "9f"
        self.data['fPosCovar'] = [0]*9

class POWER_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "32f"
        self.data['power']    = [0]*32

class TEMP_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "16f"
        self.data['temperatures']    = [0]*16

class HEAVE_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dddddddd2dII"
        self.data['StatFiltPos'] = 0
        self.data['AppliedFreqHz'] = 0
        self.data['AppliedAmplMeter'] = 0
        self.data['AppliedSigWaveHeightMeter'] = 0
        self.data['PZpos'] = 0
        self.data['ZDpos'] = 0
        self.data['ZDvel'] = 0
        self.data['AccZnavDown'] = 0

        self.data['HeavePosVelDown'] = [0] * 2
        self.data['HeaveAlgoStatus1'] = 0
        self.data['HeaveAlgoStatus2'] = 0

class CANSTAT_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "IBBBB"
        self.data['uiErrorMask'] = 0
        self.data['ucControllerStatus'] = 0
        self.data['ucTransceiverStatus'] = 0
        self.data['ucProtocolStatus'] = 0
        self.data['ucProtocolLocation'] = 0

class ARINC429STAT_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['uiStatus']    = 0

class TIME_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddddddd"
        self.data['sysTime']    = 0
        self.data['ImuInterval']    = 0
        self.data['TimeSincePPS']    = 0
        self.data['PPS_IMUtime']    = 0
        self.data['PPS_GNSStime']    = 0
        self.data['GNSSbias']    = 0
        self.data['GNSSbiasSmoothed']    = 0

class GNSSSOL_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddff3f3f3fHHfBBHffI"
        self.data['lon']            = 0
        self.data['lat']            = 0
        self.data['alt']            = 0
        self.data['undulation']     = 0
        self.data['velNED']         = [0]*3
        self.data['stdDevPos']      = [0]*3
        self.data['stdDevVel']      = [0]*3
        self.data['solStatus']      = 0
        self.data['posType']        = 0
        self.data['pdop']           = 0
        self.data['satsUsed']       = 0
        self.data['solTracked']     = 0
        self.data['res']            = 0
        self.data['diffAge']        = 0
        self.data['solAge']         = 0
        self.data['gnssStatus']     = 0

class GNSSTIME_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddIBBBBII"
        self.data['utcOffset']      = 0
        self.data['offset']         = 0
        self.data['year']           = 0
        self.data['month']          = 0
        self.data['day']            = 0
        self.data['hour']           = 0
        self.data['minute']         = 0
        self.data['millisec']       = 0
        self.data['status']         = 0

class GNSSSOLCUST_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ddff3f3f3f3f3fH2fBBBHffI"
        self.data['dLon']           = 0
        self.data['dLat']           = 0
        self.data['fAlt']           = 0
        self.data['fUndulation']    = 0
        self.data['fStdDev_Pos']    = [0]*3
        self.data['fVned']          = [0]*3
        self.data['fStdDev_Vel']    = [0]*3
        self.data['fDisplacement']  = [0]*3
        self.data['fStdDev_Displacement'] = [0]*3
        self.data['usSolStatus']    = 0
        self.data['fDOP']           = [0]*2
        self.data['ucSatsPos']      = 0
        self.data['ucSatsVel']      = 0
        self.data['ucSatsDisplacement'] = 0
        self.data['usReserved']     = 0
        self.data['fDiffAge']       = 0
        self.data['fSolAge']        = 0
        self.data['uiGnssStatus']   = 0

class GNSSHDG_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ffffHHHBBI"
        self.data['hdg']        = 0
        self.data['stdDevHdg']  = 0
        self.data['pitch']      = 0
        self.data['stdDevPitch']= 0
        self.data['solStat']    = 0
        self.data['solType']    = 0
        self.data['res']        = 0
        self.data['satsUsed']   = 0
        self.data['satsTracked']= 0
        self.data['gnssStatus'] = 0

class GNSSLEVERARM_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3f"
        self.data['primary']        = [0]*3
        self.data['stdDevPrimary']  = [0]*3
        self.data['relative']       = [0]*3
        self.data['stdDevRelative'] = [0]*3

class GNSSVOTER_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBHffffI"
        self.data['ucSatsUsed_INT']        = [0]
        self.data['ucSatsUsed_EXT']        = [0]
        self.data['usReserved']            = [0]
        self.data['fStdDevHDG_INT']        = [0]
        self.data['fStdDevHDG_EXT']        = [0]
        self.data['fStdDevPOS_INT']        = [0]
        self.data['fStdDevPOS_EXT']        = [0]
        self.data['uiStatus']              = [0]

class GNSSHWMON_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        for idx in range(16):
            self.data['val %d' % idx] = 0
            self.data['status %d' % idx] = 0
            self.structString += "fI"

class GNSSSATINFO_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I3d3dfffff"
        self.data['svID']                 = 0
        self.data['dPositionECEF']        = [0]*3
        self.data['dVelocityECEF']        = [0]*3
        self.data['fClockError']          = 0
        self.data['fIonoError']           = 0
        self.data['fTropoError']          = 0
        self.data['fElevation']           = 0
        self.data['fAzimuth']             = 0

class GNSSALIGNBSL_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dddfffHHBBBB"
        self.data['east']               = 0
        self.data['north']              = 0
        self.data['up']                 = 0
        self.data['eastStddev']         = 0
        self.data['northStddev']        = 0
        self.data['upStddev']           = 0
        self.data['solStatus']          = 0
        self.data['posVelType']         = 0
        self.data['satsTracked']        = 0
        self.data['satsUsedInSolution'] = 0
        self.data['extSolStat']         = 0
        self.data['reserved']           = 0


class WHEELDATA_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fi"
        self.data['odoSpeed']   = 0
        self.data['ticks']      = 0

class WHEELDATADBG_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fiIII"
        self.data['odoSpeed']       = 0
        self.data['ticks']          = 0
        self.data['interval']       = 0
        self.data['trigEvent']      = 0
        self.data['trigNextEvent']  = 0

class EVENTTIME_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "dd"
        self.data['dGpsTime_EVENT_0'] = 0
        self.data['dGpsTime_EVENT_1'] = 0

class OMGINT_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3ff"
        self.data['omgINT'] = [0]*3
        self.data['omgINTtime'] = 0

class ADC24STATUS_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "4I4I"
        self.data['uiRRidx']   = [0]*4
        self.data['uiRRvalue'] = [0]*4

class ADC24DATA_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3IHhB3B"
        self.data['acc']            = [0]*3
        self.data['frameCounter']   = [0]
        self.data['temperature']    = [0]
        self.data['errorStatus']    = [0]
        self.data['intervalCounter'] = [0]*3


ParameterPayloadDictionary = {
    ParameterID.PARSYS_PRJNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_PARTNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_SERIALNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_MFG:PARSYS_STRING_Payload,
    ParameterID.PARSYS_CALDATE:PARSYS_CALDATE_Payload,
    ParameterID.PARSYS_FWVERSION:PARSYS_STRING_Payload,
    ParameterID.PARSYS_NAVLIB:PARSYS_STRING_Payload,
    ParameterID.PARSYS_EKFLIB:PARSYS_STRING_Payload,
    ParameterID.PARSYS_EKFPARSET:PARSYS_STRING_Payload,
    ParameterID.PARSYS_NAVNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_NAVPARSET:PARSYS_STRING_Payload,
    ParameterID.PARSYS_MAINTIMING:PARSYS_MAINTIMIMG_Payload,
    ParameterID.PARSYS_PRESCALER:PARSYS_PRESCALER_Payload,
    ParameterID.PARSYS_UPTIME:PARSYS_UPTIME_Payload,
    ParameterID.PARSYS_OPHOURCOUNT:PARSYS_OPHOURCOUNT_Payload,
    ParameterID.PARSYS_BOOTMODE:PARSYS_BOOTMODE_Payload,
    ParameterID.PARSYS_FPGAVER:PARSYS_FPGAVER_Payload,
    ParameterID.PARSYS_CONFIGCRC:PARSYS_CONFIGCRC_Payload,
    ParameterID.PARSYS_OSVERSION:PARSYS_STRING64_Payload,
    ParameterID.PARSYS_SYSNAME:PARSYS_STRING64_Payload,

    ParameterID.PARIMU_MISALIGN:PARIMU_MISALIGN_Payload,
    ParameterID.PARIMU_TYPE:PARIMU_TYPE_Payload,
    ParameterID.PARIMU_LATENCY:PARIMU_LATENCY_Payload,
    ParameterID.PARIMU_CALIB:PARIMU_CALIB_Payload,
    ParameterID.PARIMU_CROSSCOUPLING:PARIMU_CROSSCOUPLING_Payload,
    ParameterID.PARIMU_REFPOINTOFFSET:PARIMU_REFPOINTOFFSET_Payload,
    ParameterID.PARIMU_BANDSTOP:PARIMU_BANDSTOP_Payload,
    ParameterID.PARIMU_COMPMETHOD:PARIMU_COMPMETHOD_Payload,
    ParameterID.PARIMU_ACCLEVERARM:PARIMU_ACCLEVERARM_Payload,
    ParameterID.PARIMU_STRAPDOWNCONF:PARIMU_STRAPDOWNCONF_Payload,

    ParameterID.PARGNSS_PORT:PARGNSS_PORT_Payload,
    ParameterID.PARGNSS_BAUD:PARGNSS_BAUD_Payload,
    ParameterID.PARGNSS_LATENCY:PARGNSS_LATENCY_Payload,
    ParameterID.PARGNSS_ANTOFFSET:PARGNSS_ANTOFFSET_Payload,
    ParameterID.PARGNSS_RTKMODE:PARGNSS_RTKMODE_Payload,
    ParameterID.PARGNSS_AIDFRAME:PARGNSS_AIDFRAME_Payload,
    ParameterID.PARGNSS_DUALANTMODE:PARGNSS_DUALANTMODE_Payload,
    ParameterID.PARGNSS_LOCKOUTSYSTEM:PARGNSS_LOCKOUTSYSTEM_Payload,
    ParameterID.PARGNSS_RTCMV3CONFIG:PARGNSS_RTCMV3CONFIG_Payload,
    ParameterID.PARGNSS_NAVCONFIG:PARGNSS_NAVCONFIG_Payload,
    ParameterID.PARGNSS_STDDEV:PARGNSS_STDDEV_Payload,
    ParameterID.PARGNSS_VOTER:PARGNSS_VOTER_Payload,
    ParameterID.PARGNSS_MODEL:PARGNSS_MODEL_Payload,
    ParameterID.PARGNSS_VERSION:PARGNSS_VERSION_Payload,
    ParameterID.PARGNSS_RTKSOLTHR:PARGNSS_RTKSOLTHR_Payload,
    ParameterID.PARGNSS_TERRASTAR:PARGNSS_TERRASTAR_Payload,
    ParameterID.PARGNSS_REFSTATION:PARGNSS_REFSTATION_Payload,
    ParameterID.PARGNSS_FIXPOS:PARGNSS_FIXPOS_Payload,
    ParameterID.PARGNSS_POSAVE:PARGNSS_POSAVE_Payload,
    ParameterID.PARGNSS_CORPORTCFG:PARGNSS_CORPORTCFG_Payload,
    
    ParameterID.PARMAG_COM:PARMAG_COM_Payload,
    ParameterID.PARMAG_PERIOD:PARMAG_PERIOD_Payload,
    ParameterID.PARMAG_MISALIGN:PARMAG_MISALIGN_Payload,
    ParameterID.PARMAG_CAL:PARMAG_CAL_Payload,
    ParameterID.PARMAG_CALSTATE:PARMAG_CALSTATE_Payload,
    ParameterID.PARMAG_FOM:PARMAG_FOM_Payload,
    ParameterID.PARMAG_CFG:PARMAG_CFG_Payload,
    ParameterID.PARMAG_ENABLE:PARMAG_ENABLE_Payload,

    ParameterID.PARMADC_ENABLE:PARMADC_ENABLE_Payload,
    ParameterID.PARMADC_LEVERARM:PARMADC_LEVERARM_Payload,
    ParameterID.PARMADC_LOWPASS:PARMADC_LOWPASS_Payload,

    ParameterID.PARREC_CONFIG:PARREC_CONFIG_Payload,
    ParameterID.PARREC_START:PARREC_START_Payload,
    ParameterID.PARREC_STOP:PARREC_STOP_Payload,
    ParameterID.PARREC_POWER:PARREC_POWER_Payload,
    ParameterID.PARREC_DISKSPACE:PARREC_DISKSPACE_Payload,
    ParameterID.PARREC_AUXILIARY:PARREC_AUXILIARY_Payload,
    
    ParameterID.PAREKF_ALIGNMODE:PAREKF_ALIGNMODE_Payload,
    ParameterID.PAREKF_ALIGNTIME:PAREKF_ALIGNTIME_Payload,
    ParameterID.PAREKF_COARSETIME:PAREKF_COARSETIME_Payload,
    ParameterID.PAREKF_VMP:PAREKF_VMP_Payload,
    ParameterID.PAREKF_AIDING:PAREKF_AIDING_Payload,
    ParameterID.PAREKF_DELAY:PAREKF_DELAY_Payload,
    ParameterID.PAREKF_STARTUP:PAREKF_STARTUP_Payload,
    ParameterID.PAREKF_HDGPOSTHR:PAREKF_HDGPOSTHR_Payload,
    ParameterID.PAREKF_SMOOTH:PAREKF_SMOOTH_Payload,
    ParameterID.PAREKF_ZUPT:PAREKF_ZUPT_Payload,
    ParameterID.PAREKF_DEFPOS:PAREKF_DEFPOS_Payload,
    ParameterID.PAREKF_DEFHDG:PAREKF_DEFHDG_Payload,
    ParameterID.PAREKF_OUTLIER:PAREKF_OUTLIER_Payload,
    ParameterID.PAREKF_POWERDOWN:PAREKF_POWERDOWN_Payload,
    ParameterID.PAREKF_EARTHRAD:PAREKF_EARTHRAD_Payload,
    ParameterID.PAREKF_STOREDPOS:PAREKF_STOREDPOS_Payload,
    ParameterID.PAREKF_ALIGNZUPTSTDDEV:PAREKF_ALIGNZUPTSTDDEV_Payload,
    ParameterID.PAREKF_POSAIDSTDDEVTHR:PAREKF_POSAIDSTDDEVTHR_Payload,
    ParameterID.PAREKF_SCHULERMODE:PAREKF_SCHULERMODE_Payload,
    ParameterID.PAREKF_STOREDATT:PAREKF_STOREDATT_Payload,
    ParameterID.PAREKF_ODOMETER:PAREKF_ODOMETER_Payload,
    ParameterID.PAREKF_ODOBOGIE:PAREKF_ODOBOGIE_Payload,
    ParameterID.PAREKF_GNSSLEVERARMEST:PAREKF_GNSSLEVERARMEST_Payload,
    ParameterID.PAREKF_GNSSAIDRATE:PAREKF_GNSSAIDINGRATE_Payload,
    ParameterID.PAREKF_KINALIGNTHR:PAREKF_KINALIGNTHR_Payload,
    ParameterID.PAREKF_PDOPTHR:PAREKF_PDOPTHR_Payload,
    ParameterID.PAREKF_DUALANTAID:PAREKF_DUALANTAID_Payload,
    ParameterID.PAREKF_STARTUPV2:PAREKF_STARTUPV2_Payload,
    ParameterID.PAREKF_MAGATTAID:PAREKF_MAGATTAID_Payload,
    ParameterID.PAREKF_MADCAID:PAREKF_MADCAID_Payload,
    ParameterID.PAREKF_ALIGNMENT:PAREKF_ALIGNMENT_Payload,
    ParameterID.PAREKF_GRAVITYAID:PAREKF_GRAVITYAID_Payload,
    ParameterID.PAREKF_FEEDBACK:PAREKF_FEEDBACK_Payload,
    ParameterID.PAREKF_ZARU:PAREKF_ZARU_Payload,
    ParameterID.PAREKF_IMUCONFIG:PAREKF_IMUCONFIG_Payload,
    ParameterID.PAREKF_ZUPTCALIB:PAREKF_ZUPTCALIB_Payload,
    ParameterID.PAREKF_STATEFREEZE:PAREKF_STATEFREEZE_Payload,
    ParameterID.PAREKF_RECOVERY:PAREKF_RECOVERY_Payload,
    
    ParameterID.PARDAT_POS:PARDAT_POS_Payload,
    ParameterID.PARDAT_VEL:PARDAT_VEL_Payload,
    ParameterID.PARDAT_IMU:PARDAT_IMU_Payload,
    ParameterID.PARDAT_SYSSTAT:PARDAT_SYSSTAT_Payload,

    ParameterID.PARXCOM_SERIALPORT:PARXCOM_SERIALPORT_Payload,
    ParameterID.PARXCOM_NETCONFIG:PARXCOM_NETCONFIG_Payload,
    ParameterID.PARXCOM_LOGLIST:PARXCOM_LOGLIST_Payload,
    ParameterID.PARXCOM_AUTOSTART:PARXCOM_AUTOSTART_Payload,
    ParameterID.PARXCOM_POSTPROC:PARXCOM_POSTPROC_Payload,
    ParameterID.PARXCOM_BROADCAST:PARXCOM_BROADCAST_Payload,
    ParameterID.PARXCOM_NTRIP:PARXCOM_NTRIP_Payload,
    ParameterID.PARXCOM_UDPCONFIG:PARXCOM_UDPCONFIG_Payload,
    ParameterID.PARXCOM_DUMPENABLE:PARXCOM_DUMPENABLE_Payload,
    ParameterID.PARXCOM_MIGRATOR:PARXCOM_MIGRATOR_Payload,
    ParameterID.PARXCOM_FRAMEOUT:PARXCOM_FRAMEOUT_Payload,
    ParameterID.PARXCOM_TCPKEEPAL:PARXCOM_TCPKEEPAL_Payload,
    ParameterID.PARXCOM_CANGATEWAY:PARXCOM_CANGATEWAY_Payload,
    ParameterID.PARXCOM_DEFAULTIP:PARXCOM_DEFAULTIP_Payload,
    ParameterID.PARXCOM_ABDCONFIG:PARXCOM_ABDCONFIG_Payload,
    ParameterID.PARXCOM_LOGLIST2:PARXCOM_LOGLIST2_Payload,
    ParameterID.PARXCOM_CALPROC:PARXCOM_CALPROC_Payload,
    ParameterID.PARXCOM_CLIENT:PARXCOM_CLIENT_Payload,

    ParameterID.PARFPGA_IMUSTATUSREG: PARFPGA_IMUSTATUSREG_Payload,
    ParameterID.PARFPGA_HDLCREG: PARFPGA_HDLCREG_Payload,
    ParameterID.PARFPGA_TIMINGREG: PARFPGA_TIMINGREG_Payload,
    ParameterID.PARFPGA_TIMER: PARFPGA_TIMER_Payload,
    ParameterID.PARFPGA_INTERFACE: PARFPGA_INTERFACE_Payload,
    ParameterID.PARFPGA_CONTROLREG: PARFPGA_CONTROLREG_Payload,
    ParameterID.PARFPGA_POWERUPTHR: PARFPGA_POWERUPTHR_Payload,
    ParameterID.PARFPGA_INTMAT245: PARFPGA_INTMAT245_Payload,
    ParameterID.PARFPGA_TYPE: PARFPGA_TYPE_Payload,
    ParameterID.PARFPGA_GLOBALCONF: PARFPGA_GLOBALCONF_Payload,
    ParameterID.PARFPGA_HDLCPINMODE: PARFPGA_HDLCPINMODE_Payload,
    ParameterID.PARFPGA_POWER: PARFPGA_POWER_Payload,
    ParameterID.PARFPGA_ALARMTHR: PARFPGA_ALARMTHR_Payload,
    ParameterID.PARFPGA_PPTCONFIG: PARFPGA_PPTCONFIG_Payload,
    ParameterID.PARFPGA_AUTOWAKEUP: PARFPGA_AUTOWAKEUP_Payload,

    ParameterID.PARODO_SCF: PARODO_SCF_Payload,
    ParameterID.PARODO_TIMEOUT: PARODO_TIMEOUT_Payload,
    ParameterID.PARODO_MODE: PARODO_MODE_Payload,
    ParameterID.PARODO_LEVERARM: PARODO_LEVERARM_Payload,
    ParameterID.PARODO_VELSTDDEV: PARODO_VELSTDDEV_Payload,
    ParameterID.PARODO_DIRECTION: PARODO_DIRECTION_Payload,
    ParameterID.PARODO_CONSTRAINT: PARODO_CONSTRAINTS_Payload,
    ParameterID.PARODO_UPDATERATE: PARODO_RATE_Payload,
    ParameterID.PARODO_THR: PARODO_THR_Payload,
    ParameterID.PARODO_EQEP: PARODO_EQEP_Payload,

    ParameterID.PARARINC825_PORT: PARARINC825_PORT_Payload,
    ParameterID.PARARINC825_BAUD: PARARINC825_BAUD_Payload,
    ParameterID.PARARINC825_ENABLE: PARARINC825_ENABLE_Payload,
    ParameterID.PARARINC825_LOGLIST: PARARINC825_LOGLIST_Payload,
    ParameterID.PARARINC825_BUSRECOVERY: PARARINC825_BUSRECOVERY_Payload,
    ParameterID.PARARINC825_RESETSTATUS: PARARINC825_RESETSTATUS_Payload,
    ParameterID.PARARINC825_SCALEFACTOR: PARARINC825_SCALEFACTOR_Payload,
    ParameterID.PARARINC825_EVENTMASK: PARARINC825_EVENTMASK_Payload,

    ParameterID.PARNMEA_COM:PARNMEA_COM_Payload,
    ParameterID.PARNMEA_ENABLE:PARNMEA_ENABLE_Payload,
    ParameterID.PARNMEA_TXMASK:PARNMEA_TXMASK_Payload,
    ParameterID.PARNMEA_DECPLACES:PARNMEA_DECPLACES_Payload,
    ParameterID.PARNMEA_RATE:PARNMEA_RATE_Payload,
    ParameterID.PARNMEA_UDP:PARNMEA_UDP_Payload,

    ParameterID.PARARINC429_CONFIG:PARARINC429_CONFIG_Payload,
    ParameterID.PARARINC429_LIST:PARARINC429_LIST_Payload,

    ParameterID.PARIO_HW245:PARIO_HW245_Payload,
    ParameterID.PARIO_HW288:PARIO_HW288_Payload,
}
CommandPayloadDictionary = {
    CommandID.XCOM:XcomCommandPayload,
    CommandID.LOG:CMD_LOG_Payload,
    CommandID.EKF:CMD_EKF_Payload,
    CommandID.CONF:CMD_CONF_Payload,
    CommandID.EXTAID:CMD_EXT_Payload
}

MessagePayloadDictionary = {
    MessageID.IMURAW:IMU_Payload,
    MessageID.IMUCORR:IMU_Payload,
    MessageID.IMUCOMP:IMU_Payload,
    MessageID.IMUCAL: IMUCAL_Payload,

    MessageID.INSSOL:INSSOL_Payload,
    MessageID.INSRPY:INSRPY_Payload,
    MessageID.INSDCM:INSDCM_Payload,
    MessageID.INSQUAT:INSQUAT_Payload,
    MessageID.INSVELNED:INSVEL_Payload,
    MessageID.INSVELECEF:INSVEL_Payload,
    MessageID.INSVELBODY:INSVEL_Payload,
    MessageID.INSVELENU:INSVEL_Payload,
    MessageID.INSPOSLLH:INSPOSLLH_Payload,
    MessageID.INSPOSECEF:INSPOSECEF_Payload,
    MessageID.INSPOSUTM:INSPOSUTM_Payload,
    MessageID.INSPOSUTM:INSPOSUTM_Payload,
    MessageID.INSROTTEST:INSROTTEST_Payload,

    MessageID.EKFSTDDEV:EKFSTDDEV_Payload,
    MessageID.EKFSTDDEV2:EKFSTDDEV2_Payload,
    MessageID.EKFERROR:EKFERROR_Payload,
    MessageID.EKFERROR2:EKFERROR2_Payload,
    MessageID.EKFTIGHTLY:EKFTIGHTLY_Payload,
    MessageID.EKFPOSCOVAR:EKFPOSCOVAR_Payload,

    MessageID.GNSSSOL:GNSSSOL_Payload,
    MessageID.GNSSTIME:GNSSTIME_Payload,
    MessageID.GNSSSOLCUST:GNSSSOLCUST_Payload,
    MessageID.GNSSHDG:GNSSHDG_Payload,
    MessageID.GNSSLEVERARM:GNSSLEVERARM_Payload,
    MessageID.GNSSVOTER:GNSSVOTER_Payload,
    MessageID.GNSSHWMON:GNSSHWMON_Payload,
    MessageID.GNSSSATINFO:GNSSSATINFO_Payload,
    MessageID.GNSSALIGNBSL:GNSSALIGNBSL_Payload,

    MessageID.WHEELDATA:WHEELDATA_Payload,
    MessageID.AIRDATA:AIRDATA_Payload,
    MessageID.MAGDATA:MAGDATA_Payload,
    MessageID.SYSSTAT:SYSSTAT_Payload,
    MessageID.STATFPGA:STATFPGA_Payload,
    MessageID.POWER:POWER_Payload,
    MessageID.TEMP:TEMP_Payload,
    MessageID.HEAVE:HEAVE_Payload,
    MessageID.CANSTAT:CANSTAT_Payload,
    MessageID.TIME:TIME_Payload,
    MessageID.ARINC429STAT:ARINC429STAT_Payload,
    MessageID.EVENTTIME:EVENTTIME_Payload,
    MessageID.OMGINT:OMGINT_Payload,
    MessageID.POSTPROC: POSTPROC_Payload,

    MessageID.ADC24STATUS:ADC24STATUS_Payload,
    MessageID.ADC24DATA:ADC24DATA_Payload,

    MessageID.WHEELDATADBG:WHEELDATADBG_Payload
}


def getMessageWithID(msgID):
    message = XcomProtocolMessage()
    message.header.msgID = msgID
    if msgID in MessagePayloadDictionary:
        message.payload = MessagePayloadDictionary[msgID]()
        return message
    else:
        return None


def getCommandWithID(cmdID):
    message = XcomProtocolMessage()
    message.header.msgID = MessageID.COMMAND
    if cmdID in CommandPayloadDictionary:
        message.payload = CommandPayloadDictionary[cmdID]()
        message.payload.data['cmdID'] = cmdID
        return message
    else:
        return None


def getParameterWithID(parameterID):
    message = XcomProtocolMessage()
    message.header.msgID = MessageID.PARAMETER
    if parameterID in ParameterPayloadDictionary:
        message.payload = ParameterPayloadDictionary[parameterID]()
        message.payload.data['parameterID'] = parameterID
        return message
    else:
        return None
