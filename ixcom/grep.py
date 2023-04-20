import struct
import os
import io

import numpy as np
from numpy.lib.recfunctions import append_fields

from .parser import MessageParser, MessageSearcher
from . import data
from .exceptions import EndOfConfig

def get_item_len(item):
    if isinstance(item, (list, tuple)):
        item_len = len(item)
    else:
        item_len = 1
    return item_len

def grep_file(filename='iXCOMstream.bin'):
    message_files_dict = dict()
    message_searcher = MessageSearcher(disable_crc = True)

    def message_callback(in_bytes):
        message_id = int(in_bytes[1])
        if message_id not in message_files_dict:
            message_files_dict[message_id] = open('{}.bin'.format(hex(message_id)), 'wb')
        message_files_dict[message_id].write(in_bytes)

    message_searcher.add_callback(message_callback)
    with open(filename, 'rb') as f:
        message_searcher.process_buffer_unsafe(f.read())

    for fd in message_files_dict.values():
        fd.close()

def read_config(filename='config.dump'):
    config = {}
    def parameter_callback(msg, from_device):
        if msg.header.msgID == data.MessageID.PARAMETER:
            config[msg.payload.get_name()] = msg.data
    parser = MessageParser()
    parser.nothrow = True
    parser.add_callback(parameter_callback)
    with open(filename, 'rb') as f:
        parser.messageSearcher.process_bytes(f.read())
    return config

def read_file_for_config(filename='iXCOMstream.bin'):
    parameter_bytes = io.BytesIO(b'')
    message_searcher = MessageSearcher(disable_crc = True)


    def message_callback(in_bytes):
        if not in_bytes:
            return
        message_id = int(in_bytes[1])
        if message_id == data.MessageID.PARAMETER:
            parameter_bytes.write(in_bytes)
        else:
            raise EndOfConfig()

    config = {}
    def parameter_callback(msg, from_device):
        if msg.header.msgID == data.MessageID.PARAMETER:
            config[msg.payload.get_name()] = msg.data


    message_searcher.add_callback(message_callback)

    with open(filename, 'rb') as f:
        try:
            message_searcher.process_buffer_unsafe(f.read())
        except EndOfConfig:
            pass
    parameter_bytes.seek(0, os.SEEK_SET)
    parser = MessageParser()
    parser.nothrow = True
    parser.add_callback(parameter_callback)
    parser.messageSearcher.process_bytes(parameter_bytes.read())

    return config

def read_file(filename='iXCOMstream.bin'):
    message_bytes_dict = dict()
    result = dict()
    message_searcher = MessageSearcher(disable_crc = True)

    def message_callback(in_bytes):
        if not in_bytes:
            return
        message_id = int(in_bytes[1])
        if message_id == data.MessageID.PLUGIN:
            plugin_id = int(in_bytes[16]) + (int(in_bytes[17]) << 8)
            message_id = 0x100 + plugin_id
        if message_id not in message_bytes_dict:
            message_bytes_dict[message_id] =  io.BytesIO(b'')
        message_bytes_dict[message_id].write(in_bytes)

    config = {}
    def parameter_callback(msg, from_device):
        if msg.header.msgID == data.MessageID.PARAMETER:
            config[msg.payload.get_name()] = msg.data
        

    message_searcher.add_callback(message_callback)
    with open(filename, 'rb') as f:
        message_searcher.process_buffer_unsafe(f.read())

    for msg_id in message_bytes_dict:
        message_bytes_dict[msg_id].seek(0, os.SEEK_SET)
        if msg_id < 0xFD:
            msg = data.getMessageWithID(msg_id)
            try:
                if msg:
                    result[msg.payload.get_name()] = parse_message_from_buffer(msg_id, message_bytes_dict[msg_id])
                else:
                    data.handle_undefined_message(msg_id)
            except:
                print(f"Error: Message with ID: {msg_id} could not be parsed!")
        elif msg_id == data.MessageID.PARAMETER:
            parser = MessageParser()
            parser.nothrow = True
            parser.add_callback(parameter_callback)
            parser.messageSearcher.process_bytes(message_bytes_dict[msg_id].read())
            result['config'] = config
        elif msg_id > 0xFF:
                plugin_message_id = msg_id - 0x100
                msg = data.getPluginMessageWithID(plugin_message_id)
                try:
                    if msg:
                        result[msg.payload.get_name()] = parse_message_from_buffer(msg_id, message_bytes_dict[msg_id])
                    else:
                        data.handle_undefined_plugin_message(plugin_message_id)
                except:
                    print(f"Error: Plugin Message with ID: {plugin_message_id} could not be parsed!")
    return result

def parse_message_from_file(messageID, filename = None):
    msg = data.getMessageWithID(messageID)
    if filename is None:
        fname = hex(messageID).upper()+'.bin'
    else:
        fname = filename
    if messageID != 0x19:
        msg_size = msg.size()
    else:
        with open(fname, mode='rb') as f:
            msg_size = struct.unpack('=BBBBH', f.read(6))[4]
    
    with open(fname, mode='rb') as f:
        msg.from_bytes(f.read(msg_size))

    file_size = os.path.getsize(fname)
    
    num_messages = round(file_size/msg_size)
    result_dict = dict()
    result_dict['gpstime'] = np.zeros((num_messages,1))
    result_dict['globalstat'] = np.zeros((num_messages,1),dtype=np.uint16)
    for key in msg.payload.data:
        vector_length = get_item_len(msg.payload.data[key])
        result_dict[key] = np.zeros((num_messages, vector_length))
    idx = 0
    with open(fname, mode='rb') as f:
        for chunk in iter(lambda: f.read(msg_size), b''):
            msg.from_bytes(chunk)
            result_dict['gpstime'][idx] = msg.header.get_time()
            for key in msg.payload.data:
                result_dict[key][idx,:] = np.array(msg.payload.data[key])
            result_dict['globalstat'][idx] = msg.bottom.gStatus
            idx += 1
    return result_dict

def parse_message_from_buffer(messageID, buffer):
 
    def add_time(ret):
        return append_fields(ret, 'gpstime', ret['time_of_week_sec'] + 1e-6 * ret['time_of_week_usec'], usemask=False)
    if messageID > 0xFF:
        plugin_message_id = messageID - 0x100
        msg = data.getPluginMessageWithID(plugin_message_id)
    else:
        msg = data.getMessageWithID(messageID)   
    if not msg or get_item_len(msg) == 0:
        print(f'ignored Message with ID: {messageID}')
        return None
        
    if msg.payload.get_varsize_arg_from_bytes is None:
        dtype = np.dtype(msg.get_numpy_dtype())
        nlen = int(np.floor(len(buffer.getbuffer())/ dtype.itemsize))
        return add_time(np.frombuffer(buffer.getbuffer(), dtype, count=nlen))
    else:
        _next_header = 0
        _msg_length = 16
        ret = []
        while _next_header + _msg_length < len(buffer.getbuffer()):
            buffer.seek(_next_header)
            msg.header.from_bytes(buffer.read(16))
            _msg_length = msg.header.msgLength
            _varsize_arg = msg.payload.get_varsize_arg_from_bytes(buffer.read(_msg_length - 16 - 4))
            if messageID > 0xFF:
                msg = data.getPluginMessageWithID(plugin_message_id,_varsize_arg)
            else:
                msg = data.getMessageWithID(messageID,_varsize_arg) 
            dtype = np.dtype(msg.get_numpy_dtype())
            buffer.seek(_next_header)
            ret.append(add_time(np.frombuffer(buffer.read(_msg_length), dtype, count=1)))
            _next_header += _msg_length
        return  ret  # normal ndarray not possible because of variable dtypes -> return list

        def iterate(buffer):
            start = 0
            while True:
                try:
                    current = buffer.getbuffer()[start:]
                    msg.from_bytes(current)
                    dtype = msg.get_numpy_dtype()
                    start += msg.header.msgLength
                    return add_time(np.frombuffer(current, dtype, count=1))
                except:
                    return             
        return np.hstack(iterate(buffer))
