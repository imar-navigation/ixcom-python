import struct
import os
import io

import numpy as np

from .parser import MessageParser, MessageSearcher, NpMessageParser
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
            message_files_dict[message_id] = open('{}.bin'.format(hex(message_id)), 'wb',buffering=message_searcher.file_write_buffer_length)
        message_files_dict[message_id].write(in_bytes)

    message_searcher.add_callback(message_callback)
    with open(filename, 'rb') as f:
        message_searcher.process_file_handle_unsafe(f)

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
        parser.messageSearcher.process_file_handle_unsafe(f)
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
            message_searcher.process_file_handle_unsafe(f)
        except EndOfConfig:
            pass
        except SystemError:
            pass
    parameter_bytes.seek(0, os.SEEK_SET)
    parser = MessageParser()
    parser.nothrow = True
    parser.add_callback(parameter_callback)
    parser.messageSearcher.process_file_handle(parameter_bytes)

    return config

def read_file(filename='iXCOMstream.bin', only_msg_ids = [], only_msg_names = [], get_parameter_history = False, ignore_msg_ids = [], ignore_msg_names = [], stack_varsize_arrays = False, no_gpstime_on_varsize_arrays = False, no_week_handling = False):
    """"""
    message_bytes_dict = dict()
    message_count_dict = dict()
    result = dict()
    message_searcher = MessageSearcher(disable_crc = True)

    only_this_ids = []
    if only_msg_ids:
        only_this_ids = only_msg_ids
    if only_msg_names:
        for name in only_msg_names:
            only_this_ids.append(data.get_message_id_from_name(name))

    ignore_this_ids = []
    if ignore_msg_ids:
        ignore_this_ids = ignore_msg_ids
    if ignore_msg_names:
        for name in ignore_msg_names:
            ignore_this_ids.append(data.get_message_id_from_name(name))

    gps_time_zeros = np.array([0],dtype=np.float64).tobytes()
    d = {"first_week": None}

    def message_callback(in_bytes):
        if not in_bytes:
            return
        message_id = int(in_bytes[1])
        if ignore_this_ids:
            if message_id in ignore_this_ids:
                return
        if only_this_ids:
            if not (message_id in only_this_ids):
                return
        if d["first_week"] == None:
            week = int.from_bytes(in_bytes[6:8], byteorder='little')
            if week==1:
                d["first_week"] = 0
            elif week>1:
                d["first_week"] = week
        if message_id == data.MessageID.PLUGIN:
            plugin_id = int(in_bytes[16]) + (int(in_bytes[17]) << 8)
            message_id = 0x100 + plugin_id
        if message_id not in message_bytes_dict:
            message_bytes_dict[message_id] =  io.BytesIO(b'')
            message_count_dict[message_id] = 0
        message_bytes_dict[message_id].write(in_bytes)
        message_count_dict[message_id] += 1
        if message_id != data.MessageID.PARAMETER:
            message_bytes_dict[message_id].write(gps_time_zeros)

    config = {}
    def parameter_callback(msg, from_device):
        if msg.header.msgID == data.MessageID.PARAMETER:
            if get_parameter_history:
                param_name = msg.payload.get_name()
                if param_name not in config:
                    config[param_name] = list()
                config[param_name].append(msg.data)
            else:
                config[msg.payload.get_name()] = msg.data
        

    message_searcher.add_callback(message_callback)

    if hasattr(filename,"decode"): # is bytes-like object
        message_searcher.process_buffer_unsafe(filename)

    elif hasattr(filename,"read"): # is readable file handle
        message_searcher.process_file_handle_unsafe(filename)

    else: # is a path as string or Path object
        path_string = str(filename)
        with open(path_string, 'rb') as f:
            message_searcher.process_file_handle_unsafe(f)

    if no_week_handling:
        d["first_week"] = None

    for msg_id in message_bytes_dict:
        message_bytes_dict[msg_id].seek(0, os.SEEK_SET)
        if msg_id < 0xFD:
            msg = data.getMessageWithID(msg_id)
            try:
                if msg:
                    result[msg.payload.get_name()] = parse_message_from_buffer(msg_id, message_bytes_dict[msg_id],message_count_dict[msg_id], stack_varsize_arrays = stack_varsize_arrays, no_gpstime_on_varsize_arrays = no_gpstime_on_varsize_arrays,first_week = d["first_week"])
                else:
                    data.handle_undefined_message(msg_id)
            except EndOfConfig:
                print(f"Error: Message with ID: {msg_id} could not be parsed!")
        elif msg_id == data.MessageID.PARAMETER:
            parser = MessageParser()
            parser.nothrow = True
            parser.add_callback(parameter_callback)
            parser.messageSearcher.process_file_handle(message_bytes_dict[msg_id])
            result['config'] = config
        elif msg_id > 0xFF:
                plugin_message_id = msg_id - 0x100
                msg = data.getPluginMessageWithID(plugin_message_id)
                try:
                    if msg:
                        result[msg.payload.get_name()] = parse_message_from_buffer(msg_id, message_bytes_dict[msg_id],message_count_dict[msg_id], stack_varsize_arrays = stack_varsize_arrays, no_gpstime_on_varsize_arrays = no_gpstime_on_varsize_arrays,first_week = d["first_week"])
                    else:
                        data.handle_undefined_plugin_message(plugin_message_id)
                except:
                    print(f"Error: Plugin Message with ID: {plugin_message_id} could not be parsed!")
    if message_searcher.cfg_json:
        result['cfg_json'] = message_searcher.cfg_json
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

def parse_message_from_buffer(messageID, buffer, message_count, stack_varsize_arrays=False, no_gpstime_on_varsize_arrays=False, first_week = None):
 
    def add_time_no_week_handling(ret):
        ret['gpstime'] = ret['time_of_week_sec'] + 1e-6 * ret['time_of_week_usec']
        return ret
    
    def add_time_with_week_handling(ret):
        ret['gpstime'] = ret['time_of_week_sec'] + 1e-6 * ret['time_of_week_usec']
        mask = ret['week']>first_week
        ret['gpstime'][mask] += (ret['week'][mask]-first_week).astype(np.float64) * 604800.0
        return ret
    
    add_time = add_time_no_week_handling

    if first_week!=None:
        add_time = add_time_with_week_handling
    
    if messageID > 0xFF:
        plugin_message_id = messageID - 0x100
        msg = data.getPluginMessageWithID(plugin_message_id)
    else:
        msg = data.getMessageWithID(messageID)   
    if not msg or get_item_len(msg) == 0:
        print(f'ignored Message with ID: {messageID}')
        return None
    
    if msg.payload.get_name() in ["SYSSTAT"]:
        valid = True
        buffer_view = buffer.getbuffer()
        buffer_length = len(buffer_view)
        parser = NpMessageParser()
        _next_header = 0
        _msg_length = int.from_bytes(buffer_view[_next_header + 4:_next_header + 6], byteorder='little')
        if _next_header + _msg_length + 8 > buffer_length:
            valid = False
        msg = parser.get_stashed_msg(buffer_view[_next_header:_next_header + _msg_length],extra_desc=[('gpstime', 'f8')])
        dtype = msg.extra_dtype
        nlen = int(np.floor(buffer_length/ dtype.itemsize))
        if nlen == message_count:
            return add_time(np.frombuffer(buffer_view, dtype, count=nlen))

    if msg.payload.get_varsize_arg_from_bytes is None:
        dtype = np.dtype(msg.get_numpy_dtype()+[('gpstime', 'f8')])
        nlen = int(np.floor(len(buffer.getbuffer())/ dtype.itemsize))
        return add_time(np.frombuffer(buffer.getbuffer(), dtype, count=nlen))
    
    else:
        ret = []
        if no_gpstime_on_varsize_arrays:
            parser = NpMessageParser()
            parser.nothrow = True
            parser.messageSearcher.disableCRC = True
            def combine_callback(msg, from_device):
                ret.append(np.array(msg.data))
            parser.add_callback(combine_callback)
            parser.messageSearcher.process_file_handle(buffer)
        else:
            _next_header = 0
            _msg_length = 16
            
            buffer_view = buffer.getbuffer()
            #buffer_view = buffer.read()
            buffer_length = len(buffer_view)
            parser = NpMessageParser()
            parser.nothrow = True
            parser.messageSearcher.disableCRC = True

            while _next_header + 20 <= buffer_length:
                _msg_length = int.from_bytes(buffer_view[_next_header + 4:_next_header + 6], byteorder='little')
                if _next_header + _msg_length + 8 > buffer_length:
                    break
                msg = parser.get_stashed_msg(buffer_view[_next_header:_next_header + _msg_length],extra_desc=[('gpstime', 'f8')])
                dtype = msg.extra_dtype
                npm = np.frombuffer(buffer_view, dtype, count=1,offset=_next_header)
                npm = add_time(npm)
                ret.append(npm)
                _next_header += _msg_length + 8

            
        if stack_varsize_arrays:
            return np.lib.recfunctions.stack_arrays(ret)
        return  ret  # normal ndarray not possible because of variable dtypes -> return list

