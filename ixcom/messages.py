import struct
from .protocol import message, ProtocolPayload, MessageID, PayloadItem, Message

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