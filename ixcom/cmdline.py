import ixcom
import time
import sys
import struct
import argparse
import socket


class TextFileParser(ixcom.parser.MessageParser):
    def __init__(self, outputfile, skip_parameter=None, print_request = True):
        super().__init__()
        self.outputfile = outputfile
        self.print_request = print_request
        self.messageSearcher.disableCRC = False
        self._indent_level = 0
        self.add_subscriber(self)
        self.skipParameter = skip_parameter
        self.parameterList = list()

    def __handle_loglist2(self, message):
        self.write_output(f"Channel: {message.payload.data['reserved_paramheader']}\n")
        for log in message.payload.data['loglist']:
            msgid = log['msgid']
            if msgid in ixcom.data.MessagePayloadDictionary:
                message_class = ixcom.data.MessagePayloadDictionary[msgid]
                zeile = "msgid: %s\n" % (message_class.get_name())
            else:
                zeile = f'msgid: {msgid}\n'
            self.write_divider()
            self.write_output(zeile)
            self.write_output(f'divider: {log["divider"]}\n')
            self.write_output(f'running: {log["running"]}\n')
        self.write_output('\n\n')
    
    def handle_message(self, message, from_device):
        zeile = "Header Time: %.4f\n" % (message.header.get_time())
        if self.skipParameter is None:
            self.write_output(zeile)
        elif message.data['parameterID'] in self.skipParameter:
            return
        if message.header.msgID == ixcom.data.MessageID.PARAMETER:
            self.parameterList.append((message.data['parameterID'], message))
            return
            if message.payload.data["action"] == 0:
                zeile = "Parameter: %s\n" % message.payload.get_name()
            else:
                zeile = "Parameter request: %s\n" % message.payload.get_name()
                if not self.print_request:
                    self.write_output(zeile+'\n')
                    return
        elif message.header.msgID == ixcom.data.MessageID.COMMAND:
            zeile = "Command: %s\n" % message.payload.get_name()
        self.write_output(zeile)
        if isinstance(message.payload, ixcom.data.PARXCOM_LOGLIST2_Payload):
            self.__handle_loglist2(message)
        else:                 
            self.__convert_dict(message.payload.data)
            zeile = "\n\n"
            self.write_output(zeile)

    def write_parameter(self):
        self.parameterList.sort(key=lambda messagetuple: messagetuple[0])
        for par in self.parameterList:
            message = par[1]
            if message.payload.data["action"] == 0:
                zeile = "Parameter: %s\n" % message.payload.get_name()
            else:
                zeile = "Parameter request: %s\n" % message.payload.get_name()
            self.write_output(zeile)
            if isinstance(message.payload, ixcom.data.PARXCOM_LOGLIST2_Payload):
                self.__handle_loglist2(message)
            else:
                self.__convert_dict(message.payload.data)
                zeile = "\n\n"
                self.write_output(zeile)

    def write_divider(self):
        self.write_output('-'*10+'\n')


    def __convert_dict(self, d):
        for key in d:
            if isinstance(d[key], list) and isinstance(d[key][0], dict):
                self.write_output(f'{key}:\n')
                self._indent_level += 1
                for new_d in d[key]:
                    self.write_divider()
                    self.__convert_dict(new_d)
                self._indent_level -= 1
            else:
                self.__convert_key(key, d)

    def __convert_key(self, key, d):
        if key in ['ip', 'subnetmask', 'gateway', 'defaultAddress', 'serverAddress', 'ipAddress', 'destAddr', 'udpAddr']:
            ipbinary = d[key]
            zeile = "%s: %s\n" % (key, socket.inet_ntoa(struct.pack('!L', ipbinary)))
        elif isinstance(d[key], bytes):
            try:
                tmp = d[key].split(b'\0')[0]
                tmp = tmp.decode('ascii')
                zeile = "%s: %s\n" % (key, tmp)
            except:
                zeile = "%s: %s\n" % (key, d[key])
        else:
            zeile = "%s: %s\n" % (key, d[key])
        self.write_output(zeile)

    def write_output(self, line):
        self.outputfile.write('\t'*self._indent_level+line)
        
    def parse_file(self, inputfile):
        while True:
            tmpBuffer = inputfile.read(1024)
            if not tmpBuffer: 
                break
            self.messageSearcher.process_bytes(tmpBuffer)

def xcom_lookup(argv = None):
    parser = argparse.ArgumentParser(description='Searches for XCOM servers on the network')
    parser.add_argument('-p', type=int, nargs='?', help='Port', default = 4000)
    args = parser.parse_args()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    s.settimeout(0.2)

    s.sendto("hello".encode('utf-8'), ("<broadcast>", args.p))
    time.sleep(0.1)
    
    while True:
        try:
            data, (ip, _) = s.recvfrom(1024) # buffer size is 1024 bytes
            try:
                client = ixcom.Client(ip, 3000)
                client.open_last_free_channel()
                sysname = client.get_parameter(19).payload.data['str'].decode('utf-8').split('\0')[0]
                imutype = client.get_parameter(107).payload.data["type"]
                fwversion = client.get_parameter(5).payload.data['str'].decode('utf-8').split('\0')[0]
                if imutype is not 255:
                    print("%s (%s, FW %s): ssh://root@%s, ftp://%s" % (data[:-1].decode('utf-8'), sysname, fwversion, ip, ip))
                client.close_channel()
            except:
                pass
        except (socket.timeout, OSError):
            try:
                s.close()
            except:
                pass
            sys.exit(0)


def configdump2txt(argv=None):
    parser = argparse.ArgumentParser(description='Converts xcom binary config dump files to other representations')
    parser.add_argument('input_file', metavar='', type=argparse.FileType('rb'), nargs='?', help='Name of the binary file', default='config.dump')
    parser.add_argument('-o', '--output', metavar='output_filename', type=argparse.FileType('wt'), help='Filename of the output file', default=sys.stdout)
    args = parser.parse_args(args=argv)
    xcomparser = TextFileParser(args.output, skip_parameter=[917])  # skip parxcom_loglist2(917)
    xcomparser.parse_file(args.input_file)
    xcomparser.write_parameter()


def monitor2xcom(argv = None):
    import re
    import binascii
    parser = argparse.ArgumentParser(description='Converts xcom binary config dump files to other representations')
    parser.add_argument('input_file', metavar='', type=argparse.FileType('rt'), nargs='?',
                       help='Name of the monitor file', default = 'monitor.log')
    parser.add_argument('-o', '--output', metavar='output_filename', type=argparse.FileType('wt'),
                       help='Filename of the output file', default = sys.stdout)
    args = parser.parse_args(args = argv)
    xcomparser = TextFileParser(args.output, print_request=False)

    for line in args.input_file:
        if re.search("Dump Frame", line):
            args.output.write("System Time: %s\n" % (line.split(":"))[0])
            frame = (line.split("--> "))[1]
            frame = frame.replace("\n", "")
            args.output.write("Frame: %s\n" % frame)
            frame = frame.replace(" ", "")
            frame = frame.replace("0x", "").lower()
            frame_bin = binascii.unhexlify(frame)
            try:
                xcomparser.messageSearcher.process_bytes(frame_bin)
            except ixcom.data.ParseError as e:
                frame_name = str(e).split('convert ')[1]
                args.output.write(f'Corrupt {frame_name} frame\n\n')
                

def split_config(argv = None):
    parser = argparse.ArgumentParser(description='Filters out certain parameters from config.dump file')
    parser.add_argument('inputfile', metavar='inputfile', type=argparse.FileType('rb'), nargs='?',
                       help='Name of the binary file', default = 'config.dump')
    parser.add_argument('-o', '--output', metavar='output_filename', type=argparse.FileType(mode='wb'),
                       help='Filename of the output file', default = sys.stdout.buffer)  
    parser.add_argument('parameter_ids', metavar = 'ID', type=int, nargs = '+', help = 'Parameter IDs to pass through')
    args = parser.parse_args()
    xcomparser = ixcom.parser.MessageSearcher()
    
       
    try:
        def callback(msg_bytes):
            message = ixcom.data.ProtocolMessage()
            message.payload = ixcom.data.DefaultParameterPayload()
            message.payload.from_bytes(msg_bytes[16:20])
            parameterID = message.payload.data['parameterID']
            if parameterID in args.parameter_ids:
                args.output.write(msg_bytes)
            
        xcomparser.add_callback(callback)
        xcomparser.process_bytes(args.inputfile.read())
        sys.exit(0)
    except Exception as ex:
        print(ex)
        sys.exit(1)
