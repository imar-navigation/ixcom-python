from .protocol import parameter, DefaultParameterPayload, Message, PayloadItem

"""
PARSYS
"""
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


@parameter(112)
class PARIMU_BANDSTOP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'bandwidth', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'center', dimension = 1, datatype = 'f'),
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

@parameter(226)
class PARGNSS_SWITCHER_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'switcher', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
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

@parameter(606)
class PARREC_SUFFIX_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'suffix', dimension = 128, datatype = 's'),
    ])


@parameter(607)
class PARREC_DISKSPACE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'freespace', dimension = 1, datatype = 'd'),
    ])
        
"""
PAREKF
"""
@parameter(700)
class PAREKF_ALIGNMODE_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'alignmode', dimension = 1, datatype = 'I'),
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

@parameter(704)
class PAREKF_AIDING_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'aidingMode', dimension = 1, datatype = 'I'),
        PayloadItem(name = 'aidingMask', dimension = 1, datatype = 'I'),
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

@parameter(708)
class PAREKF_HDGPOSTHR_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'hdgGoodThr', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'posMedThr', dimension = 1, datatype = 'f'),
        PayloadItem(name = 'posHighThr', dimension = 1, datatype = 'f'),
    ])

@parameter(709)
class PAREKF_SMOOTH_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'smooth', dimension = 1, datatype = 'I'),
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

@parameter(717)
class PAREKF_POWERDOWN_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'savestate', dimension = 1, datatype = 'I'),
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



@parameter(737)
class PAREKF_ZARU_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'enable', dimension = 1, datatype = 'B'),
        PayloadItem(name = 'reserved2', dimension = 3, datatype = 'B'),
    ])

@parameter(739)
class PAREKF_ZUPTCALIB_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'zuptCalibTime', dimension = 1, datatype = 'H'),
        PayloadItem(name = 'reserved2', dimension = 1, datatype = 'H'),
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

@parameter(915)
class PARXCOM_DEFAULTIP_Payload(DefaultParameterPayload):
    parameter_payload = Message([
        PayloadItem(name = 'defaultAddress', dimension = 1, datatype = 'I'),
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
