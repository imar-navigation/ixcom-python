import collections
import math
import queue
import select
import socket
import struct
import threading
import time
from enum import IntEnum
from typing import Sequence

from . import crc16, data, protocol
from .data import (BROADCAST_PORT, GENERAL_PORT, LAST_CHANNEL_NUMBER,
                   SYNC_BYTE, WAIT_TIME_FOR_RESPONSE)
from .exceptions import (ClientTimeoutError, CommunicationError, ParseError,
                         ResponseError)

PositionTuple = collections.namedtuple('PositionTuple', 'Lon Lat Alt')

class MessageSearcherState(IntEnum):
    waiting_for_sync = 0
    waiting_for_msglength = 1
    fetching_bytes = 2


class MessageSearcher:
    def __init__(self, parserDelegate = None, disable_crc = False):
        self.searcherState = MessageSearcherState.waiting_for_sync
        self.currentBytes = bytearray(512)
        self.currentByteIdx = 0
        self.remainingByteCount = 0
        self.msgLength = 0
        self.disableCRC = disable_crc
        self.callbacks = []
        if parserDelegate is not None:
            self.callbacks.append(parserDelegate.parse)

    def process_buffer_unsafe(self, buffer):
        current_msg_start_idx = 0
        inBytes = memoryview(buffer)
        inbytelen = len(inBytes)
        while current_msg_start_idx + 5 < inbytelen:
            current_msg_length = inBytes[current_msg_start_idx + 4] + 256*inBytes[current_msg_start_idx + 5]
            if current_msg_start_idx + current_msg_length > inbytelen: # Message nicht mehr komplett
                break
            self.publish(inBytes[current_msg_start_idx:current_msg_start_idx+current_msg_length])
            current_msg_start_idx += current_msg_length

    def process_bytes(self, inBytes):
        inByteIdx = 0
        while inByteIdx < len(inBytes):
            if self.searcherState == MessageSearcherState.waiting_for_sync:
                poppedByte = inBytes[inByteIdx]
                inByteIdx += 1
                if poppedByte == SYNC_BYTE:
                    self.currentBytes[0] = SYNC_BYTE
                    self.currentByteIdx = 1
                    self.remainingByteCount = 5
                    self.searcherState = MessageSearcherState.waiting_for_msglength
            elif self.searcherState == MessageSearcherState.waiting_for_msglength:
                poppedByte = inBytes[inByteIdx]
                inByteIdx += 1
                self.currentBytes[self.currentByteIdx] = poppedByte
                self.currentByteIdx += 1
                self.remainingByteCount -= 1
                if self.remainingByteCount == 0:
                    self.msgLength = self.currentBytes[self.currentByteIdx - 1] * 256 + self.currentBytes[self.currentByteIdx - 2]
                    self.remainingByteCount = self.msgLength - 6
                    # 4096 should be replaced if greater messages would be defined
                    if self.remainingByteCount < 4096 and self.remainingByteCount > 0:
                        self.searcherState = MessageSearcherState.fetching_bytes
                    else:
                        self.searcherState = MessageSearcherState.waiting_for_sync
            elif self.searcherState == MessageSearcherState.fetching_bytes:
                if len(inBytes) - 1 >= self.remainingByteCount + inByteIdx - 1:  # Der Buffer ist Länger als der Rest der Nachricht.
                    self.currentBytes[self.currentByteIdx:self.currentByteIdx + self.remainingByteCount] = inBytes[inByteIdx:inByteIdx + self.remainingByteCount]
                    self.currentByteIdx = self.currentByteIdx + self.remainingByteCount
                    inByteIdx = inByteIdx + self.remainingByteCount
                    self.remainingByteCount = 0
                else:
                    self.currentBytes[self.currentByteIdx:self.currentByteIdx + (len(inBytes) - inByteIdx)] = inBytes[inByteIdx:]
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
                    self.searcherState = MessageSearcherState.waiting_for_sync

    def publish(self, msg_bytes):
        for callback in self.callbacks:
            callback(msg_bytes)

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        self.callbacks.remove(callback)


class MessageParser:
    def __init__(self):
        self.subscribers = set()
        self.callbacks = list()
        self.messageSearcher = MessageSearcher(self)
        self.nothrow = False

    def parse_response(self, inBytes):
        message = data.ProtocolMessage()
        message.header.from_bytes(inBytes[:16])
        message.payload = data.ResponsePayload(message.header.msgLength)
        message.from_bytes(inBytes)
        self.publish(message)

    def parse_parameter(self, inBytes):
        parameterID = inBytes[16] + (inBytes[17] << 8)
        message = data.getParameterWithID(parameterID)
        if message is not None:
            try:
                message.from_bytes(inBytes)
                self.publish(message)
            except Exception:
                print('Error: Parameter with ID: {} ({}) could not be parsed!'.format(parameterID, message.payload.get_name()))
        else:
            print('Warning: Parameter with ID: {} not handled!'.format(parameterID))

    def parse_command(self, inBytes):
        cmdID = inBytes[16] + (inBytes[17] << 8)
        message = data.getCommandWithID(cmdID)
        if message is not None:
            message.from_bytes(inBytes)
            self.publish(message)
        else:
            pass

    def parse(self, inBytes):
        header = data.ProtocolHeader()
        header.from_bytes(inBytes)
        try:
            if header.msgID == data.MessageID.RESPONSE:
                self.parse_response(inBytes)
            elif header.msgID == data.MessageID.PARAMETER:
                self.parse_parameter(inBytes)
            elif header.msgID == data.MessageID.COMMAND:
                self.parse_command(inBytes)
            else:
                message = data.getMessageWithID(header.msgID)
                if message is not None:
                    message.from_bytes(inBytes)
                    self.publish(message)
        except ParseError as err:
            if self.nothrow:
                print(err)
            else:
                raise

    def add_subscriber(self, subscriber):
        self.subscribers.add(subscriber)

    def add_callback(self, callback):
        self.callbacks += [callback]

    def add_callback_and_block(self, callback):
        '''Add a callback function and joins the communication thread.
        Call stop() in a callback function the stop the communication thread and continue.
        '''
        self.callbacks += [callback]
        self.join_comm_thread.join()

    def remove_callback(self, callback):
        self.callbacks.remove(callback)

    def remove_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)

    def publish(self, message):
        for subscriber in self.subscribers:
            subscriber.handle_message(message, from_device=self)
        for callback in self.callbacks:
            callback(message, from_device=self)

class MessageCallback:
    def __init__(self, callback, msg, client):
        self.callback = callback
        self.msg = msg
        self.client = client

    def run(self):
        self.callback(self.msg, self.client)

class Client(MessageParser):
    '''XCOM TCP Client

    Implements a TCP-socket based XCOM client and offers convenience methods to interact with the 
    device. Other classes may subscribe to decoded messages.
    '''

    def __init__(self, host, port=GENERAL_PORT, timeout = WAIT_TIME_FOR_RESPONSE):
        MessageParser.__init__(self)
        self.timeout = timeout
        self.host = host
        self.port = port
        self._create_socket_and_connect()
        self._stop_event = threading.Event()
        self._response_event = threading.Event()
        self._response_event.response = None
        self._parameter_event = threading.Event()
        self._parameter_event.parameter = None
        self._message_event = threading.Event()
        self._message_event.msg = None
        self._message_event.id = None
        self.okay_lock = threading.Lock()
        self._comm_thread = threading.Thread(target = self._update_data, daemon = True, name='CommThread')
        self._comm_thread.start()
        self._callback_queue = queue.Queue()
        self._callback_thread = threading.Thread(target = self._callback_worker, daemon = True, name='CallbackThread')
        
        self._callback_thread.start()
        
        self.add_subscriber(self)

    def _create_socket_and_connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.connect((self.host, self.port))

    def join_comm_thread(self):
        '''Join the communication thread
        Blocks the calling location until the communications thread terminates.
        Can e.g. be used if callbacks have been set up, logs have been requested and we just want to
        leave the program running like this until the communications with the device stop.
        Args:
            self
        '''
        self._comm_thread.join()

    def stop(self):
        self._stop_event.set()
        self._comm_thread.join()
        self._callback_thread.join()

    def publish(self, message):
        for subscriber in self.subscribers:
            subscriber.handle_message(message, from_device=self)
        for callback in self.callbacks:
            cb = MessageCallback(callback, message, self)
            self._callback_queue.put(cb)

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

    def _callback_worker(self):
        while not self._stop_event.is_set():
            try:
                callback = self._callback_queue.get(block=True, timeout=1)
                callback.run()
            except queue.Empty:
                pass
        
    def handle_message(self, message, from_device):
       if message.header.msgID == data.MessageID.RESPONSE:
           self._response_event.response = message
           self._response_event.set()
       elif message.header.msgID == data.MessageID.PARAMETER:           
           self._parameter_event.parameter = message
           self._parameter_event.set()
       elif message.header.msgID == self._message_event.id:
           self._message_event.msg = message
           self._message_event.set()
        

    def open_channel(self, channelNumber=0):
        '''Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Args:
            chnannelNumber: XCOM channel to open. Default = 0

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.XcomCommandPayload.command_id)
        msgToSend.payload.data['mode'] = data.XcomCommandParameter.channel_open
        msgToSend.payload.data['channelNumber'] = channelNumber
        self.send_msg_and_waitfor_okay(msgToSend)

    def _update_data(self):
        while not self._stop_event.is_set():
            inputready, _, _ = select.select([self.sock], [],[], 0.1)
            for _ in inputready:
                if self.sock.fileno() != -1:
                    try:
                        self.messageSearcher.process_bytes(self.sock.recv(1024))
                    except OSError:
                        pass

    def open_last_free_channel(self):
        '''Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
            RuntimeError: If no free channel is available on the system.
            
        Returns:
            channelNumber: number of the opened channel
        
        '''
        self._create_socket_and_connect()
        msgToSend = data.getCommandWithID(data.XcomCommandPayload.command_id)
        msgToSend.payload.data['mode'] = data.XcomCommandParameter.channel_open
        channelNumber = LAST_CHANNEL_NUMBER
        while channelNumber >= 0:
            msgToSend.payload.data['channelNumber'] = channelNumber
            try:
                self.send_msg_and_waitfor_okay(msgToSend)
                self.clear_all()
                return channelNumber
            except (ResponseError, ConnectionError):
                channelNumber -= 1
                self._create_socket_and_connect()
            finally:
                if channelNumber == 0:
                    raise RuntimeError('No free channel on the system!')

    def get_loglist(self, channel):
        msgToSend = data.getParameterWithID(data.PARXCOM_LOGLIST2_Payload.parameter_id)
        msgToSend.payload.data['reserved_paramheader'] = channel
        msgToSend.payload.data['action'] = data.ParameterAction.REQUESTING
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_parameter()



    def open_first_free_channel(self):
        '''Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an 'OK' response.

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
            RuntimeError: If no free channel is available on the system.
            
        Returns:
            channelNumber: number of the opened channel
        
        '''
        msgToSend = data.getCommandWithID(data.XcomCommandPayload.command_id)
        msgToSend.payload.data['mode'] = data.XcomCommandParameter.channel_open
        channelNumber = 0
        while channelNumber <= LAST_CHANNEL_NUMBER:
            msgToSend.payload.data['channelNumber'] = channelNumber
            try:
                self.send_msg_and_waitfor_okay(msgToSend)
                self.clear_all()
                return channelNumber
            except (ResponseError, ConnectionError):
                channelNumber += 1
                self._create_socket_and_connect()
            finally:
                if channelNumber > LAST_CHANNEL_NUMBER:
                    raise RuntimeError('No free channel on the system!')

    def close_channel(self):
        '''Closes XCOM logical channel

        Closes XCOM  channel on the associated socket and waits for an 'OK' response.

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.XcomCommandPayload.command_id)
        msgToSend.payload.data['mode'] = data.XcomCommandParameter.channel_close
        msgToSend.payload.data['channelNumber'] = 0
        self.send_msg_and_waitfor_okay(msgToSend)

    def reboot(self):
        '''Reboots the system

        Sends an XCOM reboot command on the associated socket and waits for an 'OK' response.

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.XcomCommandPayload.command_id)
        msgToSend.payload.data['mode'] = data.XcomCommandParameter.reboot
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_parameter(self, parameterID: int):
        '''Gets parameter from device with specified ID

        Gets the specified parameter. Blocks until parameter is retrieved.

        Args:
            parameterID: ID of the parameter to retrieve
        
        Returns:
            An XcomMessage object containing the parameter
        
        Raises:
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getParameterWithID(parameterID)
        msgToSend.payload.data['action'] = data.ParameterAction.REQUESTING
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_parameter()

    def set_aligncomplete(self):
        '''Completes the alignment

        Completes system alignment by sending the EKF ALIGN_COMPLETE command. Blocks until system
        repsonse is received.

 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_EKF_Payload.command_id)
        msgToSend.payload.data['subcommand'] = data.EkfCommand.ALIGN_COMPLETE
        self.send_msg_and_waitfor_okay(msgToSend)

    def realign(self):
        '''Initiates a new alignment

        Initiates a new system alignment by sending the EKF ALIGN command. Blocks until system 
        repsonse is received.

 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_EKF_Payload.command_id)
        msgToSend.payload.data['subcommand'] = data.EkfCommand.ALIGN
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_pos(self):
        '''Saves the current position

        Saves the current system position in ROM. Uses the EKF SAVE_POS command

 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_EKF_Payload.command_id)
        msgToSend.payload.data['subcommand'] = data.EkfCommand.SAVEPOS
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_hdg(self):
        '''Saves the current heading

        Saves the current heading value in ROM. Uses the EKF SAVE_HDG command

 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_EKF_Payload.command_id)
        msgToSend.payload.data['subcommand'] = data.EkfCommand.SAVEHDG
        self.send_msg_and_waitfor_okay(msgToSend)

    def forced_zupt(self, enable: bool):
        '''Enables or disables forced Zero Velocity updates

        Enables or disables forced Zero Velocity updates using the EKF FORCED_ZUPT command.
        
        Args:
            enable: boolean value to enable or disable ZUPTs.
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_EKF_Payload.command_id)
        msgToSend.payload.data['subcommand'] = data.EkfCommand.FORCED_ZUPT
        msgToSend.payload.structString += 'f'
        msgToSend.payload.data['enable'] = enable
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_antoffset(self, antenna: int):
        '''Saves the currently estimated GNSS antenna offset

        Saves the currently estimated GNSS antenna offset using the EKF SAVE_ANTOFFSET command.
        
        Args:
            antenna: Antenna # to save the offset for.
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_EKF_Payload.command_id)
        msgToSend.payload.data['subcommand'] = data.EkfCommand.SAVEANTOFFSET
        msgToSend.payload.structString += 'f'
        msgToSend.payload.data['antenna'] = antenna
        self.send_msg_and_waitfor_okay(msgToSend)

    def save_config(self):
        '''Saves the current configuration

        Saves the current configuration to ROM using the CONF SAVE_CONFIG command.
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_CONF_Payload.command_id)
        msgToSend.payload.data['configAction'] = 0
        self.send_msg_and_waitfor_okay(msgToSend)

    def load_config(self):
        '''Loads the configuration from ROM

        Loads the configuration from ROM using the CONF LOAD_CONFIG command.
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_CONF_Payload.command_id)
        msgToSend.payload.data['configAction'] = 1
        self.send_msg_and_waitfor_okay(msgToSend)

    def factory_reset(self):
        '''Performs a factory reset

        Performs a factory reset using the CONF FACTORY_RESET command.
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_CONF_Payload.command_id)
        msgToSend.payload.data['configAction'] = 4
        self.send_msg_and_waitfor_okay(msgToSend)

    def add_log_with_rate(self, msgID: int, rate: float):
        '''Add a log with specified rate

        Adds a log with a specific message ID with a specified rate. The divider is computed by
        taking into account the MAINTIMING and PRESCALER system parameters.
        
        Args:
            msgID: Mesage ID which should be requested.
            rate: Requested log rate in Hz
            
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK' or if rate too high.
        
        '''
        divider = self.get_divider_for_rate(rate)
        self.add_log_sync(msgID, math.ceil(divider))

    def get_divider_for_rate(self, rate: float):
        '''Determines the divider resulting in a certain log output rate for this system.

        Args:
            rate: output rate in Hz

        Returns:
            Divider which results in an output rate as close as possible to the requested rate.

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK' or if rate too high.
            ValueError: If the selected rate os higher than the inertial sensor sampling rate.

        '''
        maintiming = self.get_parameter(data.PARSYS_MAINTIMING_Payload.parameter_id)
        prescaler = self.get_parameter(data.PARSYS_PRESCALER_Payload.parameter_id)
        divider = (maintiming.payload.data['maintiming'] / rate / prescaler.payload.data['prescaler'])
        if divider < 1:
            raise ValueError('Selected rate too high')
        else:
            return divider

    def add_log_sync(self, msgID: int, divider: int):
        '''Add a log with specified divider

        Adds a log with a specific message ID with a divider.
        
        Args:
            msgID: Mesage ID which should be requested.
            divider: divider to use
            
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_LOG_Payload.command_id)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = data.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = data.LogCommand.ADD
        msgToSend.payload.data['divider'] = divider
        self.send_msg_and_waitfor_okay(msgToSend)
        
    def add_log_event(self, msgID: int):
        '''Add an event-triggered log

        Adds a log with a specific message ID to be sent at event. The triggering event depends on the specific log,
        e.g. for GNSSSOL, an event trigger will trigger the log with every new solution.
        
        Args:
            msgID: Mesage ID which should be requested.
            
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_LOG_Payload.command_id)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = data.LogTrigger.EVENT
        msgToSend.payload.data['parameter'] = data.LogCommand.ADD
        msgToSend.payload.data['divider'] = 500 # use 500 here, because a '1' is rejected from some logs
        self.send_msg_and_waitfor_okay(msgToSend)

    def clear_all(self):
        '''Clears all logs

        Sends a CLEAR_ALL command to the system.
 
        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_LOG_Payload.command_id)
        msgToSend.payload.data['messageID'] = 3
        msgToSend.payload.data['trigger'] = data.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = data.LogCommand.CLEAR_ALL
        msgToSend.payload.data['divider'] = 1
        self.send_msg_and_waitfor_okay(msgToSend)

    def clear_log(self, msgID: int):
        '''Clears a log with a specific message ID.

        Clears a log with a specific message ID.

        Args:
            msgID: Mesage ID which should be requested.

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'.

        '''
        msgToSend = data.getCommandWithID(data.CMD_LOG_Payload.command_id)
        msgToSend.payload.data['messageID'] = 3
        msgToSend.payload.data['trigger'] = data.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = data.LogCommand.CLEAR_ALL
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
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getCommandWithID(data.CMD_LOG_Payload.command_id)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = data.LogTrigger.POLLED
        msgToSend.payload.data['parameter'] = data.LogCommand.ADD
        msgToSend.payload.data['divider'] = 500  # use 500 here, because a '1' is rejected from some logs
        self._message_event.id = msgID
        self._message_event.clear()
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_polled_log()


    def wait_for_parameter(self):
        '''Waits for reception of parameter

        Blocks until a parameterEvent is received.
        
        Raises:
            ClientTimeoutError: Timeout while waiting for parameter from the XCOM server
        
        '''
        self._update_until_event(self._parameter_event, self.timeout)
        result = self._parameter_event.parameter
        return result

    def _update_until_event(self, event, timeout):
        event.wait(timeout=timeout)
        if event.is_set():
            event.clear()
            return
        raise ClientTimeoutError('Timeout while waiting for event', thrower=self)

        
    def wait_for_polled_log(self):
        '''Waits for reception of log

        Blocks until a messageEvent is received.
        
        Raises:
            ClientTimeoutError: Timeout while waiting for message from the XCOM server
        
        '''
        self._update_until_event(self._message_event, self.timeout)
        result = self._message_event.msg
        return result

    def wait_for_log(self, msgID: int):
        '''Waits for reception of log with specified message ID

        Args:
            msgID: message ID of the log to be retrieved

        Raises:
            ClientTimeoutError: Timeout while waiting for message from the XCOM server
        
        '''
        self._message_event.id = msgID
        self._message_event.clear()
        self._update_until_event(self._message_event, self.timeout)
        result = self._message_event.msg
        return result

    def enable_recorder(self, channel: int, enable_autostart: bool):
        '''Enable the system recorder on the specified channel

        Args:
            channel: XCOM channel to use for autostart
            enable_autostart: selects whether to start the recorder directly

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARREC_CONFIG_Payload.parameter_id)
        msgToSend.payload.data['channelNumber'] = channel
        msgToSend.payload.data['autostart'] = enable_autostart
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def disable_recorder(self):
        '''Disable the system recorder

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        currently_enabled = self.get_parameter(data.PARREC_CONFIG_Payload.parameter_id).data['autostart']
        if currently_enabled:
            msgToSend = data.getParameterWithID(data.PARREC_CONFIG_Payload.parameter_id)
            msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
            self.send_msg_and_waitfor_okay(msgToSend)

    def start_recorder(self, path: str):
        '''Start the system recorder

        Args:
            path: log directory to use

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARREC_START_Payload.parameter_id)
        msgToSend.payload.data['str'] = path.ljust(128, '\0').encode('ascii')
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def stop_recorder(self):
        '''Stop the system recorder

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARREC_STOP_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def disable_udp_broadcast(self):
        '''Stop the UDP broadcast

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''

        currently_enabled = self.get_parameter(data.PARXCOM_UDPCONFIG_Payload.parameter_id).data['enable']

        if currently_enabled:
            curr_ip = self.get_parameter(data.PARXCOM_UDPCONFIG_Payload.parameter_id).data['ip']
            curr_port = self.get_parameter(data.PARXCOM_UDPCONFIG_Payload.parameter_id).data['port']
            curr_ch = self.get_parameter(data.PARXCOM_UDPCONFIG_Payload.parameter_id).data['channel']

            msgToSend = data.getParameterWithID(data.PARXCOM_UDPCONFIG_Payload.parameter_id)
            msgToSend.payload.data['ip'] = curr_ip
            msgToSend.payload.data['port'] = curr_port
            msgToSend.payload.data['enable'] = 0
            msgToSend.payload.data['channel'] = curr_ch
            msgToSend.payload.data['enableABD'] = 0
            msgToSend.payload.data['reserved2'] = 0

            msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
            self.send_msg_and_waitfor_okay(msgToSend)

    def set_recorder_suffix(self, suffix: str):
        '''Sets the suffix of the system recorder

        The suffix will be the part between the GNSS time and before the idx, e.g. the log path will be
        2019_08_07_1230_suffix, or suffix_001

        Args:
            suffix: suffix to use

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARREC_SUFFIX_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['suffix'] = suffix.ljust(128, '\0')
        self.send_msg_and_waitfor_okay(msgToSend)

    def enable_full_sysstatus(self):
        '''Enables all available system status payloads

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARDAT_SYSSTAT_Payload.parameter_id)
        msgToSend.payload.data['statMode'] = 127
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_device_info(self):
        '''Get information about the connected device

        Returns:
            A dictionary containing information about the device, e.g. part number, serial number, etc.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        result = dict()
        result['prjnumber'] = self.get_parameter(0).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['partnumber'] = self.get_parameter(1).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['serialnumber'] = self.get_parameter(2).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['mfgdate'] = self.get_parameter(3).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['caldate'] = self.get_parameter(4).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['fwversion'] = self.get_parameter(5).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['navversion'] = self.get_parameter(6).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['ekfversion'] = self.get_parameter(7).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['navnum'] = self.get_parameter(9).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['navparset'] = self.get_parameter(10).payload.data['str'].split(b'\0')[0].decode('ascii')
        result['sysname'] = self.get_parameter(19).payload.data['str'].split(b'\0')[0].decode('utf-8')
        result['maintiming'] = self.get_parameter(data.PARSYS_MAINTIMING_Payload.parameter_id).payload.data['maintiming']
        try:
            result['gyro_range'] = self.get_parameter(data.PARIMU_RANGE_Payload.parameter_id).payload.data['range_gyro']
        except:
            pass
        result['ip'] = self.host
        return result

    def set_zupt_parameters(self, thr_acc: float = 1, thr_omg: float = 1, thr_vel: float = 0, cut_off: float = 1, interval: float = 3, final_std_dev: float = 0.002,
                            start_std_dev: float = 0.01, time_constant: float = 1, delay_samples: int = 300, activation_mask: int = 0x0, auto_zupt: bool = 1):
        '''Sets the parameters for the motion detection engine

        Args:
            thr_acc: Acceleration threshold in m/s^2.
            thr_omg: Angular rate threshold in rad/s.
            thr_vel: Threshold in m/s for the ZUPT inhibitor, i.e. ZUPTs will be inhibited if GNSS detects a velocity higher than this threshold
            cut_off: Cutoff frequency in Hz for the low-pass filter filtering the accelerations and angular rates for the ZUPT detector
            interval: ZUPT interval in seconds
            final_std_dev: Final ZUPT standard deviation in m/s. For details, please refer to the protocol documentation
            start_std_dev: Initial ZUPT standard deviation in m/s. For details, please refer to the protocol documentation
            time_constant: Time constant for the exponential ZUPT standard deviation falloff. For details, please refer to the protocol documentation
            delay_samples: Number of samples for which a all detection conditions have to be met before a stationary condition is proclaimed.
            activation_mask: Selects which sensors to use in ZUPT detecion. Bit 0: Accelerometer, Bit 1: Angular rate, Bit 2: Odometer.
            auto_zupt: Selects whether to do zero velocity updates in the navigation filter if a stationary condition has been detected.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PAREKF_ZUPT_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
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

    def set_autozupt(self, enable: bool):
        '''Enable or disable automatic ZUPT execution if a stationary condition has been detected.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        parekf_zupt = self.get_parameter(data.PAREKF_ZUPT_Payload.parameter_id)
        parekf_zupt.payload.data['autoZupt'] = enable
        parekf_zupt.payload.data['action']= data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(parekf_zupt)

    def get_startup(self):
        '''Convenience getter for startup parameters of the device.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'.

        '''
        msgToSend = data.getParameterWithID(data.PAREKF_STARTUPV2_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.REQUESTING
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_parameter()

    def get_interface(self, port=0):
        msgToSend = data.getParameterWithID(data.PARXCOM_INTERFACE_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.REQUESTING
        msgToSend.payload.data['port'] = port
        self.send_msg_and_waitfor_okay(msgToSend)
        return self.wait_for_parameter()

    def set_interface(self, port=0, portlevel=0, portmode=0, baudrate=115200, reservedList=[0,0,0,0,0,0,0,0]):
        msgToSend = data.getParameterWithID(data.PARXCOM_INTERFACE_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['port'] = port
        msgToSend.payload.data['portmode'] = portmode
        msgToSend.payload.data['portlevel'] = portlevel
        msgToSend.payload.data['baudrate'] = baudrate
        msgToSend.payload.data['reserved'] = reservedList
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_startup(self, initPos=PositionTuple(Lon=0.1249596927, Lat=0.8599914412, Alt=311.9),
                    initPosStdDev: Sequence[float] = [10, 10, 10], posMode: data.StartupPositionMode = data.StartupPositionMode.GNSSPOS, initHdg: float = 0,
                    initHdgStdDev: float = 1, hdgMode: data.StartupHeadingMode = data.StartupHeadingMode.DEFAULT, realign: bool = False, inMotion: bool = False,
                    leverArm: Sequence[float] = [0, 0, 0], leverArmStdDev: Sequence[float] = [1, 1, 1], autorestart: bool = False, gnssTimeout: int = 0):
        '''Sets the startup parameters of the device.

        Args:
            initPos: Initial position to use. Type: PositionTuple(Lon, Lat, Alt) in (rad, rad, m)
            initPosStdDev: Standard deviation of initial position in m.
            posMode (ixcom.protocol.StartupPositionMode): Source of initial position
            initHdg: Initial heading in rad
            initHdgStdDev: Initial heading standard deviation rad
            hdgMode (ixcom.protocol.StartupHeadingMode): Source of initial heading
            realign: Select whether a realignment shall be performed with the reception of the parameter
            inMotion: If set, an in-motion alignment will be performed, regardless of the method selected in PAREKF_ALIGNMENT
            leverArm: Lever arm for the starting position in m
            leverArmStdDev: Standard deviation of the lever arm
            autorestart: Select whether the alignment shall be automatically restarted upon detected motion (during levelling) or finished (during stationary alignment)
            gnssTimeout: Timeout in seconds after which the system will resort to fallback positions after a realignment if the posMode is set to GNSS but no valid GNSS signal can be obtained. For details, please refer to the protocol documentation


        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PAREKF_STARTUPV2_Payload.parameter_id)
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
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_alignment(self, mode: protocol.AlignmentMode = None, levelling_time: int = None, stationary_time: int = None, 
                      enable_gyro_avg: bool = None, enable_track_align: bool = None, track_align_thresh: float = None,
                      track_align_direction: Sequence[float] = None, zupt_std_dev: float = None):
        '''Change the configured alignment method

        Changes only parameters which are not None.

        Args:
            mode (protocol.AlignmentMode): Selected alignment mode
            levelling_time: Levelling duration in seconds.
            stationary_time: Stationary alignment duration in seconds. Automatic ZUPTs will be executed during this period.
            enable_gyro_avg: Selects whether an initial guess of the gyro bias shall be formed by averaging during levelling.
            enable_track_align: Selects whether the direction of the GNSS velocity vector shall be used for attitude initialization 
                                by matching it with the body vector given it in the track_align_direction argument.
            track_align_thresh: Velocity threshold in m/s which has to be exceeded to use the GNSS track for aiding.
            track_align_direction: Main motion direction in the INS enclosure coordinate frame.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = self.get_parameter(data.PAREKF_ALIGNMENT_Payload.parameter_id)
        if mode is not None:
            msgToSend.payload.data['method'] = mode
        if levelling_time is not None:
            msgToSend.payload.data['levellingDuration'] = levelling_time
        if stationary_time is not None:
            msgToSend.payload.data['stationaryDuration'] = stationary_time
        if enable_gyro_avg is not None:  
            msgToSend.payload.data['enableGyroAvg'] = enable_gyro_avg
        if enable_track_align is not None:
            msgToSend.payload.data['enableTrackAlign'] = enable_track_align
        if track_align_thresh is not None:
            msgToSend.payload.data['trackAlignThresh'] = track_align_thresh
        if track_align_direction is not None:
            msgToSend.payload.data['trackAlignDirection'] = track_align_direction
        if zupt_std_dev is not None:
            msgToSend.payload.data['alignZuptStdDev'] = zupt_std_dev
        
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_aligntime(self, levelling_time: int, zupt_time: int):
        '''Sets the alignment duration to the commanded values

        Args:
            levelling_time: Duration of levelling in seconds
            zupt_time: Duration of stationary alignment in seconds

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PAREKF_ALIGNTIME_Payload.parameter_id)
        msgToSend.payload.data['aligntime'] = zupt_time
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)
        msgToSend = data.getParameterWithID(data.PAREKF_COARSETIME_Payload.parameter_id)
        msgToSend.payload.data['coarsetime'] = levelling_time
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_alignmode(self, mode: protocol.AlignmentMode):
        '''Change the configured alignment mode


        Args:
            mode (protocol.AlignmentMode): Selected alignment mode

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PAREKF_ALIGNMODE_Payload.parameter_id)
        msgToSend.payload.data['alignmode'] = mode
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_thresholds(self, pos_medium: float = 1, pos_high: float = 0.1, heading_good: float = 0.001 * math.pi / 180.0):
        '''Sets the thresholds used for the position and heading accuracy status bits in the global status.

        Args:
            pos_medium: Threshold to fall below for POS_MEDIUM_ACCURACY in m
            pos_high: Threshold to fall below for POS_HIGH_ACCURACY in m
            heading_good: Threshold to fall below for HEADING_GOOD_ACCURACY in rad. Note: A stationary alignment will be ended if this value has been reached!
        
        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PAREKF_HDGPOSTHR_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['hdgGoodThr'] = heading_good
        msgToSend.payload.data['posMedThr'] = pos_medium
        msgToSend.payload.data['posHighThr'] = pos_high
        self.send_msg_and_waitfor_okay(msgToSend)

    def send_msg_and_waitfor_okay(self, msg):
        with self.okay_lock:
            bytesToSend = msg.to_bytes()
            self.send_and_wait_for_okay(bytesToSend)

    def send_msg_and_dont_waitfor_okay(self, msg):
        with self.okay_lock:
            bytesToSend = msg.to_bytes()
            self.send_and_dont_wait_for_okay(bytesToSend)

    def set_imu_misalign(self, x: float, y: float, z: float):
        '''Adjusts PARIMU_MISALIGN

        Args:
            x: rotation around the x axis in rad
            y: rotation around the y axis in rad
            z: rotation around the z axis in rad

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARIMU_MISALIGN_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['rpy'] = [x, y, z]
        self.send_msg_and_waitfor_okay(msgToSend)


    def enable_postproc(self, channel: int):
        '''Enables the logging of data used for analysis and postprocessing on the selected channel

        Args:
            channel: Channel to use for the system recorder

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getParameterWithID(data.PARXCOM_POSTPROC_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['channel'] = channel
        msgToSend.payload.data['enable'] = 1
        self.send_msg_and_waitfor_okay(msgToSend)
        # self.save_config()

    def disable_postproc(self, channel: int = -1):
        '''Disables the logging of data used for analysis and postprocessing for a specific channel

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        channel = -1
        if channel == -1:
            channel = self.get_parameter(data.PARXCOM_POSTPROC_Payload.parameter_id).data['channel']
        msgToSend = data.getParameterWithID(data.PARXCOM_POSTPROC_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['channel'] = channel
        msgToSend.payload.data['enable'] = 0
        self.send_msg_and_waitfor_okay(msgToSend)
        # self.save_config()

    def set_ntrip(self, stream, user, password, server, sendPos=0, enable=1, remotePort=2101, ggaSendPeriod=1):
        msgToSend = data.getParameterWithID(data.PARXCOM_NTRIP_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['stream'] = stream.ljust(128, '\0').encode('ascii')
        msgToSend.payload.data['user'] = user.ljust(128, '\0').encode('ascii')
        msgToSend.payload.data['password'] = password.ljust(128, '\0').encode('ascii')
        msgToSend.payload.data['server'] = server.ljust(128, '\0').encode('ascii')
        msgToSend.payload.data['send_pos_on_login'] = sendPos
        msgToSend.payload.data['enable'] = enable
        msgToSend.payload.data['remote_port'] = remotePort
        msgToSend.payload.data['gga_send_period'] = ggaSendPeriod
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_pos(self, lonLatAlt: Sequence[float], llhStdDev: Sequence[float], 
                leverarmXYZ: Sequence[float], leverarmStdDev: Sequence[float], 
                enableMSLaltitude = 0, 
                time: float = 0, timeMode: protocol.ExtAidingTimeMode = protocol.ExtAidingTimeMode.LATENCY):
        '''External position aiding

        Args:
            lonLatAlt: (Lon, Lat, Alt) in (rad, rad, m)
            llhStdDev: Standard deviation in the directions of (Lon, Lat, Alt) in (m, m, m)
            leverarmXYZ: Leverarm in m
            leverarmStdDev: Standard deviation of the leverarm in m
            enableMSLaltitude: Set 1 if Altitude is meansealevel
            time: Timestamp or latency, depending on the timeMode argument
            timeMode (protocol.ExtAidingTimeMode): Selects whether the timestamp is a GPS second of week or a latency.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getCommandWithID(data.CMD_EXTAID_Payload.command_id)
        msgToSend.payload.data['time'] = time
        msgToSend.payload.data['timeMode'] = timeMode
        msgToSend.payload.data['cmdParamID'] = 3
        msgToSend.payload.structString += '12dI'
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
        msgToSend.payload.data['enableMSL_Alt'] = enableMSLaltitude
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_vel(self, vNED: Sequence[float], vNEDStdDev: Sequence[float], time: float = 0, timeMode: protocol.ExtAidingTimeMode = protocol.ExtAidingTimeMode.LATENCY):
        '''External velocity aiding

        Args:
            vNED: NED velocity in m/s
            vNEDStdDev: Standard deviation of vNED in m/s
            time: Timestamp or latency, depending on the timeMode argument
            timeMode (protocol.ExtAidingTimeMode): Selects whether the timestamp is a GPS second of week or a latency.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getCommandWithID(data.CMD_EXTAID_Payload.command_id)
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
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_heading(self, heading: float, standard_dev: float, time: float = 0, timeMode: protocol.ExtAidingTimeMode = protocol.ExtAidingTimeMode.LATENCY):
        '''External heading aiding

        Args:
            heading: heading in rad
            standard_dev: Standard deviation of heading in rad
            time: Timestamp or latency, depending on the timeMode argument
            timeMode (protocol.ExtAidingTimeMode): Selects whether the timestamp is a GPS second of week or a latency.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getCommandWithID(data.CMD_EXTAID_Payload.command_id)
        msgToSend.payload.data['time'] = time
        msgToSend.payload.data['timeMode'] = timeMode
        msgToSend.payload.data['cmdParamID'] = 5
        msgToSend.payload.structString += 'dd'
        msgToSend.payload.data['heading'] = heading
        msgToSend.payload.data['headingStdDev'] = standard_dev
        self.send_msg_and_waitfor_okay(msgToSend)

    def aid_height(self, height: float, standard_dev: float, time: float =0, timeMode: protocol.ExtAidingTimeMode = protocol.ExtAidingTimeMode.LATENCY):
        '''External height aiding

        Args:
            heading: height in m
            standard_dev: Standard deviation of height in m
            time: Timestamp or latency, depending on the timeMode argument
            timeMode (protocol.ExtAidingTimeMode): Selects whether the timestamp is a GPS second of week or a latency.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or log from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        '''
        msgToSend = data.getCommandWithID(data.CMD_EXTAID_Payload.command_id)
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
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        try:
            self.sock.sendall(inBytes)
        except socket.error:
            raise CommunicationError('Failed sending bytes to device {}'.format(self.host), self)

        self._update_until_event(self._response_event, self.timeout)
        response = self._response_event.response
        if response.payload.data['responseID'] != data.Response.OK:
            raise ResponseError(self._response_event.response.data['responseText'].decode('ascii'), self)

    def send_and_dont_wait_for_okay(self, inBytes):
        '''Waits for reception of OK response

        Send the bytes and waits for an OK response from the system

        Args:
            inBytes: bytes to send

        Raises:
            ClientTimeoutError: Timeout while waiting for response from the XCOM server
            ResponseError: The response from the system was not 'OK'.

        '''
        try:
            self.sock.sendall(inBytes)
        except socket.error:
            raise CommunicationError('Failed sending bytes to device {}'.format(self.host), self)

    def get_antoffset(self, antenna):
        '''Convenience getter for antenna offset

        Gets the antenna offset for the specified antenna #
        
        Args:
            antenna: Antenna # to retrieve the antenna offset for.
        
        Raises:
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getParameterWithID(data.PARGNSS_ANTOFFSET_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.REQUESTING
        msgToSend.payload.data['reserved_paramheader'] = antenna
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
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getParameterWithID(data.PARGNSS_ANTOFFSET_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['reserved_paramheader'] = antenna
        msgToSend.payload.data['antennaOffset'] = offset
        msgToSend.payload.data['stdDev'] = stdDev
        self.send_msg_and_waitfor_okay(msgToSend)

    def set_odooffset(self, offset=[0, 0, 0]):
        '''Convenience setter for odometer offset

        Sets the odometer offset

        Args:
            offset: antenna offset in m.

        Raises:
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'.

        '''
        msgToSend = data.getParameterWithID(data.PARODO_LEVERARM_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['leverArm'] = offset
        self.send_msg_and_waitfor_okay(msgToSend)

    def get_virtual_meas_pt(self):
        '''Convenience getter for virtual measpoint offset

        Gets the virtual measpoint offset for the output values defined with the mask #
                
        Raises:
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        return self.get_parameter(data.PAREKF_VMP_Payload.parameter_id)

    def set_virtual_meas_pt(self, offset=[0, 0, 0], activationMask=0, cutOffFreq=0):
        '''Convenience setter for virtual measpoint offset

        Sets the virtual measpoint offset #
        
        Args:
            offset: Distance between INS center of measurement and virtual measurement point [m, m, m].
            activationMask: Bit 0 -> INS/GNSS Position, Bit 1 -> INS/GNSS Velocity, Bit 2 -> Specific Force, Bit 3 -> Angular Rate
            cutOffFreq: The parameter CUTOFF-FREQ specifies the cut-off 1st frequency in [Hz] of the 1 order low pass. The low pass
                        is used to filter ω for the transformation. Due to the noise, the derivation of ω will not be transformed.
        
        Raises:
            ClientTimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ResponseError: The response from the system was not 'OK'.
        
        '''
        msgToSend = data.getParameterWithID(data.PAREKF_VMP_Payload.parameter_id)
        msgToSend.payload.data['action'] = data.ParameterAction.CHANGING
        msgToSend.payload.data['leverArm'] = offset
        msgToSend.payload.data['mask'] = activationMask
        msgToSend.payload.data['cutoff'] = cutOffFreq
        self.send_msg_and_waitfor_okay(msgToSend)

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
