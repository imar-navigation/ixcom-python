import socket
import select
import threading
import collections
import crc16
import math
import time
import struct
from enum import IntEnum
from xcom import xcomdata

PositionTuple = collections.namedtuple('PositionTuple', 'Lon Lat Alt')

SYNC_BYTE = 0x7E
GENERAL_PORT = 3000
BROADCAST_PORT = 4000
LAST_CHANNEL_NUMBER = 31
WAIT_TIME_FOR_RESPONSE = 10

class XcomError(Exception):
    def __init__(self, message = '', thrower = None):
        super().__init__(message)
        self.thrower = thrower

class ResponseError(XcomError):
    pass

class StatusError(XcomError):
    pass

class ClientTimeoutError(XcomError):
    pass



class XcomMessageSearcherState(IntEnum):
    waiting_for_sync = 0
    waiting_for_msglength = 1
    fetching_bytes = 2


class XcomMessageSearcher:
    def __init__(self, parserDelegate = None, disable_crc = False):
        self.searcherState = XcomMessageSearcherState.waiting_for_sync
        self.currentBytes = bytearray(b' ' * 512)
        self.currentByteIdx = 0
        self.remainingByteCount = 0
        self.disableCRC = disable_crc
        self.callbacks = []
        if parserDelegate is not None:
            self.callbacks.append(parserDelegate.parse)

    def process_bytes(self, inBytes):
        inByteIdx = 0
        while inByteIdx < len(inBytes):

            if self.searcherState == XcomMessageSearcherState.waiting_for_sync:
                poppedByte = inBytes[inByteIdx]
                inByteIdx += 1
                if poppedByte == SYNC_BYTE:
                    self.currentBytes[0] = SYNC_BYTE
                    self.currentByteIdx = 1
                    self.remainingByteCount = 5
                    self.searcherState = XcomMessageSearcherState.waiting_for_msglength
            elif self.searcherState == XcomMessageSearcherState.waiting_for_msglength:
                poppedByte = inBytes[inByteIdx]
                inByteIdx += 1
                self.currentBytes[self.currentByteIdx] = poppedByte
                self.currentByteIdx += 1
                self.remainingByteCount -= 1
                if self.remainingByteCount == 0:
                    self.remainingByteCount = self.currentBytes[self.currentByteIdx - 1] * 256 + self.currentBytes[
                        self.currentByteIdx - 2] - 6
                    if self.remainingByteCount < 600:
                        self.searcherState = XcomMessageSearcherState.fetching_bytes
                    else:
                        self.searcherState = XcomMessageSearcherState.waiting_for_sync
            elif self.searcherState == XcomMessageSearcherState.fetching_bytes:
                if len(
                        inBytes) - 1 >= self.remainingByteCount + inByteIdx - 1:  # Der Buffer ist Länger als der Rest der Nachricht.
                    self.currentBytes[self.currentByteIdx:self.currentByteIdx + self.remainingByteCount] = inBytes[
                                                                                                           inByteIdx:inByteIdx + self.remainingByteCount]
                    self.currentByteIdx = self.currentByteIdx + self.remainingByteCount
                    inByteIdx = inByteIdx + self.remainingByteCount
                    self.remainingByteCount = 0
                else:
                    self.currentBytes[self.currentByteIdx:self.currentByteIdx + (len(inBytes) - inByteIdx)] = inBytes[
                                                                                                              inByteIdx:]
                    self.currentByteIdx = self.currentByteIdx + (len(inBytes) - inByteIdx)
                    self.remainingByteCount -= (len(inBytes) - inByteIdx)
                    inByteIdx = len(inBytes)
                if self.remainingByteCount == 0:
                    if self.disableCRC:
                        self.publish(self.currentBytes[:self.currentByteIdx])
                    else:
                        crc = crc16.crc16xmodem(bytes(self.currentBytes[:self.currentByteIdx - 2]))
                        if crc == self.currentBytes[self.currentByteIdx - 2] + self.currentBytes[
                                    self.currentByteIdx - 1] * 256:
                            self.publish(self.currentBytes[:self.currentByteIdx])
                        else:
                            pass
                    self.searcherState = XcomMessageSearcherState.waiting_for_sync

    def publish(self, msg_bytes):
        for callback in self.callbacks:
            callback(msg_bytes)

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        self.callbacks.remove(callback)


class XcomMessageParser:
    def __init__(self):
        self.subscribers = set()
        self.callbacks = list()
        self.messageSearcher = XcomMessageSearcher(self)

    def parse_response(self, inBytes):
        message = xcomdata.XcomProtocolMessage()
        message.header.from_bytes(inBytes[:16])
        message.payload = xcomdata.XcomResponsePayload(message.header.msgLength)
        message.from_bytes(inBytes)
        self.publish(message)

    def parse_parameter(self, inBytes):
        message = xcomdata.XcomProtocolMessage()
        message.payload = xcomdata.XcomDefaultParameterPayload()
        message.payload.from_bytes(inBytes[16:20])
        parameterID = message.payload.data['parameterID']
        message = xcomdata.getParameterWithID(parameterID)
        if message is not None:
            message.from_bytes(inBytes)
            self.publish(message)
        else:
            pass

    def parse_command(self, inBytes):
        message = xcomdata.XcomProtocolMessage()
        message.payload = xcomdata.XcomDefaultCommandPayload()
        message.payload.from_bytes(inBytes[16:20])
        cmdID = message.payload.data['cmdID']
        message = xcomdata.getCommandWithID(cmdID)
        if message is not None:
            message.from_bytes(inBytes)
            self.publish(message)
        else:
            pass

    def parse(self, inBytes):
        header = xcomdata.XcomProtocolHeader()
        header.from_bytes(inBytes)
        if header.msgID == xcomdata.MessageID.RESPONSE:
            self.parse_response(inBytes)
        elif header.msgID == xcomdata.MessageID.PARAMETER:
            self.parse_parameter(inBytes)
        elif header.msgID == xcomdata.MessageID.COMMAND:
            self.parse_command(inBytes)
        else:
            message = xcomdata.getMessageWithID(header.msgID)
            if message is not None:
                message.from_bytes(inBytes)
                self.publish(message)

    def add_subscriber(self, subscriber):
        self.subscribers.add(subscriber)

    def add_callback(self, callback):
        self.callbacks += [callback]

    def remove_callback(self, callback):
        self.callbacks.remove(callback)

    def remove_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def publish(self, message):
        for subscriber in self.subscribers:
            subscriber.handle_message(message, from_device=self)
        for callback in self.callbacks:
            callback(message, from_device=self)


class XcomClient(XcomMessageParser):
    '''XCOM TCP Client

    Implements a TCP-socket based XCOM client and offers convenience methods to interact with the 
    device. Other classes may subscribe to decoded messages.
    '''

    def __init__(self, host, port=GENERAL_PORT):
        XcomMessageParser.__init__(self)
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        
        self.response_event = threading.Event()
        self.response_event.response = None
        self.parameter_event = threading.Event()
        self.parameter_event.parameter = None
        self.message_event = threading.Event()
        self.message_event.msg = None
        self.message_event.id = None
        self.okay_lock = threading.Lock()
        self.thread = threading.Thread(target = self.update_data)
        self.thread.start()
        
        self.add_subscriber(self)


    def __hash__(self):
        '''Hash function

        Implements hash to use a Client as a key in a dictionary

        Args:
            self
        Returns:
            A hash
        '''
        return id(self)

    def __eq__(self, other):
        return self is other
        
    def handle_message(self, message, from_device):
       if message.header.msgID == xcomdata.MessageID.RESPONSE:
           self.response_event.response = message
           self.response_event.set()
       elif message.header.msgID == xcomdata.MessageID.PARAMETER:           
           self.parameter_event.parameter = message
           self.parameter_event.set()
       elif message.header.msgID == self.message_event.id:
           self.message_event.msg = message
           self.message_event.set()
        

    def open_channel(self, channelNumber=0):
        '''Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Args:
            chnannelNumber: XCOM channel to open. Default = 0

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.channel_open
        msgToSend.payload.data['channelNumber'] = channelNumber
        self.send_msg_and_waitfor_okay(msgToSend)

    def update_data(self):
        while True:
            inputready, _, _ = select.select([self.sock], [],[], 0.1)
            for _ in inputready:
                self.messageSearcher.process_bytes(self.sock.recv(1024))

    def enable_calproc(self, rate, channel, pathname):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_CALPROC)
        msgToSend.payload.data['enable'] = 1
        msgToSend.payload.data['channel'] = channel
        msgToSend.payload.data['divider'] = round(self.get_divider_for_rate(rate))
        msgToSend.payload.data['pathName'] = pathname.ljust(256, '\0').encode('ascii')
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def disable_calproc(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_CALPROC)
        msgToSend.payload.data['enable'] = 0
        msgToSend.payload.data['channel'] = 0
        msgToSend.payload.data['divider'] = 1
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)


    def open_last_free_channel(self):
        '''Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
            
        Returns:
            channelNumber: number of the opened channel
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.channel_open
        channelNumber = LAST_CHANNEL_NUMBER
        while channelNumber >= 0:
            msgToSend.payload.data['channelNumber'] = channelNumber
            try:
                self.send_msg_and_waitfor_okay(msgToSend)
                self.clear_all()
                return channelNumber
            except ResponseError:
                channelNumber -= 1
                if channelNumber == 0:
                    raise RuntimeError('No free channel on the system!')

    def open_first_free_channel(self):
        '''Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
            
        Returns:
            channelNumber: number of the opened channel
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.channel_open
        channelNumber = 0
        while channelNumber <= LAST_CHANNEL_NUMBER:
            msgToSend.payload.data['channelNumber'] = channelNumber
            try:
                self.send_msg_and_waitfor_okay(msgToSend)
                return channelNumber
            except:
                channelNumber += 1
                if channelNumber > LAST_CHANNEL_NUMBER:
                    raise RuntimeError('No free channel on the system!')

    def close_channel(self, channelNumber=0):
        '''Closes an XCOM logical channel

        Closes an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Args:
            chnannelNumber: XCOM channel to close. Default = 0

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.channel_close
        msgToSend.payload.data['channelNumber'] = channelNumber
        self.send_msg_and_waitfor_okay(msgToSend)

    def reset_timebias(self):
        '''Reset internal time bias

        Reset the internial clock bias to zero and waits for an 'OK' response.
        E.G. to snyc several device to a common time base

        Args:
            none

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.reset_timebias
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)


    def reboot(self):
        '''Reboots the system

        Sends an XCOM reboot command on the associated socket and waits for an 'OK' response.

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.reboot
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_parameter(self, parameterID):
        '''Gets parameter from Server with specified ID

        Gets the specified parameter. Blocks until parameter is retrieved.

        Args:
            parameterID: ID of the parameter to retrieve
        
        Returns:
            An XcomMessage object containing the parameter
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getParameterWithID(parameterID)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.REQUESTING
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_parameter()

    def set_aligncomplete(self):
        '''Completes the alignment

        Completes system alignment by sending the EKF ALIGN_COMPLETE command. Blocks until system
        repsonse is received.

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.ALIGN_COMPLETE
        self.send_msg_and_waitfor_okay(msgToSend)

    def realign(self):
        '''Initiates a new alignment

        Initiates a new system alignment by sending the EKF ALIGN command. Blocks until system 
        repsonse is received.

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.ALIGN
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_pos(self):
        '''Saves the current position

        Saves the current system position in ROM. Uses the EKF SAVE_POS command

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.SAVEPOS
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_hdg(self):
        '''Saves the current heading

        Saves the current heading position in ROM. Uses the EKF SAVE_HDG command

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.SAVE_HDG
        self.send_msg_and_waitfor_okay(msgToSend)

    def forced_zupt(self, enable):
        '''Enables or disables forced Zero Velocity updates

        Enables or disables forced Zero Velocity updates using the EKF FORCED_ZUPT command.
        
        Args:
            enable: boolean value to enable or disable ZUPTs.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.FORCED_ZUPT
        msgToSend.payload.structString += 'f'
        msgToSend.payload.data['enable'] = enable
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_antoffset(self, antenna):
        '''Saves the currently estimated GNSS antenna offset

        Saves the currently estimated GNSS antenna offset using the EKF SAVE_ANTOFFSET command.
        
        Args:
            antenna: Antenna # to save the offset for.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.SAVE_ANTOFFSET
        msgToSend.payload.structString += 'f'
        msgToSend.payload.data['antenna'] = antenna
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_config(self):
        '''Saves the current configuration

        Saves the current configuration to ROM using the CONF SAVE_CONFIG command.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.CONF)
        msgToSend.payload.data['configAction'] = 0
        self.send_msg_and_waitfor_okay(msgToSend)

    def load_config(self):
        '''Loads the configuration from ROM

        Loads the configuration from ROM using the CONF LOAD_CONFIG command.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.CONF)
        msgToSend.payload.data['configAction'] = 1
        self.send_msg_and_waitfor_okay(msgToSend)

    def factory_reset(self):
        '''Performs a factory reset

        Performs a factory reset using the CONF FACTORY_RESET command.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.CONF)
        msgToSend.payload.data['configAction'] = 4
        self.send_msg_and_waitfor_okay(msgToSend)

    def add_log_with_rate(self, msgID, rate):
        '''Add a log with specified rate

        Adds a log with a specific message ID with a specified rate. The divider is computed by
        taking into account the MAINTIMING and PRESCALER system parameters.
        
        Args:
            msgID: Mesage ID which should be requested.
            rate: Requested log rate in Hz
            
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK' or if rate too high.
        
        '''
        divider = self.get_divider_for_rate(rate)
        self.add_log_sync(msgID, math.ceil(divider))

    def get_divider_for_rate(self, rate):
        maintiming = self.get_parameter(xcomdata.ParameterID.PARSYS_MAINTIMING)
        prescaler = self.get_parameter(xcomdata.ParameterID.PARSYS_PRESCALER)
        divider = (maintiming.payload.data['maintiming'] / rate / prescaler.payload.data['prescaler'])
        if divider < 1:
            raise ValueError('Selected rate too high')
        else:
            return divider

    def add_log_sync(self, msgID, divider):
        '''Add a log with specified divider

        Adds a log with a specific message ID with a divider.
        
        Args:
            msgID: Mesage ID which should be requested.
            divider: divider to use
            
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.ADD
        msgToSend.payload.data['divider'] = divider
        self.send_msg_and_waitfor_okay(msgToSend)
        
    def add_log_event(self, msgID):
        '''Add a log with specified event

        Adds a log with a specific message ID to be sent at event.
        
        Args:
            msgID: Mesage ID which should be requested.
            
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.EVENT
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.ADD
        msgToSend.payload.data['divider'] = 500 # use 500 here, because a '1' is rejected from some logs
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)

    def clear_all(self):
        '''Clears all logs

        Sends a CLEAR_ALL command to the system.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = 3
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.CLEAR_ALL
        msgToSend.payload.data['divider'] = 1
        self.send_msg_and_waitfor_okay(msgToSend)

    def poll_log(self, msgID):
        '''Polls a log

        Polls a log with a specified message ID. Blocks until the log is retrieved and returns 
        the log.

        Args:
            msgID: Message ID to poll
        
        Returns:
            The polled log
        
        Raises:
            TimeoutError: Timeout while waiting for response or log from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.POLLED
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.ADD
        msgToSend.payload.data['divider'] = 500  # use 500 here, because a '1' is rejected from some logs
        self.message_event.id = msgID
        self.message_event.clear()
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_log(msgID)

    def wait_for_parameter(self):
        '''Waits for reception of parameter

        Blocks until a parameterEvent is received.
        
        Raises:
            TimeoutError: Timeout while waiting for parameter from the XCOM server
        
        '''
        self.update_until_event(self.parameter_event, WAIT_TIME_FOR_RESPONSE)
        result = self.parameter_event.parameter
        return result

    def update_until_event(self, event, timeout):
        event.wait(timeout=timeout)
        if event.is_set:
            event.clear()
            return
        raise ClientTimeoutError('Timeout while waiting for event', thrower=self)
        

    def wait_for_log(self, msgID):
        '''Waits for reception of log

        Blocks until a messageEvent is received.
        
        Args:
            msgID: message ID of log to wait for.
        
        Raises:
            TimeoutError: Timeout while waiting for message from the XCOM server
        
        '''
        self.update_until_event(self.message_event, WAIT_TIME_FOR_RESPONSE)
        result = self.message_event.msg
        return result

        

    def enable_recorder(self, channel, enable_autostart):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_CONFIG)
        msgToSend.payload.data['channelNumber'] = channel
        msgToSend.payload.data['autostart'] = enable_autostart
        msgToSend.payload.data['enable'] = 1
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def disable_recorder(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_CONFIG)
        msgToSend.payload.data['enable'] = 0
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def start_recorder(self, path):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_START)
        msgToSend.payload.data['str'] = path.ljust(128, '\0').encode('ascii')
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def stop_recorder(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_STOP)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_recorder_suffix(self, suffix):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_SUFFIX)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['suffix'] = suffix.ljust(128, '\0')
        self.send_msg_and_waitfor_okay(msgToSend)

    def enable_full_sysstatus(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARDAT_SYSSTAT)
        msgToSend.payload.data['statMode'] = 127
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_schulermode(self, enable_schuler):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_SCHULERMODE)
        msgToSend.payload.data['enable'] = enable_schuler
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def update_firmware_svn(self):
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode'] = xcomdata.XcomCommandParameter.update_svn
        msgToSend.payload.data['channelNumber'] = 0
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_device_info(self):
        result = dict()
        result['prjnumber'] = self.get_parameter(0).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['partnumber'] = self.get_parameter(1).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['serialnumber'] = self.get_parameter(2).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['mfgdate'] = self.get_parameter(3).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['caldate'] = self.get_parameter(4).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['fwversion'] = self.get_parameter(5).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['navversion'] = self.get_parameter(6).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['ekfversion'] = self.get_parameter(7).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['ekfparset'] = self.get_parameter(8).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['navnum'] = self.get_parameter(9).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['navparset'] = self.get_parameter(10).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['sysname'] = self.get_parameter(19).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['imutype'] = self.get_parameter(107).payload.data['type']
        result['maintiming'] = self.get_parameter(xcomdata.ParameterID.PARSYS_MAINTIMING).payload.data['maintiming']
        try:
            result['gyro_range'] = self.get_parameter(xcomdata.ParameterID.PARIMU_RANGE).payload.data['range_gyro']
        except:
            pass
        result['ip'] = self.host
        return result

    def set_caldate(self, caldate = time.strftime('%d.%m.%Y', time.gmtime())):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARSYS_CALDATE)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['str']= caldate.ljust(32,'\0').encode('ascii')
        msgToSend.payload.data['password'] = self.get_password(xcomdata.ParameterID.PARSYS_CALDATE)
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_imucalib(self, scf_acc, bias_acc, scf_omg, bias_omg):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARIMU_CALIB)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['sfAcc']= scf_acc
        msgToSend.payload.data['biasAcc'] = bias_acc
        msgToSend.payload.data['sfOmg']= scf_omg
        msgToSend.payload.data['biasOmg'] = bias_omg
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_imucalib(self):
        return self.get_parameter(xcomdata.ParameterID.PARIMU_CALIB)

    def set_acc_scf(self, scf_acc):
        msgToSend = self.get_imucalib()
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['sfAcc']= scf_acc
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_acc_bias(self, bias_acc):
        msgToSend = self.get_imucalib()
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['biasAcc']= bias_acc
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_gyro_bias(self, bias_omg):
        msgToSend = self.get_imucalib()
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['biasOmg']= bias_omg
        self.send_msg_and_waitfor_okay(msgToSend)
    

    def set_gyro_scf(self, scf_omg):
        msgToSend = self.get_imucalib()
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['sfOmg']= scf_omg
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_broadcast(self, port=BROADCAST_PORT, hidden=0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_BROADCAST)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['port'] = port
        msgToSend.payload.data['hidden_mode'] = hidden
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_zupt_parameters(self, thr_acc=1, thr_omg=1, thr_vel=0, cut_off=1, interval=3, final_std_dev=0.002,
                            start_std_dev=0.01, time_constant=1, delay_samples=300, activation_mask=0x0, auto_zupt=1):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_ZUPT)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['accThr'] = thr_acc
        msgToSend.payload.data['omgThr'] = thr_omg
        msgToSend.payload.data['velThr'] = thr_vel
        msgToSend.payload.data['cutoff'] = cut_off
        msgToSend.payload.data['zuptrate'] = interval
        msgToSend.payload.data['minStdDev'] = final_std_dev
        msgToSend.payload.data['weightingFactor'] = start_std_dev
        msgToSend.payload.data['timeConstant'] = time_constant
        msgToSend.payload.data['delay'] = delay_samples
        msgToSend.payload.data['mask'] = activation_mask
        msgToSend.payload.data['autoZupt'] = auto_zupt
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_startup(self, initPos=PositionTuple(Lon=0.1249596927, Lat=0.8599914412, Alt=311.9),
                    initPosStdDev=[10, 10, 10], posMode=xcomdata.StartupPositionMode.GNSSPOS, initHdg=0,
                    initHdgStdDev=1, hdgMode=xcomdata.StartupHeadingMode.DEFAULT, realign=0, inMotion=0,
                    leverArm=[0, 0, 0], leverArmStdDev=[1, 1, 1], autorestart=0, gnssTimeout=600):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_STARTUPV2)
        msgToSend.payload.data['initLon'] = initPos.Lon
        msgToSend.payload.data['initLat'] = initPos.Lat
        msgToSend.payload.data['initAlt'] = initPos.Alt
        msgToSend.payload.data['stdDev'] = initPosStdDev
        msgToSend.payload.data['initHdg'] = initHdg
        msgToSend.payload.data['stdDevHdg'] = initHdgStdDev
        msgToSend.payload.data['posMode'] = posMode
        msgToSend.payload.data['hdgMode'] = hdgMode
        msgToSend.payload.data['leverArm'] = leverArm
        msgToSend.payload.data['stdLeverArm'] = leverArmStdDev
        msgToSend.payload.data['gnssTimeout'] = gnssTimeout
        msgToSend.payload.data['altMSL'] = 0
        msgToSend.payload.data['realign'] = realign
        msgToSend.payload.data['inMotion'] = inMotion
        msgToSend.payload.data['autoRestart'] = autorestart
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_parekf_aiding(self, mode=0, mask=0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_AIDING)
        msgToSend.payload.data['aidingMode'] = mode
        msgToSend.payload.data['aidingMask'] = mask
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)


    def set_aligntime(self, levelling_time, zupt_time):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_ALIGNTIME)
        msgToSend.payload.data['aligntime'] = zupt_time
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_COARSETIME)
        msgToSend.payload.data['coarsetime'] = levelling_time
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_alignmode(self, mode):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_ALIGNMODE)
        msgToSend.payload.data['alignmode'] = mode
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_thresholds(self, pos_medium=1, pos_high=0.1, heading_good=0.001 * math.pi / 180.0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_HDGPOSTHR)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['hdgGoodThr'] = heading_good
        msgToSend.payload.data['posMedThr'] = pos_medium
        msgToSend.payload.data['posHighThr'] = pos_high
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_crosscoupling(self, CCAcc, CCOmg):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARIMU_CROSSCOUPLING)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['CCAcc'] = CCAcc
        msgToSend.payload.data['CCOmg'] = CCOmg
        self.send_msg_and_waitfor_okay(msgToSend)

    def send_msg_and_waitfor_okay(self, msg):
        self.okay_lock.acquire()
        bytesToSend = msg.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        self.okay_lock.release()

    def get_crosscoupling(self):
        param = self.get_parameter(xcomdata.ParameterID.PARIMU_CROSSCOUPLING)
        returnDict = dict()
        returnDict['CCAcc'] = param.payload.data['CCAcc']
        returnDict['CCOmg'] = param.payload.data['CCOmg']
        return returnDict

    def set_imu_misalign(self, x, y, z):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARIMU_MISALIGN)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['rpy'] = [x, y, z]
        self.send_msg_and_waitfor_okay(msgToSend)


    def enable_postproc(self, channel, copy_channel=0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_POSTPROC)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['channel'] = channel
        msgToSend.payload.data['enable'] = 1
        msgToSend.payload.data['log_mode'] = copy_channel
        self.send_msg_and_waitfor_okay(msgToSend)
        self.save_config()

    def disable_postproc(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_POSTPROC)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['enable'] = 0
        self.send_msg_and_waitfor_okay(msgToSend)
        self.save_config()

    def set_elevationmask(self, mask_angle):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARGNSS_ELEVATIONMASK)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['elevationMaskAngle'] = mask_angle
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_feedback(self, pos=1, vel=1, att=1, sensor_err=1):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_FEEDBACK)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['feedbackMask'] = (pos << 0) | (vel << 1) | (att << 2) | (sensor_err << 3)
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_freeze(self, pos=0, vel=0, att=0, height=0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_STATEFREEZE)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['freezeMask'] = (pos << 0) | (vel << 1) | (att << 2) | (height << 3)
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_pos(self, lonLatAlt, llhStdDev, leverarmXYZ, leverarmStdDev, time=0, timeMode=1):
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EXTAID)
        msgToSend.payload.data['time'] = time
        msgToSend.payload.data['timeMode'] = timeMode
        msgToSend.payload.data['cmdParamID'] = 3
        msgToSend.payload.structString += 'dddddddddddd'
        msgToSend.payload.data['lon'] = lonLatAlt[0]
        msgToSend.payload.data['lat'] = lonLatAlt[1]
        msgToSend.payload.data['alt'] = lonLatAlt[2]
        msgToSend.payload.data['lonStdDev'] = llhStdDev[0]
        msgToSend.payload.data['latStdDev'] = llhStdDev[1]
        msgToSend.payload.data['altStdDev'] = llhStdDev[2]
        msgToSend.payload.data['laX'] = leverarmXYZ[0]
        msgToSend.payload.data['laY'] = leverarmXYZ[1]
        msgToSend.payload.data['laZ'] = leverarmXYZ[2]
        msgToSend.payload.data['laXStdDev'] = leverarmStdDev[0]
        msgToSend.payload.data['laYStdDev'] = leverarmStdDev[1]
        msgToSend.payload.data['laZStdDev'] = leverarmStdDev[2]
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_vel(self, vNED, vNEDStdDev, time=0, timeMode=1):
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EXTAID)
        msgToSend.payload.data['time'] = time
        msgToSend.payload.data['timeMode'] = timeMode
        msgToSend.payload.data['cmdParamID'] = 4
        msgToSend.payload.structString += 'dddddd'
        msgToSend.payload.data['vN'] = vNED[0]
        msgToSend.payload.data['vE'] = vNED[1]
        msgToSend.payload.data['vD'] = vNED[2]
        msgToSend.payload.data['vNStdDev'] = vNEDStdDev[0]
        msgToSend.payload.data['vEStdDev'] = vNEDStdDev[1]
        msgToSend.payload.data['vDStdDev'] = vNEDStdDev[2]
        # msgToSend.payload.data['laX'] = leverarmXYZ[0];
        # msgToSend.payload.data['laY'] = leverarmXYZ[1];
        # msgToSend.payload.data['laZ'] = leverarmXYZ[2];
        # msgToSend.payload.data['laXStdDev'] = leverarmStdDev[0];
        # msgToSend.payload.data['laYStdDev'] = leverarmStdDev[1];
        # msgToSend.payload.data['laZStdDev'] = leverarmStdDev[2];
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_heading(self, heading, standard_dev, time=0, timeMode=1):
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EXTAID)
        msgToSend.payload.data['time'] = time
        msgToSend.payload.data['timeMode'] = timeMode
        msgToSend.payload.data['cmdParamID'] = 5
        msgToSend.payload.structString += 'dd'
        msgToSend.payload.data['heading'] = heading
        msgToSend.payload.data['headingStdDev'] = standard_dev
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_height(self, height, standard_dev, time=0, timeMode=1):
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EXTAID)
        msgToSend.payload.data['time'] = time
        msgToSend.payload.data['timeMode'] = timeMode
        msgToSend.payload.data['cmdParamID'] = 6
        msgToSend.payload.structString += 'dd'
        msgToSend.payload.data['height'] = height
        msgToSend.payload.data['heightStdDev'] = standard_dev
        self.send_msg_and_waitfor_okay(msgToSend)

    def send_and_wait_for_okay(self, inBytes):
        '''Waits for reception of OK response

        Send the bytes and waits for an OK response from the system
        
        Args:
            inBytes: bytes to send
        
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        self.sock.sendall(inBytes)
        self.update_until_event(self.response_event, WAIT_TIME_FOR_RESPONSE)
        response = self.response_event.response
        if response.payload.data['responseID'] != xcomdata.XcomResponse.OK:
            raise ResponseError(self.response_event.response.data['responseText'].decode('ascii'), self)

    def run_forever(self):
        while True:
            self.update_data()

    def get_antoffset(self, antenna):
        '''Convenience getter for antenna offset

        Gets the antenna offset for the specified antenna #
        
        Args:
            antenna: Antenna # to retrieve the antenna offset for.
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARGNSS_ANTOFFSET)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.REQUESTING
        msgToSend.payload.data['reserved'] = antenna
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_parameter()

    def set_antoffset(self, antenna=0, offset=[0, 0, 0], stdDev=[0.1, 0.1, 0.1]):
        '''Convenience setter for antenna offset

        Sets the antenna offset for the specified antenna #
        
        Args:
            antenna: Antenna # to retrieve the antenna offset for.
            offset: antenna offset in m.
            stdDev: standard deviation of antenna offset in m.
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARGNSS_ANTOFFSET)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['reserved'] = antenna
        msgToSend.payload.data['antennaOffset'] = offset
        msgToSend.payload.data['stdDev'] = stdDev
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_password(self, parameter_id):
        tmp_buffer = struct.pack('=BBBBH', 11, 6, 19, 85, parameter_id)
        return crc16.crc16xmodem(tmp_buffer)
        
    def set_gpspower(self, state):
        msgToSend = self.get_parameter(xcomdata.ParameterID.PARFPGA_POWER)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        if state == 1:
            msgToSend.payload.data['powerSwitch'] |= 1
        elif state == 0:
            msgToSend.payload.data['powerSwitch'] &= ~(1 << 0)
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_virtual_meas_pt(self):
        '''Convenience getter for virtual measpoint offset

        Gets the virtual measpoint offset for the output values defined with the mask #
                
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        return self.get_parameter(xcomdata.ParameterID.PAREKF_VMP)

    def set_virtual_meas_pt(self, offset=[0, 0, 0], activationMask=0, cutOffFreq=0):
        '''Convenience setter for virtual measpoint offset

        Sets the virtual measpoint offset #
        
        Args:
            offset: Distance between INS center of measurement and virtual measurement point [m, m, m].
            activationMask: Bit 0 -> INS/GNSS Position, Bit 1 -> INS/GNSS Velocity, Bit 2 -> Specific Force, Bit 3 -> Angular Rate
            cutOffFreq: The parameter CUTOFF-FREQ specifies the cut-off 1st frequency in [Hz] of the 1 order low pass. The low pass
                        is used to filter ω for the transformation. Due to the noise, the derivation of ω will not be transformed.
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not 'OK'.
        
        '''
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_VMP)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['leverArm'] = offset
        msgToSend.payload.data['mask'] = activationMask
        msgToSend.payload.data['cutoff'] = cutOffFreq
        self.send_msg_and_waitfor_okay(msgToSend)

        



        
    def eof_received(self):
        return True



def broadcast_search(timeout=0.1, port=BROADCAST_PORT, addr='<broadcast>'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    s.settimeout(timeout)

    s.sendto('hello'.encode('utf-8'), (addr, port))
    time.sleep(timeout)
    result_ips = list()
    result_names = list()
    while True:
        try:
            data, (ip, port) = s.recvfrom(1024)  # buffer size is 1024 bytes   
            name = data[:-1].decode('utf-8')
            result_ips.append(ip)
            result_names.append(name)
        except socket.timeout:
            s.close()
            break
    result = {'ip': result_ips, 'name': result_names}
    return result
    
