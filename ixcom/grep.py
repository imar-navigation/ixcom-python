import struct
import os
import io

import numpy as np
from numpy.lib.recfunctions import append_fields

from .parser import XcomMessageParser, XcomMessageSearcher
from . import data

def get_item_len(item):
    if isinstance(item, (list, tuple)):
        item_len = len(item)
    else:
        item_len = 1
    return item_len

def grep_file(filename='iXCOMstream.bin'):
    message_files_dict = dict()
    message_searcher = XcomMessageSearcher(disable_crc = True)

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
    parser = XcomMessageParser()
    parser.nothrow = True
    parser.add_callback(parameter_callback)
    with open(filename, 'rb') as f:
        parser.messageSearcher.process_bytes(f.read())
    return config

def read_file(filename='iXCOMstream.bin'):
    message_bytes_dict = dict()
    result = dict()
    message_searcher = XcomMessageSearcher(disable_crc = True)

    def message_callback(in_bytes):
        message_id = int(in_bytes[1])
        try:
            message_bytes_dict[message_id].write(in_bytes)
        except:
            message_bytes_dict[message_id] = io.BytesIO(in_bytes)

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
            result[msg.payload.get_name()] = parse_message_from_buffer(msg_id, message_bytes_dict[msg_id])
        elif msg_id == data.MessageID.PARAMETER:
            parser = XcomMessageParser()
            parser.nothrow = True
            parser.add_callback(parameter_callback)
            parser.messageSearcher.process_bytes(message_bytes_dict[msg_id].read())
            result['config'] = config

    return result

def parse_message_from_file(messageID, filename = None):
    msg = data.getMessageWithID(messageID)
    if filename is None:
        fname = hex(messageID).upper()+'.bin'
    else:
        fname = filename
    if messageID is not 0x19:
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
    if messageID != data.SYSSTAT_Payload.message_id:
        msg = data.getMessageWithID(messageID)   
        dtype = np.dtype(msg.get_numpy_dtype())
        ret = np.frombuffer(buffer.getbuffer(), dtype)
        ret = append_fields(ret, 'gpstime', ret['time_of_week_sec'] + 1e-6*ret['time_of_week_usec'], usemask=False)
        return ret
    else:
        return None
