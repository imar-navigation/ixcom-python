import asynchat, socket
import asyncore
import threading
import collections
import crc16
import math
from enum import IntEnum
from xcom import xcomdata

PositionTuple = collections.namedtuple('PositionTuple','Lon Lat Alt')

class XcomMessageSearcherState(IntEnum):
    waiting_for_sync = 0
    waiting_for_msglength = 1
    fetching_bytes = 2

class XcomMessageSearcher:
    def __init__(self, parserDelegate):
        self.parserDelegate = parserDelegate
        self.searcherState  = XcomMessageSearcherState.waiting_for_sync
        self.currentBytes = bytearray(b' '*512)
        self.currentByteIdx = 0
        self.remainingByteCount = 0
        self.disableCRC = False
        self.processing = threading.Lock()
        
    def process_bytes(self, inBytes):
        self.processing.acquire()
        inByteIdx = 0
        while inByteIdx < len(inBytes):
            
            if self.searcherState == XcomMessageSearcherState.waiting_for_sync:
                poppedByte = inBytes[inByteIdx]
                inByteIdx += 1
                if poppedByte == 0x7E:
                    self.currentBytes[0] = 0x7E
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
                    self.remainingByteCount = self.currentBytes[self.currentByteIdx-1]*256 + self.currentBytes[self.currentByteIdx-2]-6
                    if self.remainingByteCount < 600:
                        self.searcherState = XcomMessageSearcherState.fetching_bytes
                    else:
                        self.searcherState = XcomMessageSearcherState.waiting_for_sync
            elif self.searcherState == XcomMessageSearcherState.fetching_bytes:
                if len(inBytes)-1 >=self.remainingByteCount+inByteIdx-1: # Der Buffer ist Länger als der Rest der Nachricht.
                    self.currentBytes[self.currentByteIdx:self.currentByteIdx+self.remainingByteCount] = inBytes[inByteIdx:inByteIdx+self.remainingByteCount]
                    self.currentByteIdx = self.currentByteIdx+self.remainingByteCount
                    inByteIdx = inByteIdx+self.remainingByteCount
                    self.remainingByteCount = 0
                else:
                    self.currentBytes[self.currentByteIdx:self.currentByteIdx+(len(inBytes)-inByteIdx)] = inBytes[inByteIdx:]
                    self.currentByteIdx = self.currentByteIdx+(len(inBytes)-inByteIdx)
                    self.remainingByteCount -= (len(inBytes)-inByteIdx)
                    inByteIdx = len(inBytes)
                if self.remainingByteCount == 0:
                    if self.disableCRC:
                        self.parserDelegate.parse(self.currentBytes[:self.currentByteIdx])
                    else:
                        crc = crc16.crc16xmodem(bytes(self.currentBytes[:self.currentByteIdx-2]))
                        if crc == self.currentBytes[self.currentByteIdx-2]+self.currentBytes[self.currentByteIdx-1]*256:
                            if hasattr(self.parserDelegate, 'parse'):
                                self.parserDelegate.parse(self.currentBytes[:self.currentByteIdx])
                        else:
                            print("CRC Error %d" % crc)
                    self.searcherState = XcomMessageSearcherState.waiting_for_sync
        self.processing.release()
        
class XcomMessageParser:
    def __init__(self):
        self.subscribers = set()
        self.messageSearcher = XcomMessageSearcher(self)
        self.responseEvent = threading.Event()
        self.responseEvent.responseID = None
        self.parameterEvent = threading.Event()
        self.parameterEvent.parameter = None
        self.messageEvent = threading.Event()
        self.messageEvent.message = None
        self.messageEvent.messageID = None
        
    def parse_response(self, inBytes):
        message = xcomdata.XcomProtocolMessage()
        message.header.from_bytes(inBytes[:16])
        message.payload = xcomdata.XcomResponsePayload(message.header.msgLength)
        message.from_bytes(inBytes)
        self.responseEvent.responseID = message.payload.data['responseID']
        self.responseEvent.set()
        print(message.payload.data['responseText'].decode('utf-8'))
                
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
            print("Unknown parameter ID %s" % parameterID)
        self.parameterEvent.parameter = message
        self.parameterEvent.set()
        
    def parse(self, inBytes):
        header = xcomdata.XcomProtocolHeader()
        header.from_bytes(inBytes)
        if header.msgID == xcomdata.MessageID.RESPONSE:
            self.parse_response(inBytes)
        elif header.msgID == xcomdata.MessageID.PARAMETER:
            self.parse_parameter(inBytes)
        else:
            message = xcomdata.getMessageWithID(header.msgID)
            if message is not None:
                message.from_bytes(inBytes)
                self.publish(message)
            if header.msgID == self.messageEvent.messageID:
                self.messageEvent.message = message
                self.messageEvent.set()
                
    def add_subscriber(self, subscriber):
        self.subscribers.add(subscriber)
        
    def remove_subscriber(self, subscriber):
        self.subscribers.discard(subscriber)
            
    def publish(self, message):
        for subscriber in self.subscribers:
            subscriber.handle_message(message, from_device = self)

class XcomClient(asynchat.async_chat, XcomMessageParser):
    """XCOM TCP Client

    Implements a TCP-socket based XCOM client and offers convenience methods to interact with the 
    device. Other classes may subscribe to decoded messages.
    """
    
    def __init__(self, host, port=3000):
        asynchat.async_chat.__init__(self)
        XcomMessageParser.__init__(self)
        

        self.set_terminator(None)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        hostAndPort = (host, port)
        self.connect(hostAndPort)
        self.sending = threading.Lock()
        self.waiting = threading.Lock()
        threading.Thread(target=asyncore.loop).start()
    
    def __del__(self):
        self.close()
        
    def __hash__(self):
        """Hash function

        Implements hash to use a Client as a key in a dictionary

        Args:
            self
        Returns:
            A hash
        """
        return id(self)
        
    def __eq__(self, other):
        return self is other
        
    def initiate_send(self):
            # because of bug in asynchat
            self.sending.acquire()
            asynchat.async_chat.initiate_send(self)
            self.sending.release()
        
    def open_channel(self, channelNumber = 0):
        """Opens an XCOM logical channel

        Opens an XCOM logical channel on the associated socket and waits for an "OK" response.

        Args:
            chnannelNumber: XCOM channel to open. Default = 0

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode']  = xcomdata.XcomCommandParameter.channel_open
        msgToSend.payload.data['channelNumber'] = channelNumber
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
        
    def close_channel(self, channelNumber = 0):
        """Closes an XCOM logical channel

        Closes an XCOM logical channel on the associated socket and waits for an "OK" response.

        Args:
            chnannelNumber: XCOM channel to close. Default = 0

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode']  = xcomdata.XcomCommandParameter.channel_close
        msgToSend.payload.data['channelNumber'] = channelNumber
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def reboot(self):
        """Reboots the system

        Sends an XCOM reboot command on the associated socket and waits for an "OK" response.

        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.XCOM)
        msgToSend.payload.data['mode']  = xcomdata.XcomCommandParameter.reboot
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def get_parameter(self, parameterID):
        """Gets parameter from Server with specified ID

        Gets the specified parameter. Blocks until parameter is retrieved.

        Args:
            parameterID: ID of the parameter to retrieve
        
        Returns:
            An XcomMessage object containing the parameter
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getParameterWithID(parameterID)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.REQUESTING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        self.wait_for_parameter()
        return self.parameterEvent.parameter
        
    def set_aligncomplete(self):
        """Completes the alignment

        Completes system alignment by sending the EKF ALIGN_COMPLETE command. Blocks until system
        repsonse is received.

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.ALIGN_COMPLETE
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def realign(self):
        """Initiates a new alignment

        Initiates a new system alignment by sending the EKF ALIGN command. Blocks until system 
        repsonse is received.

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.ALIGN
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
    
    def save_pos(self):
        """Saves the current position

        Saves the current system position in ROM. Uses the EKF SAVE_POS command

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.SAVEPOS
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def save_hdg(self):
        """Saves the current heading

        Saves the current heading position in ROM. Uses the EKF SAVE_HDG command

 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.SAVE_HDG
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def forced_zupt(self, enable):
        """Enables or disables forced Zero Velocity updates

        Enables or disables forced Zero Velocity updates using the EKF FORCED_ZUPT command.
        
        Args:
            enable: boolean value to enable or disable ZUPTs.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.FORCED_ZUPT
        msgToSend.payload.structString += "f"
        msgToSend.payload.data['enable'] = enable
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def save_antoffset(self, antenna):
        """Saves the currently estimated GNSS antenna offset

        Saves the currently estimated GNSS antenna offset using the EKF SAVE_ANTOFFSET command.
        
        Args:
            antenna: Antenna # to save the offset for.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.EKF)
        msgToSend.payload.data['subcommand'] = xcomdata.EkfCommand.SAVE_ANTOFFSET
        msgToSend.structString += "f"
        msgToSend.data['antenna'] = antenna
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def save_config(self):
        """Saves the current configuration

        Saves the current configuration to ROM using the CONF SAVE_CONFIG command.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.CONF)
        msgToSend.payload.data['configAction'] = 0
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def load_config(self):
        """Loads the configuration from ROM

        Loads the configuration from ROM using the CONF LOAD_CONFIG command.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.CONF)
        msgToSend.payload.data['configAction'] = 1
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def factory_reset(self):
        """Performs a factory reset

        Performs a factory reset using the CONF FACTORY_RESET command.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK"
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.CONF)
        msgToSend.payload.data['configAction'] = 2
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def add_log_with_rate(self, msgID, rate):
        """Add a log with specified rate

        Adds a log with a specific message ID with a specified rate. The divider is computed by
        taking into account the MAINTIMING and PRESCALER system parameters.
        
        Args:
            msgID: Mesage ID which should be requested.
            rate: Requested log rate in Hz
            
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK" or if rate too high.
        
        """
        maintiming = self.get_parameter(xcomdata.ParameterID.PARSYS_MAINTIMING)
        prescaler  = self.get_parameter(xcomdata.ParameterID.PARSYS_PRESCALER)
        divider = (maintiming.payload.data['maintiming']/rate/prescaler.payload.data['prescaler'])
        if divider < 1:
            raise ValueError("Selected rate too high")
        else:
            self.add_log_sync(msgID, math.ceil(divider))
        
    def add_log_sync(self, msgID, divider):
        """Add a log with specified divider

        Adds a log with a specific message ID with a divider.
        
        Args:
            msgID: Mesage ID which should be requested.
            divider: divider to use
            
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK".
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.ADD
        msgToSend.payload.data['divider'] = divider
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def clear_all(self):
        """Clears all logs

        Sends a CLEAR_ALL command to the system.
 
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK".
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = 3
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.SYNC
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.CLEAR_ALL
        msgToSend.payload.data['divider'] = 1
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def poll_log(self, msgID):
        """Polls a log

        Polls a log with a specified message ID. Blocks until the log is retrieved and returns 
        the log.

        Args:
            msgID: Message ID to poll
        
        Returns:
            The polled log
        
        Raises:
            TimeoutError: Timeout while waiting for response or log from the XCOM server
            ValueError: The response from the system was not "OK".
        
        """
        msgToSend = xcomdata.getCommandWithID(xcomdata.CommandID.LOG)
        msgToSend.payload.data['messageID'] = msgID
        msgToSend.payload.data['trigger'] = xcomdata.LogTrigger.POLLED
        msgToSend.payload.data['parameter'] = xcomdata.LogCommand.ADD
        msgToSend.payload.data['divider'] = 1
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        self.wait_for_log(msgID)
        return self.messageEvent.message
        
        
    def wait_for_parameter(self):
        """Waits for reception of parameter

        Blocks until a parameterEvent is received.
        
        Raises:
            TimeoutError: Timeout while waiting for parameter from the XCOM server
        
        """
        self.waiting.acquire()
        if not self.parameterEvent.wait(10):
            self.waiting.release()
            self.parameterEvent.clear()
            raise TimeoutError("Timed out while waiting for parameter")
        else:
            self.waiting.release()
            self.parameterEvent.clear()
            
    def wait_for_log(self, msgID):
        """Waits for reception of log

        Blocks until a messageEvent is received.
        
        Args:
            msgID: message ID of log to wait for.
        
        Raises:
            TimeoutError: Timeout while waiting for message from the XCOM server
        
        """
        self.waiting.acquire()
        self.messageEvent.messageID = msgID
        if not self.messageEvent.wait(10):
            self.waiting.release()
            self.messageEvent.clear()
            raise TimeoutError("Timed out while waiting for message")
        else:
            self.waiting.release()
            self.messageEvent.clear()
            
    def enable_recorder(self, channel, enable_autostart):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_CONFIG)
        msgToSend.payload.data['channelNumber'] = channel
        msgToSend.payload.data['autostart'] = enable_autostart
        msgToSend.payload.data['enable'] = 1
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def disable_recorder(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_CONFIG)
        msgToSend.payload.data['enable'] = 0
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def start_recorder(self, path):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_START)
        msgToSend.payload.data['str'] = path.ljust(128, '\0')
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def stop_recorder(self, path):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARREC_STOP)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_schulermode(self, enable_schuler):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_SCHULERMODE)
        msgToSend.payload.data['enable'] = enable_schuler
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_broadcast(self, port = 4000, hidden = 0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_BROADCAST)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['port'] = port
        msgToSend.payload.data['hidden_mode'] = hidden  
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_zupt_parameters(self, thr_acc = 1, thr_omg = 1, thr_vel = 0, cut_off = 1, interval = 3, final_std_dev = 0.002, start_std_dev = 0.01, time_constant = 1, delay_samples = 300, activation_mask = 0x0, auto_zupt = 1):
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
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_startup(self, initPos = PositionTuple(Lon = 0.1249596927, Lat = 0.8599914412, Alt = 311.9), initPosStdDev = [10, 10, 10], posMode = xcomdata.StartupPositionMode.GNSSPOS, initHdg = 0, initHdgStdDev = 1, hdgMode = xcomdata.StartupHeadingMode.DEFAULT, realign = 0, inMotion = 0, leverArm = [0, 0, 0], leverArmStdDev = [1, 1, 1], autorestart = 0, gnssTimeout = 600): 
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
        msgToSend.payload.data['reserved2'] = 0
        msgToSend.payload.data['realign'] = realign
        msgToSend.payload.data['inMotion'] = inMotion
        msgToSend.payload.data['autoRestart'] = autorestart
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_aligntime(self, levelling_time, zupt_time):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_ALIGNTIME)
        msgToSend.payload.data['aligntime'] = zupt_time
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_COARSETIME)
        msgToSend.payload.data['coarsetime'] = levelling_time
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_alignmode(self, mode):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_ALIGNMODE)
        msgToSend.payload.data['alignmode'] = mode
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_threshholds(self, pos_medium = 1, pos_high = 0.1, heading_good = 0.001*math.pi/180.0):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PAREKF_HDGPOSTHR)
        msgToSend.payload.data['hdgGoodThr'] = heading_good
        msgToSend.payload.data['posMedThr'] = pos_medium
        msgToSend.payload.data['posHighThr'] = pos_high
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def set_crosscoupling(self, CCAcc, CCOmg):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARIMU_CROSSCOUPLING)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['CCAcc'] = CCAcc
        msgToSend.payload.data['CCOmg'] = CCOmg
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def get_crosscoupling(self):
        param = self.get_parameter(xcomdata.ParameterID.PARIMU_CROSSCOUPLING)
        returnDict = dict()
        returnDict['CCAcc'] = param.payload.data['CCAcc']
        returnDict['CCOmg'] = param.payload.data['CCOmg']
        return returnDict
        
    def enable_postproc(self, channel):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_POSTPROC)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['channel'] = channel
        msgToSend.payload.data['enable'] = 1
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        self.save_config()
        
    def disable_postproc(self):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARXCOM_POSTPROC)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['enable'] = 0
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        self.save_config()
        
    def set_elevationmask(self, mask_angle):
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARGNSS_ELEVATIONMASK)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['elevationMaskAngle'] = mask_angle
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        
    def send_and_wait_for_okay(self, inBytes):
        """Waits for reception of OK response

        Send the bytes and waits for an OK response from the system
        
        Args:
            inBytes: bytes to send
        
        Raises:
            TimeoutError: Timeout while waiting for response from the XCOM server
            ValueError: The response from the system was not "OK".
        
        """
        self.waiting.acquire()
        self.push(inBytes)
        if not self.responseEvent.wait(10):
            self.waiting.release()
            self.responseEvent.clear()
            raise TimeoutError("Timed out while waiting for okay")
        else:
            self.waiting.release()
            self.responseEvent.clear()
            if self.responseEvent.responseID != xcomdata.XcomResponse.OK:
                raise ValueError("Expected response %d, got %d" % (xcomdata.XcomResponse.OK, self.responseEvent.responseID))
            
        
    def get_antoffset(self, antenna):
        """Convencie getter for antenna offset

        Gets the antenna offset for the specified antenna #
        
        Args:
            antenna: Antenna # to retrieve the antenna offset for.
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not "OK".
        
        """
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARGNSS_ANTOFFSET)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.REQUESTING
        msgToSend.payload.data['reserved'] = antenna
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
        self.wait_for_parameter()
        return self.parameterEvent.parameter
        
    def set_antoffset(self, antenna = 0, offset = [0,0,0], stdDev = [0.1, 0.1, 0.1]):
        """Convencie setter for antenna offset

        Sets the antenna offset for the specified antenna #
        
        Args:
            antenna: Antenna # to retrieve the antenna offset for.
            offset: antenna offset in m.
            stdDev: standard deviation of antenna offset in m.
        
        Raises:
            TimeoutError: Timeout while waiting for response or parameter from the XCOM server
            ValueError: The response from the system was not "OK".
        
        """
        msgToSend = xcomdata.getParameterWithID(xcomdata.ParameterID.PARGNSS_ANTOFFSET)
        msgToSend.payload.data['action'] = xcomdata.XcomParameterAction.CHANGING
        msgToSend.payload.data['reserved'] = antenna
        msgToSend.payload.data['antennaOffset'] = offset
        msgToSend.payload.data['stdDev'] = offset
        bytesToSend = msgToSend.to_bytes()
        self.send_and_wait_for_okay(bytesToSend)
    
        
    def collect_incoming_data(self, data):
        self.messageSearcher.process_bytes(data)
    
    def found_terminator(self):
        pass
        

        
          


