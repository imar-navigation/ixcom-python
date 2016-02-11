import collections
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
    POSTPROC      = 0x40

    EKFSTDDEV     = 0x0F
    EKFERROR      = 0x10

    GNSSSOL       = 0x12
    GNSSSTATUS    = 0x13
    GNSSTIME      = 0x14
    GNSSHDG       = 0x33
    GNSSLEVERARM  = 0x1B

    WHEELDATA     = 0x16
    AIRDATA       = 0x17
    MAGDATA       = 0x18
    SYSSTAT       = 0x19
    STATFPGA      = 0x20
    POWER         = 0x21
    TEMP          = 0x22

    IMUDBG        = 0x30
    IMUCAL        = 0x31
    WHEELDATADBG  = 0x32
    
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
    
    PARGNSS_PORT            = 200
    PARGNSS_BAUD            = 201
    PARGNSS_ANTOFFSET       = 204
    PARGNSS_RTKMODE         = 207
    PARGNSS_AIDFRAME        = 209
    PARGNSS_DUALANTMODE     = 211
    PARGNSS_ELEVATIONMASK   = 212
    
    PARMAG_PERIOD           = 302
    PARMAG_MISALIGN         = 304
    PARMAG_CAL              = 307
    PARMAG_CALSTATE         = 308
    PARMAG_FOM              = 309
    PARMAG_CFG              = 310
    
    PARMADC_PORT            = 400
    PARMADC_BAUD            = 401
    PARMADC_RATE            = 402
    PARMADC_LATENCY         = 403
    PARMADC_BAROCORRECTION  = 404
    PARMADC_FILTER          = 405
    
    PARMON_LEVEL            = 500
    PARMON_TPYE             = 501
    PARMON_PORT             = 502
    PARMON_BAUD             = 503
    
    PARREC_CONFIG           = 600
    PARREC_START            = 601
    PARREC_STOP             = 602
    PARREC_POWER            = 603
    
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
    
    PARDAT_POS              = 800
    PARDAT_VEL              = 801
    PARDAT_IMU              = 802
    PARDAT_SYSSTAT          = 803
    
    PARXCOM_SERIALPORT      = 902
    PARXCOM_NETCONFIG       = 903
    PARXCOM_LOGLISTE        = 905
    PARXCOM_AUTOSTART       = 906
    PARXCOM_NTRIP           = 907
    PARXCOM_POSTPROC        = 908
    PARXCOM_BROADCAST       = 909
    
    
    PARPCTRL_MODES          = 1010
    PARPCTRL_GAINS          = 1011
    PARPCTRL_INTERFACE      = 1012
    
    PARODO_SCF              = 1100
    PARODO_TIMEOUT          = 1101
    PARODO_MODE             = 1102
    PARODO_LEVERARM         = 1103
    PARODO_VELSTDDEV        = 1104
    PARODO_DIRECTION        = 1105
    PARODO_CONSTRAINT       = 1106
    PARODO_UPDATERATE       = 1107
    PARODO_THR              = 1108
    
    PARARINC825_PORT        = 1200
    PARARINC825_BAUD        = 1201
    PARARINC825_ENABLE      = 1202
    
    PARNMEA_COM             = 1300
    PARNMEA_ENABLE          = 1301
    PARNMEA_TXMASK          = 1302
    PARNMEA_DECPLACES       = 1303
    
    
class MessageItem(object):
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
        keyList = self.data.keys()
        valueList = list(struct.unpack(self.structString, inBytes))
        numberOfValues = 0
        for key in keyList:
            if isinstance(self.data[key], list):
                curLen = len(self.data[key])
                value = valueList[:curLen]
                valueList = valueList[curLen:]
            else:
                value = valueList[0]
                valueList = valueList[1:]
            self.data[key] = value
            
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
        self.structString += "IHH"
        self.data['baud'] = 0
        self.data['reserved2'] = 0
        self.data['password'] = 0     
             
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
        
class PARGNSS_ELEVATIONMASK_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['elevationMaskAngle'] = 0
        
"""
PARMAG
"""
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
        self.data['bias'] = 0   
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

class PARMAG_FOM_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "f"
        self.data['FOM'] = 0
        
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
        self.data['direction'] = 0
        
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
        
"""
PARREC
"""
class PARREC_CONFIG_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "BBH"
        self.data['channelNumber'] = 0
        self.data['enable'] = 0
        self.data['autostart'] = 0
        
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
        self.data['reserved2'] = 0
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
        self.structString += "IfffHH"
        self.data['samplePeriods'] = 0
        self.data['thrHdg'] = 0
        self.data['latency'] = 0
        self.data['thrINSHdg'] = 0
        self.data['mode'] = 0
        self.data['interval'] = 0

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
        self.structString += "BBBBI"
        self.data['port'] = 0
        self.data['switch'] = 0
        self.data['loopback'] = 0
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
        
class PARXCOM_AUTOSTART_Payload(XcomDefaultParameterPayload):
    def __init__(self):
        super().__init__()
        self.structString += "HHHH"
        self.data['channelNumber'] = 0
        self.data['autoStart'] = 0
        self.data['port'] = 0
        self.data['reserved2'] = 0
        
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
        
"""
Messages
"""
        
class POSTPROC_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f4d3d3dI2IfiIII"
        self.data['acc'] = [0, 0, 0]
        self.data['omg'] = [0, 0, 0]
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
        self.structString += "3f3f3f3fddfHH"
        self.data['acc'] = [0, 0, 0]
        self.data['omg'] = [0, 0, 0]
        self.data['rpy'] = [0, 0, 0]
        self.data['vel'] = [0, 0, 0]
        self.data['lon'] = 0
        self.data['lat'] = 0
        self.data['alt'] = 0
        self.data['DiffAge'] = 0
        self.data['DatSel'] = 0
        
class IMU_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f"
        self.data['acc'] = [0, 0, 0]
        self.data['omg'] = [0, 0, 0]

class IMUCAL_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3d3d4d3d3d16fI2I6I"
        self.data['accLSB'] = [0, 0, 0]
        self.data['omgLSB'] = [0, 0, 0]
        self.data['accCal'] = [0, 0, 0]
        self.data['omgCal'] = [0, 0, 0]
        self.data['q_nb']   = [1, 0, 0, 0]
        self.data['pos']    = [0, 0, 0]
        self.data['vel']    = [0, 0, 0]
        self.data['temp']   = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.data['sysstat']=  0
        self.data['ekfstat']= [0, 0]
        self.data['imustat']= [0, 0, 0, 0, 0, 0]
        
class SYSSTAT_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "II"
        self.data['mode']    = 0
        self.data['sysstat'] = 0
        
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
        self.structString += "Iddf"
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
        self.structString += "fffffffI"
        self.data['TAS']        = 0
        self.data['IAS']        = 0
        self.data['baroAlt']    = 0
        self.data['Vs']         = 0
        self.data['Pd']         = 0
        self.data['Ps']         = 0
        self.data['OAT']        = 0
        self.data['status']     = 0
        
class EKFSTDDEV_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "3f3f3f3f3f3f3ffI"
        self.data['pos']        = [0, 0, 0]
        self.data['vel']        = [0, 0, 0]
        self.data['tilt']       = [0, 0, 0]
        self.data['biasAcc']    = [0, 0, 0]
        self.data['biasOmg']    = [0, 0, 0]
        self.data['scfAcc']     = [0, 0, 0]
        self.data['scfOmg']     = [0, 0, 0]
        self.data['scfOdo']     =  0
        self.data['status']     =  0
        
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
        
class GNSSHDG_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "ffffHHHBI"
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
        
class GNSSSTATUS_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "I"
        self.data['status']        = 0

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
        
class WHEELDATADBG_Payload(XcomProtocolPayload):
    def __init__(self):
        super().__init__()
        self.structString += "fiIII"
        self.data['odoSpeed']       = 0
        self.data['ticks']          = 0
        self.data['interval']       = 0
        self.data['trigEvent']      = 0
        self.data['trigNextEvent']  = 0
        
CommandPayloadDictionary = {
    CommandID.XCOM:XcomCommandPayload,
    CommandID.LOG:CMD_LOG_Payload,
    CommandID.EKF:CMD_EKF_Payload,
    CommandID.CONF:CMD_CONF_Payload
                        }
ParameterPayloadDictionary = {
    ParameterID.PARSYS_PRJNUM:PARSYS_STRING_Payload, 
    ParameterID.PARSYS_PRJNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_PARTNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_SERIALNUM:PARSYS_STRING_Payload,
    ParameterID.PARSYS_MFG:PARSYS_STRING_Payload,
    ParameterID.PARSYS_CALDATE:PARSYS_STRING_Payload,
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
    
    ParameterID.PARGNSS_PORT:PARGNSS_PORT_Payload,
    ParameterID.PARGNSS_BAUD:PARGNSS_BAUD_Payload,
    ParameterID.PARGNSS_ANTOFFSET:PARGNSS_ANTOFFSET_Payload,
    ParameterID.PARGNSS_RTKMODE:PARGNSS_RTKMODE_Payload,
    ParameterID.PARGNSS_AIDFRAME:PARGNSS_AIDFRAME_Payload,
    ParameterID.PARGNSS_DUALANTMODE:PARGNSS_DUALANTMODE_Payload,
    ParameterID.PARGNSS_ELEVATIONMASK:PARGNSS_ELEVATIONMASK_Payload,
    
    ParameterID.PARMAG_PERIOD:PARMAG_PERIOD_Payload,
    ParameterID.PARMAG_MISALIGN:PARMAG_MISALIGN_Payload,
    ParameterID.PARMAG_CAL:PARMAG_CAL_Payload,
    ParameterID.PARMAG_CALSTATE:PARMAG_CALSTATE_Payload,
    ParameterID.PARMAG_FOM:PARMAG_FOM_Payload,
    ParameterID.PARMAG_CFG:PARMAG_CFG_Payload,
    
    ParameterID.PARODO_SCF:PARODO_SCF_Payload,
    ParameterID.PARODO_TIMEOUT:PARODO_TIMEOUT_Payload,
    ParameterID.PARODO_MODE:PARODO_MODE_Payload,
    ParameterID.PARODO_LEVERARM:PARODO_LEVERARM_Payload,
    ParameterID.PARODO_VELSTDDEV:PARODO_VELSTDDEV_Payload,
    ParameterID.PARODO_DIRECTION:PARODO_DIRECTION_Payload,
    ParameterID.PARODO_CONSTRAINT:PARODO_CONSTRAINTS_Payload,
    ParameterID.PARODO_UPDATERATE:PARODO_RATE_Payload,
    ParameterID.PARODO_THR:PARODO_THR_Payload,
    
    ParameterID.PARREC_CONFIG:PARREC_CONFIG_Payload,
    ParameterID.PARREC_START:PARREC_START_Payload,
    ParameterID.PARREC_STOP:PARREC_STOP_Payload,
    ParameterID.PARREC_POWER:PARREC_POWER_Payload,
    
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
    
    ParameterID.PARDAT_POS:PARDAT_POS_Payload,
    ParameterID.PARDAT_VEL:PARDAT_VEL_Payload,
    ParameterID.PARDAT_IMU:PARDAT_IMU_Payload,
    ParameterID.PARDAT_SYSSTAT:PARDAT_SYSSTAT_Payload,
    
    ParameterID.PARXCOM_SERIALPORT:PARXCOM_SERIALPORT_Payload,
    ParameterID.PARXCOM_NETCONFIG:PARXCOM_NETCONFIG_Payload,
    ParameterID.PARXCOM_AUTOSTART:PARXCOM_AUTOSTART_Payload,
    ParameterID.PARXCOM_POSTPROC:PARXCOM_POSTPROC_Payload,
    ParameterID.PARXCOM_BROADCAST:PARXCOM_BROADCAST_Payload
}

MessagePayloadDictionary = {
    MessageID.IMURAW:IMU_Payload,
    MessageID.IMUCORR:IMU_Payload,
    MessageID.IMUCOMP:IMU_Payload,
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
    MessageID.POSTPROC:POSTPROC_Payload,

    MessageID.EKFSTDDEV:EKFSTDDEV_Payload,
    MessageID.EKFERROR:EKFERROR_Payload,

    MessageID.GNSSSOL:GNSSSOL_Payload,
    MessageID.GNSSSTATUS:GNSSSTATUS_Payload,
    MessageID.GNSSTIME:GNSSTIME_Payload,
    MessageID.GNSSHDG:GNSSHDG_Payload,
    MessageID.GNSSLEVERARM:GNSSLEVERARM_Payload,

    MessageID.WHEELDATA:WHEELDATA_Payload,
    MessageID.AIRDATA:AIRDATA_Payload,
    MessageID.MAGDATA:MAGDATA_Payload,
    MessageID.SYSSTAT:SYSSTAT_Payload,
    #MessageID.STATFPGA:,
    MessageID.POWER:POWER_Payload,
    MessageID.TEMP:TEMP_Payload,

    #MessageID.IMUDBG:,
    MessageID.IMUCAL:IMUCAL_Payload,
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