import ixcom
import time
import sys
import struct
import argparse
import socket

        
class TextFileParser(ixcom.parser.MessageParser):
    def __init__(self, outputfile, print_request = True):
        super().__init__()
        self.outputfile = outputfile
        self.print_request = print_request
        self.messageSearcher.disableCRC = True
        self.add_subscriber(self)
    
    def handle_message(self, message, from_device):
        zeile = "Header Time: %.4f\n" % (message.header.get_time())
        self.write_output(zeile)
        if message.header.msgID == ixcom.data.MessageID.PARAMETER:
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
        for key in message.payload.data:
            if key == 'str':
                try:
                    tmp = message.payload.data[key].decode('ascii')
                    tmp = tmp.split('\0')[0]
                    zeile = "%s: %s\n" % (key, tmp)
                except:
                    zeile = "%s: %s\n" % (key, message.payload.data[key])
            elif key == 'ip' or key == 'subnetmask' or key == 'gateway':
                ipbinary = message.payload.data[key]
                zeile = "%s: %s\n" % (key, socket.inet_ntoa(struct.pack('!L', ipbinary)))
            elif message.payload.get_name() == 'PARXCOM_LOGLIST2' and 'msgid' in key:
                value = message.payload.data[key]
                if value in ixcom.data.MessagePayloadDictionary:
                    message_class = ixcom.data.MessagePayloadDictionary[value]
                    zeile = "%s: %s\n" % (key, message_class.get_name()) 
            else:
                zeile = "%s: %s\n" % (key, message.payload.data[key])
            self.write_output(zeile)
        zeile = "\n\n"
        self.write_output(zeile)

    def write_output(self, line):
        self.outputfile.write(line)
        
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

def configdump2txt(argv = None):
    parser = argparse.ArgumentParser(description='Converts xcom binary config dump files to other representations')
    parser.add_argument('input_file', metavar='', type=argparse.FileType('rb'), nargs='?',
                       help='Name of the binary file', default = 'config.dump')
    parser.add_argument('-o', '--output', metavar='output_filename', type=argparse.FileType('wt'),
                       help='Filename of the output file', default = sys.stdout)     
    args = parser.parse_args(args = argv)
    xcomparser = TextFileParser(args.output)
    xcomparser.parse_file(args.input_file)

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