from .protocol import DefaultCommandPayload, command, Message, PayloadItem

"""
Commands
"""
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
